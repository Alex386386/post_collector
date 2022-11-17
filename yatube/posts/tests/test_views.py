import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.constants_tests import (LIMIT_POST_COEFFICIENT1,
                                  LIMIT_POST_COEFFICIENT2,
                                  OBJECT_MAGNIFICATION_FACTOR)
from posts.models import Post, Group, Follow, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTestsPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
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
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.index = reverse('posts:index')
        cls.group_page = reverse('posts:group_list',
                                 kwargs={'slug': 'test-slug'})
        cls.profile = reverse('posts:profile', args=[cls.user])
        cls.detail = reverse('posts:post_detail', args=[cls.post.id])
        cls.create = reverse('posts:post_create')
        cls.edit = reverse('posts:post_edit', args=[cls.post.id])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_index_group_profile_show_correct_context_posts(self):
        """
        Шаблоны index, group_list, profile сформированы
        с правильным контекстом.
        """
        response = (
            self.guest_client.get(self.index),
            self.guest_client.get(self.group_page),
            self.guest_client.get(self.profile),
        )
        for response in response:
            with self.subTest(response=response):
                first_object = response.context['page_obj'][0]
                context = (
                    (first_object.author, self.user),
                    (first_object.text, self.post.text),
                    (first_object.group, self.group),
                    (first_object.image, self.post.image),
                )
                for context, reverse_context in context:
                    with self.subTest(context=context):
                        self.assertEqual(context, reverse_context)

    def test_post_detail_show_correct_context_posts(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(self.detail)
        detail_context = [
            (response.context['post'].id, self.post.id),
            (response.context['post'].image, self.post.image),
        ]
        for context, reverse_context in detail_context:
            with self.subTest(context=context):
                self.assertEqual(context, reverse_context)

    def test_create_post_show_correct_context_posts(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.create)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_edit_show_correct_context_posts(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.edit)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_one_post_on_the_page(self):
        """При создании поста, тот отображается в нужных шаблонах."""
        post_index = self.guest_client.get(
            self.index).context['page_obj'][0]
        post_group = self.guest_client.get(
            self.group_page).context['page_obj'][0]
        post_profile = self.authorized_client.get(
            self.profile).context['page_obj'][0]
        comment_attribute = (
            (post_index.group, self.post.group),
            (post_group.group, self.post.group),
            (post_profile.group, self.post.group),
        )
        for comment_context, attribute in comment_attribute:
            with self.subTest(comment_context=comment_context):
                self.assertEqual(comment_context, attribute)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        content_first = response.content
        Post.objects.create(
            text='test_new_post',
            author=PostPagesTestsPosts.user,
        )
        second_response = self.authorized_client.get(reverse('posts:index'))
        content_second = second_response.content
        self.assertEqual(content_first, content_second)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        content_third = third_response.content
        self.assertNotEqual(content_second, content_third)


class PostPaginatorTestsPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text=f'Тестовый пост{id_text}',
                    group=cls.group, )
                for id_text in range(14)
            ]
        )
        cls.index = reverse('posts:index')
        cls.group_page = reverse('posts:group_list',
                                 kwargs={'slug': 'test-slug'})
        cls.profile = reverse('posts:profile', args=[cls.user])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTestsPosts.user)

    def test_paginator(self):
        """При создании поста, тот отображается в нужных шаблонах."""
        url_number_first_page = (
            (self.index, LIMIT_POST_COEFFICIENT1),
            (self.group_page, LIMIT_POST_COEFFICIENT1),
            (self.profile, LIMIT_POST_COEFFICIENT1),
        )
        for value, number_of_post in url_number_first_page:
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                self.assertEqual(len(response.context['page_obj']),
                                 number_of_post)
        url_number_second_page = (
            (self.index + '?page=2', LIMIT_POST_COEFFICIENT2),
            (self.group_page + '?page=2', LIMIT_POST_COEFFICIENT2),
            (self.profile + '?page=2', LIMIT_POST_COEFFICIENT2),
        )
        for value, number_of_post in url_number_second_page:
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                self.assertEqual(len(response.context['page_obj']),
                                 number_of_post)


class FollowTestsPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username='first_auth')
        cls.second_user = User.objects.create_user(username='second_auth')
        cls.first_author = User.objects.create_user(username='first_author')
        cls.second_author = User.objects.create_user(username='second_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.first_post = Post.objects.create(
            author=cls.first_author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.second_post = Post.objects.create(
            author=cls.second_author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.first_author_profile_follow = reverse(
            'posts:profile_follow', args=[cls.first_author.username])
        cls.first_author_profile_unfollow = reverse(
            'posts:profile_unfollow', args=[cls.first_author.username])
        cls.first_user_profile_follow = reverse(
            'posts:profile_follow', args=[cls.first_user.username])
        cls.second_author_profile_follow = reverse(
            'posts:profile_follow', args=[cls.second_author.username])
        cls.follow_index = reverse('posts:follow_index')

    def setUp(self):
        self.guest_client = Client()
        self.first_authorized_client = Client()
        self.second_authorized_client = Client()
        self.first_authorized_client.force_login(self.first_user)
        self.second_authorized_client.force_login(self.second_user)

    def tearDown(self):
        cache.clear()

    def test_follow(self):
        """Тест создания и удаления подписки."""
        count_follow = Follow.objects.count()
        self.first_authorized_client.get(self.first_author_profile_follow)
        self.assertEqual(Follow.objects.count(),
                         count_follow + OBJECT_MAGNIFICATION_FACTOR)
        self.first_authorized_client.get(self.first_author_profile_unfollow)
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_follow_user_few_times(self):
        """
        Проверка того, что пользователь может подписаться только один раз.
        """
        count_follow = Follow.objects.count()
        # Создаём подписку
        self.first_authorized_client.get(self.first_author_profile_follow)
        # Проверяем, создалась ли подписка
        self.assertEqual(Follow.objects.count(),
                         count_follow + OBJECT_MAGNIFICATION_FACTOR)
        new_count_follow = Follow.objects.count()
        # Попытка создать ещё одну подписку с такими же параметрами
        self.first_authorized_client.get(self.first_author_profile_follow)
        # Проверка того что подписка не создалась
        self.assertEqual(Follow.objects.count(), new_count_follow)

    def test_follow_same_user(self):
        """
        Проверка того, что пользователь не может подписаться сам на себя.
        """
        count_follow = Follow.objects.count()
        self.first_authorized_client.get(self.first_user_profile_follow)
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_follow_index_correct(self):
        """Тест проверки корректного отображения ленты подписок."""
        # Создаём подписку
        self.first_authorized_client.get(self.first_author_profile_follow)
        response = self.first_authorized_client.get(self.follow_index)
        # Проверяем что в ленте подписок находиться ожидаемый пост
        self.assertEqual(response.context['page_obj'][0].id,
                         self.first_post.id)

    def test_follow_index_wrong(self):
        # Создаём подписку первого клиента
        self.first_authorized_client.get(self.first_author_profile_follow)
        # Создаём подписку второго клиента
        self.second_authorized_client.get(self.second_author_profile_follow)
        response = self.second_authorized_client.get(self.follow_index)
        # Проверяем что в ленте подписок второго клиента нет поста
        # находящегося в ленте первого клиента
        self.assertNotEqual(response.context['page_obj'][0].id,
                            self.first_post.id)
