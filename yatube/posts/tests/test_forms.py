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
        cls.first_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.second_group = Group.objects.create(
            title='Тестовая группа',
            slug='second_test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.first_group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий',
        )
        cls.index = ('posts:index', None)
        cls.group_page = ('posts:group_list', [cls.first_group.slug])
        cls.profile = ('posts:profile', [cls.user])
        cls.detail = ('posts:post_detail', [cls.post.id])
        cls.create = ('posts:post_create', None)
        cls.edit = ('posts:post_edit', [cls.post.id])
        cls.add_comment = ('posts:add_comment', [cls.post.id])

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
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.first_group.id,
            'image': uploaded,
        }
        template_address, argument = self.create
        response = self.authorized_client.post(
            reverse(template_address, args=argument),
            data=form_data,
            follow=True
        )
        template_address, argument = self.profile
        self.assertRedirects(response, reverse(template_address,
                                               args=argument))
        self.assertEqual(Post.objects.count(),
                         post_count + OBJECT_MAGNIFICATION_FACTOR)
        post = Post.objects.first()
        attributes_post = (
            (post.author, self.user),
            (post.text, self.post.text),
            (post.group, self.first_group),
            (post.image.read(), self.post.image.read()),
        )
        for attribut, expected in attributes_post:
            with self.subTest(attribut=attribut):
                self.assertEqual(attribut, expected,
                                 'Атрибут не соответствует ожидаемому')

    def test_create_edit_post(self):
        """Проверка редактирования нового поста."""

        post_count = Post.objects.count()

        form_data = {
            'text': 'Изменённый тестовый пост',
            'group': self.second_group.id,
        }

        template_address, argument = self.edit

        response = self.authorized_client.post(
            reverse(template_address, args=argument),
            data=form_data,
            follow=True
        )
        template_address, argument = self.detail

        self.assertRedirects(response, reverse(template_address,
                                               args=argument))
        self.assertEqual(Post.objects.count(), post_count)

        post = get_object_or_404(Post, id=self.post.id)

        template_address, argument = self.group_page

        response_context = self.authorized_client.post(
            reverse(template_address, args=argument)).context['page_obj']
        self.assertNotIn(post, response_context)

        attributes_post = (
            (post.author, self.user),
            (post.text, form_data['text']),
            (post.group.id, form_data['group']),
            (post.image.read(), self.small_gif),
        )
        for attribut, expected in attributes_post:
            with self.subTest(attribut=attribut):
                self.assertEqual(attribut, expected,
                                 'Атрибут не соответствует ожидаемому')

    def test_create_comments_post(self):
        """Проверка создания комментария авторизованным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
            'post': self.post.id,
        }
        template_address, argument = self.add_comment
        response = self.authorized_client.post(
            reverse(template_address, args=argument),
            data=form_data,
            follow=True
        )
        template_address, argument = self.detail
        # пользователь был перенаправлен на страницу post_detail
        self.assertRedirects(response, reverse(template_address,
                                               args=argument))
        # # Проверяем что в БД создался новый комментарий
        self.assertEqual(Comment.objects.count(),
                         comment_count + OBJECT_MAGNIFICATION_FACTOR)
        context = response.context['comments'][0]
        comment_attribute = (
            (context.text, form_data['text']),
            (context.post.id, form_data['post']),
            (context.author, self.user),
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
        template_address, argument = self.add_comment
        self.guest_client.post(
            reverse(template_address, args=argument),
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
