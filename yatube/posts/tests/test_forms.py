import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

OBJECT_MAGNIFICATION_FACTOR: int = 1


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_new_post(self):
        """Проверка создания нового поста. И сравнение с имеющимся постом."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': PostCreateFormTests.post.text,
            'group': PostCreateFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=[PostCreateFormTests.user]))
        self.assertEqual(Post.objects.count(),
                         post_count + OBJECT_MAGNIFICATION_FACTOR)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                group_id=PostCreateFormTests.group.id,
                image='posts/small.gif',
            ).exists()
        )
        last_post = Post.objects.last()
        first_post = Post.objects.first()
        attributes_post = {
            last_post.text: first_post.text,
            last_post.author: first_post.author,
            last_post.group: first_post.group,
        }
        for last_post, first_post in attributes_post.items():
            with self.subTest(last_post=last_post):
                self.assertEqual(last_post, first_post)

    def test_create_edit_post(self):
        """Проверка редактирования нового поста."""
        post_count = Post.objects.count()
        form_data = {
            'text': PostCreateFormTests.post.text,
            'group': '',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[PostCreateFormTests.post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=[PostCreateFormTests.post.id]))
        self.assertEqual(Post.objects.count(), post_count)
        post = get_object_or_404(Post, id=PostCreateFormTests.post.id)
        response = self.authorized_client.post(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        self.assertNotIn(post, response.context['page_object'])

    def test_create_comments_post(self):
        """Проверка создания комментария авторизованным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
            'post': PostCreateFormTests.post.id,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[PostCreateFormTests.post.id]),
            data=form_data,
            follow=True
        )
        # Проверяем что после создания комментария
        # пользователь был перенаправлен на страницу post_detail
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=[PostCreateFormTests.post.id]))
        # Проверяем что в БД создался новы комментарий
        self.assertEqual(Comment.objects.count(),
                         comment_count + OBJECT_MAGNIFICATION_FACTOR)
        # Проверяем что в контексте страницы
        # передан комментарий с тестовым текстом
        self.assertEqual(response.context['comments'][0].text,
                         'Тестовый текст комментария')

    def test_delete_comments_post(self):
        """Проверка создания комментария неавторизованным пользователем"""
        comment_count_before = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
            'post': PostCreateFormTests.post.id,
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=[PostCreateFormTests.post.id]),
            data=form_data,
            follow=True
        )
        comment_count_after = Comment.objects.count()
        # Проверяем что в БД не создалось новых комментариев
        self.assertEqual(comment_count_before, comment_count_after)
