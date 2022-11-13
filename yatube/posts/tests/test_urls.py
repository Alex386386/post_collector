from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from django.core.cache import cache

User = get_user_model()


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

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTestsPosts.user)

    def tearDown(self):
        cache.clear()

    def test_urls_exists_at_desired_location_posts(self):
        """URL-адрес доступен."""
        url_names_code = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            f'/posts/{URLTestsPosts.post.id}/': HTTPStatus.OK,
        }
        for address, http_response in url_names_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_urls_authorized_exists_at_desired_location_posts(self):
        """URL-адрес доступен авторизованному пользователю."""
        url_names_code = {
            '/create/': HTTPStatus.OK,
            f'/posts/{URLTestsPosts.post.id}/edit/': HTTPStatus.OK,
        }
        for address, http_response in url_names_code.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_posts(self):
        """Страница перенаправляет анонимного пользователя."""
        url_names_code = {
            '/create/': HTTPStatus.FOUND,
            f'/posts/{URLTestsPosts.post.id}/edit/': HTTPStatus.FOUND,
        }
        for address, http_response in url_names_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_address_posts(self):
        """Страница перенаправляет анонимного пользователя."""
        url_names = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{URLTestsPosts.post.id}/edit/':
                f'/auth/login/?next=/posts/{URLTestsPosts.post.id}/edit/',
        }
        for address, redirect_address in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_urls_uses_correct_template_posts(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{URLTestsPosts.post.id}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template,
                                        f'не доступен данный адрес {address}')

    def test_urls_user_correct_template_authorized_posts(self):
        """
        URL-адрес использует соответствующий шаблон
        для авторизованного пользователя
        """
        templates_url_names = {
            '/create/': 'posts/create_post.html',
            f'/posts/{URLTestsPosts.post.id}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template,
                                        'не доступен данный адрес')

    def test_url_unexisting_page_posts(self):
        """"Проверка несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
