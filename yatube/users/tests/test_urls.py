from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class URLTests_about(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location_users(self):
        """URL-адрес доступен для авторизованного пользователя."""
        url_names_code = {
            '/auth/signup/': HTTPStatus.OK,
            '/auth/login/': HTTPStatus.OK,
            '/auth/password_change/': HTTPStatus.OK,
            '/auth/password_change/done/': HTTPStatus.OK,
            '/auth/password_reset/': HTTPStatus.OK,
            '/auth/password_reset/done/': HTTPStatus.OK,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK,
            '/auth/reset/done/': HTTPStatus.OK,
            '/auth/logout/': HTTPStatus.OK,
        }
        for address, http_response in url_names_code.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_users(self):
        """Страница перенаправляет анонимного пользователя."""
        url_names_code = {
            '/auth/password_change/': HTTPStatus.FOUND,
            '/auth/password_change/done/': HTTPStatus.FOUND,
        }
        for address, http_response in url_names_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_address_users(self):
        """Страница перенаправляет анонимного пользователя."""
        url_names = {
            '/auth/password_change/':
                '/auth/login/?next=/auth/password_change/',
            '/auth/password_change/done/':
                '/auth/login/?next=/auth/password_change/done/',
        }
        for address, redirect_address in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_urls_uses_correct_template_users(self):
        """URL-адрес доступен для авторизованного пользователя."""
        templates_url_names = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/logout/': 'users/logged_out.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template,
                                        'не доступен данный адрес')
