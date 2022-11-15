import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, Follow

User = get_user_model()


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
            content=PostPagesTestsPosts.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=PostPagesTestsPosts.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTestsPosts.user)

    def tearDown(self):
        cache.clear()

    def test_pages_uses_correct_template_posts(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = [
            ('posts/index.html', reverse('posts:index')),
            ('posts/group_list.html', reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'})),
            ('posts/profile.html', reverse(
                'posts:profile',
                args=[PostPagesTestsPosts.user])),
            ('posts/post_detail.html', reverse(
                'posts:post_detail',
                args=[PostPagesTestsPosts.post.id])),
            ('posts/create_post.html', reverse('posts:post_create')),
            ('posts/create_post.html', reverse(
                'posts:post_edit',
                args=[PostPagesTestsPosts.post.id])),
        ]
        for template, reverse_name in templates_page_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context_posts(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_object'][0]
        index_context = [
            (first_object.author, PostPagesTestsPosts.user),
            (first_object.text, 'Тестовый пост'),
            (first_object.group, PostPagesTestsPosts.group),
            (response.context['page_object'][0].image,
             PostPagesTestsPosts.post.image),
        ]
        for context, reverse_context in index_context:
            with self.subTest(context=context):
                self.assertEqual(context, reverse_context)

    def test_group_list_show_correct_context_posts(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}))
        group_context = [
            (response.context['page_object'][0].group,
             PostPagesTestsPosts.group),
            (response.context['page_object'][0].image,
             PostPagesTestsPosts.post.image),
        ]
        for context, reverse_context in group_context:
            with self.subTest(context=context):
                self.assertEqual(context, reverse_context)

    def test_profile_show_correct_context_posts(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:profile',
            args=[PostPagesTestsPosts.user]))
        profile_context = [
            (response.context['page_object'][0].author,
             PostPagesTestsPosts.user),
            (response.context['page_object'][0].image,
             PostPagesTestsPosts.post.image),
        ]
        for context, reverse_context in profile_context:
            with self.subTest(context=context):
                self.assertEqual(context, reverse_context)

    def test_post_detail_show_correct_context_posts(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            args=[PostPagesTestsPosts.post.id]))
        detail_context = [
            (response.context['post'].id, PostPagesTestsPosts.post.id),
            (response.context['post'].image,
             PostPagesTestsPosts.post.image),
        ]
        for context, reverse_context in detail_context:
            with self.subTest(context=context):
                self.assertEqual(context, reverse_context)

    def test_create_post_show_correct_context_posts(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
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
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            args=[PostPagesTestsPosts.post.id]))
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

        response_index = self.guest_client.get(reverse('posts:index'))
        post_index = response_index.context['page_object'][0].group
        self.assertEqual(post_index, PostPagesTestsPosts.post.group)

        response_group = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}))
        post_group = response_group.context['page_object'][0].group
        self.assertEqual(post_group, PostPagesTestsPosts.post.group)

        response_profile = self.authorized_client.get(reverse(
            'posts:profile',
            args=[PostPagesTestsPosts.user]))
        post_profile = response_profile.context['page_object'][0].group
        self.assertEqual(post_profile, PostPagesTestsPosts.post.group)

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
                    group=cls.group,)
                for id_text in range(14)
            ]
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTestsPosts.user)

    def test_paginator(self):
        """При создании поста, тот отображается в нужных шаблонах."""
        LIMIT_POST_COEFFICIENT1: int = 10
        LIMIT_POST_COEFFICIENT2: int = 4
        url_number_first_page = {
            reverse('posts:index'): LIMIT_POST_COEFFICIENT1,
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                LIMIT_POST_COEFFICIENT1,
            reverse('posts:profile', args=[PostPagesTestsPosts.user]):
                LIMIT_POST_COEFFICIENT1,
        }
        for value, number_of_post in url_number_first_page.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                self.assertEqual(len(response.context['page_object']),
                                 number_of_post)
        url_number_second_page = {
            reverse('posts:index') + '?page=2': LIMIT_POST_COEFFICIENT2,
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}) + '?page=2':
                        LIMIT_POST_COEFFICIENT2,
            reverse('posts:profile',
                    args=[PostPagesTestsPosts.user]) + '?page=2':
                        LIMIT_POST_COEFFICIENT2,
        }
        for value, number_of_post in url_number_second_page.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                self.assertEqual(len(response.context['page_object']),
                                 number_of_post)


class FollowTestsPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_two = User.objects.create_user(username='auth_two')
        cls.author = User.objects.create_user(username='author')
        cls.author_two = User.objects.create_user(username='author_two')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.post_two = Post.objects.create(
            author=cls.author_two,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_two = Client()
        self.authorized_client.force_login(FollowTestsPosts.user)
        self.authorized_client_two.force_login(FollowTestsPosts.user_two)

    def tearDown(self):
        cache.clear()

    def test_follow(self):
        """Тест создания и удаления подписки."""
        OBJECT_MAGNIFICATION_FACTOR: int = 1
        count_follow = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[FollowTestsPosts.author.username]))
        self.assertEqual(Follow.objects.count(),
                         count_follow + OBJECT_MAGNIFICATION_FACTOR)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            args=[FollowTestsPosts.author.username]))
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_follow_user(self):
        """
        Проверка того, что пользователь не может подписаться сам на себя.
        Проверка того, что пользователь может подписаться только один раз.
        """
        OBJECT_MAGNIFICATION_FACTOR: int = 1
        count_follow = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[FollowTestsPosts.user.username]))
        self.assertEqual(Follow.objects.count(), count_follow)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[FollowTestsPosts.author.username]))
        self.assertEqual(Follow.objects.count(),
                         count_follow + OBJECT_MAGNIFICATION_FACTOR)
        new_count_follow = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[FollowTestsPosts.author.username]))
        self.assertEqual(Follow.objects.count(), new_count_follow)

    def test_follow_index(self):
        """Тест проверки ленты подписок."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            args=[FollowTestsPosts.author.username]))
        self.authorized_client_two.get(reverse(
            'posts:profile_follow',
            args=[FollowTestsPosts.author_two.username]))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_object'][0].id,
                         FollowTestsPosts.post.id)
        response = self.authorized_client_two.get(reverse(
            'posts:follow_index'))
        self.assertNotEqual(response.context['page_object'][0].id,
                            FollowTestsPosts.post.id)
