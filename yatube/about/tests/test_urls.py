from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class URLTestsAbout(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_exists_at_desired_location_about(self):
        """URL-адрес доступен для всех пользователей."""
        url_names_code = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, http_response in url_names_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_response,
                                 'status code не соответствует ожидаемому')

    def test_urls_uses_correct_template_about(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template,
                                        'не доступен данный адрес')
