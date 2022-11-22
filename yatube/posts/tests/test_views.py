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
                                  OBJECT_MAGNIFICATION_FACTOR,
                                  LIMIT_POST_TEST,
                                  )
from posts.models import Post, Group, Follow, User
from posts.utils import create_post

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
        cls.index = ('posts:index', None)
        cls.group_page = ('posts:group_list', [cls.group.slug])
        cls.profile = ('posts:profile', [cls.user])
        cls.detail = ('posts:post_detail', [cls.post.id])
        cls.create = ('posts:post_create', None)
        cls.edit = ('posts:post_edit', [cls.post.id])

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
        responses = (
            self.index,
            self.group_page,
            self.profile,
        )
        for response in responses:
            with self.subTest(response=response):
                template_address, argument = response
                first_object = self.guest_client.get(reverse(template_address,
                                                             args=argument)
                                                     ).context['page_obj'][0]
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
        template_address, argument = self.detail
        response = self.guest_client.get(reverse(template_address,
                                                 args=argument)
                                         ).context['post']
        detail_context = [
            (response.id, self.post.id),
            (response.image, self.post.image),
        ]
        for context, reverse_context in detail_context:
            with self.subTest(context=context):
                self.assertEqual(context, reverse_context)

    def test_create_post_show_correct_context_posts(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        template_address, argument = self.create
        response = self.authorized_client.get(reverse(template_address,
                                                      args=argument))
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        )
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_edit_show_correct_context_posts(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        template_address, argument = self.edit
        response = self.authorized_client.get(reverse(template_address,
                                                      args=argument))
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
        address_list = [
            self.index,
            self.group_page,
            self.profile
        ]
        for address in address_list:
            with self.subTest(address=address):
                template_address, argument = address
                page_group = self.guest_client.get(
                    reverse(template_address, args=argument)
                ).context['page_obj'][0].group
                self.assertEqual(page_group, self.post.group)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        template_address, _ = self.index
        response = self.authorized_client.get(reverse(template_address))
        content_first = response.content
        Post.objects.create(
            text='test_new_post',
            author=PostPagesTestsPosts.user,
        )
        second_response = self.authorized_client.get(reverse(template_address))
        content_second = second_response.content
        self.assertEqual(content_first, content_second)
        cache.clear()
        third_response = self.authorized_client.get(reverse(template_address))
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
        cls.post = create_post(LIMIT_POST_TEST, cls.user, cls.group)
        cls.index = ('posts:index', None)
        cls.group_page = ('posts:group_list', [cls.group.slug])
        cls.profile = ('posts:profile', [cls.user])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTestsPosts.user)

    def test_paginator(self):
        """При создании поста, тот отображается в нужных шаблонах."""
        url_number_first_page = (
            self.index,
            self.group_page,
            self.profile,
        )
        for value in url_number_first_page:
            with self.subTest(value=value):
                template_address, argument = value
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument))
                self.assertEqual(len(response.context['page_obj']),
                                 LIMIT_POST_COEFFICIENT1)
        second_page = '?page=2'
        url_number_second_page = (
            self.index,
            self.group_page,
            self.profile,
        )
        for value in url_number_second_page:
            with self.subTest(value=value):
                template_address, argument = value
                response = self.guest_client.get(
                    f'{reverse(template_address, args=argument)}{second_page}')
                self.assertEqual(len(response.context['page_obj']),
                                 LIMIT_POST_COEFFICIENT2)


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
        cls.first_author_profile_follow = (
            'posts:profile_follow', [cls.first_author.username])
        cls.first_author_profile_unfollow = (
            'posts:profile_unfollow', [cls.first_author.username])
        cls.first_user_profile_follow = (
            'posts:profile_follow', [cls.first_user.username])
        cls.second_author_profile_follow = (
            'posts:profile_follow', [cls.second_author.username])
        cls.follow_index = ('posts:follow_index', None)

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
        template_address, argument = self.first_author_profile_follow
        self.first_authorized_client.get(
            reverse(template_address, args=argument))
        self.assertEqual(Follow.objects.count(),
                         count_follow + OBJECT_MAGNIFICATION_FACTOR)
        template_address, argument = self.first_author_profile_unfollow
        self.first_authorized_client.get(
            reverse(template_address, args=argument))
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_follow_user_few_times(self):
        """
        Проверка того, что пользователь может подписаться только один раз.
        """
        count_follow = Follow.objects.count()
        template_address, argument = self.first_author_profile_follow
        self.first_authorized_client.get(
            reverse(template_address, args=argument))
        # Проверяем, создалась ли подписка
        self.assertEqual(Follow.objects.count(),
                         count_follow + OBJECT_MAGNIFICATION_FACTOR)
        new_count_follow = Follow.objects.count()
        # Попытка создать ещё одну подписку с такими же параметрами
        self.first_authorized_client.get(
            reverse(template_address, args=argument))
        # Проверка того что подписка не создалась
        self.assertEqual(Follow.objects.count(), new_count_follow)

    def test_follow_same_user(self):
        """
        Проверка того, что пользователь не может подписаться сам на себя.
        """
        count_follow = Follow.objects.count()
        template_address, argument = self.first_user_profile_follow
        self.first_authorized_client.get(
            reverse(template_address, args=argument))
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_follow_index_correct(self):
        """Тест проверки корректного отображения ленты подписок."""
        template_address, argument = self.first_author_profile_follow
        self.first_authorized_client.get(
            reverse(template_address, args=argument))
        template_address, _ = self.follow_index
        response = self.first_authorized_client.get(reverse(template_address))
        # Проверяем что в ленте подписок находиться ожидаемый пост
        self.assertEqual(response.context['page_obj'][0].id,
                         self.first_post.id)

    def test_follow_index_wrong(self):
        """
        Тест корректного отображения ленты подписок,
        на странице ленты находятся ожидаемые посты
        """
        template_address, argument = self.first_author_profile_follow
        self.first_authorized_client.get(
            reverse(template_address, args=argument))
        template_address, argument = self.second_author_profile_follow
        self.second_authorized_client.get(
            reverse(template_address, args=argument))
        template_address, _ = self.follow_index
        response = self.second_authorized_client.get(reverse(template_address))
        # Проверяем что в ленте подписок второго клиента нет поста
        # находящегося в ленте первого клиента
        self.assertNotEqual(response.context['page_obj'][0].id,
                            self.first_post.id)
