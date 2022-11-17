import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.constants_tests import OBJECT_MAGNIFICATION_FACTOR
from posts.models import Post, Group, Comment, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


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
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий',
        )
        cls.index = reverse('posts:index')
        cls.group_page = reverse('posts:group_list',
                                 kwargs={'slug': 'test-slug'})
        cls.profile = reverse('posts:profile', args=[cls.user])
        cls.detail = reverse('posts:post_detail', args=[cls.post.id])
        cls.create = reverse('posts:post_create')
        cls.edit = reverse('posts:post_edit', args=[cls.post.id])
        cls.add_comment = reverse('posts:add_comment', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

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
            'text': self.post.text,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.create,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.profile)
        self.assertEqual(Post.objects.count(),
                         post_count + OBJECT_MAGNIFICATION_FACTOR)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                group_id=self.group.id,
                image='posts/small.gif',
            ).exists()
        )
        post = Post.objects.last()
        attributes_post = (
            (post.text, self.post.text),
            (post.group, self.group),
        )
        for attribut, expected in attributes_post:
            with self.subTest(attribut=attribut):
                self.assertEqual(attribut, expected,
                                 'Атрибут не соответствует ожидаемому')

    def test_create_edit_post(self):
        """Проверка редактирования нового поста."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': '',
        }
        response = self.authorized_client.post(
            self.edit,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.detail)
        self.assertEqual(Post.objects.count(), post_count)
        post = get_object_or_404(Post, id=self.post.id)
        response = self.authorized_client.post(self.group_page)
        self.assertNotIn(post, response.context['page_obj'])

    def test_create_comments_post(self):
        """Проверка создания комментария авторизованным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
            'post': self.post.id,
        }
        response = self.authorized_client.post(
            self.add_comment,
            data=form_data,
            follow=True
        )
        # Проверяем что после создания комментария
        # пользователь был перенаправлен на страницу post_detail
        self.assertRedirects(response, self.detail)
        # # Проверяем что в БД создался новый комментарий
        self.assertEqual(Comment.objects.count(),
                         comment_count + OBJECT_MAGNIFICATION_FACTOR)
        comment_attribute = (
            (response.context['comments'][0].text,
             'Тестовый текст комментария'),
            (response.context['comments'][0].post.id, self.post.id),
            (response.context['comments'][0].author, self.user),
        )
        for comment_context, attribute in comment_attribute:
            with self.subTest(comment_context=comment_context):
                self.assertEqual(comment_context, attribute)

    def test_delete_comments_post(self):
        """
        Проверка, что неавторизованный пользователь
        не может создать комментарий, и что имеющиеся комментарии
        не были изменены
        """
        comment_count_before = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
            'post': self.post.id,
        }
        self.guest_client.post(
            self.add_comment,
            data=form_data,
            follow=True
        )
        comment_count_after = Comment.objects.count()
        # Проверяем что в БД не создалось новых комментариев
        self.assertEqual(comment_count_before, comment_count_after)
        # Проверяем что имеющийся комментарий не был изменён
        last_comment = get_object_or_404(Comment, post=self.post)
        comment_attribute = (
            (last_comment.text, self.comment.text),
            (last_comment.author, self.user),
        )
        for comment_context, attribute in comment_attribute:
            with self.subTest(comment_context=comment_context):
                self.assertEqual(comment_context, attribute)
