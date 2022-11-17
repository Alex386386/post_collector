from http import HTTPStatus

from django.test import TestCase, Client
from posts.models import Post, Group, User
from django.core.cache import cache
from django.urls import reverse


class URLTestsPosts(TestCase):
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
        cls.index = reverse('posts:index')
        cls.group_page = reverse('posts:group_list',
                                 kwargs={'slug': 'test-slug'})
        cls.profile = reverse('posts:profile', args=[cls.user])
        cls.detail = reverse('posts:post_detail', args=[cls.post.id])
        cls.create = reverse('posts:post_create')
        cls.edit = reverse('posts:post_edit', args=[cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_urls_exists_at_desired_location_posts(self):
        """URL-адрес доступен."""
        url_names_code = (
            (self.index, HTTPStatus.OK),
            (self.group_page, HTTPStatus.OK),
            (self.profile, HTTPStatus.OK),
            (self.detail, HTTPStatus.OK),
        )
        for address, http_response in url_names_code:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_urls_authorized_exists_at_desired_location_posts(self):
        """URL-адрес доступен авторизованному пользователю."""
        url_names_code = (
            (self.create, HTTPStatus.OK),
            (self.detail, HTTPStatus.OK),
        )
        for address, http_response in url_names_code:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_posts(self):
        """Страница перенаправляет анонимного пользователя."""
        url_names_code = (
            (self.create, HTTPStatus.FOUND),
            (self.edit, HTTPStatus.FOUND),
        )
        for address, http_response in url_names_code:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_address_posts(self):
        """Страница перенаправляет анонимного пользователя."""
        url_names = (
            (self.create, '/auth/login/?next=/create/'),
            (self.edit,
             f'/auth/login/?next=/posts/{self.post.id}/edit/'),
        )
        for address, redirect_address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_urls_uses_correct_template_posts(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (self.index, 'posts/index.html'),
            (self.group_page, 'posts/group_list.html'),
            (self.profile, 'posts/profile.html'),
            (self.detail, 'posts/post_detail.html'),
        )
        for address, template in templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template,
                                        f'не доступен данный адрес {address}')

    def test_urls_user_correct_template_authorized_posts(self):
        """
        URL-адрес использует соответствующий шаблон
        для авторизованного пользователя
        """
        templates_url_names = (
            (self.create, 'posts/create_post.html'),
            (self.edit, 'posts/create_post.html'),
        )
        for address, template in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template,
                                        'не доступен данный адрес')

    def test_url_unexisting_page_posts(self):
        """"Проверка несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
