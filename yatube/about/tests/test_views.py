from django.test import Client, TestCase
from django.urls import reverse


class PagesTestsAbout(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template_about(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = [
            ('about/author.html', reverse('about:author')),
            ('about/tech.html', reverse('about:tech')),
        ]
        for template, reverse_name in templates_page_names:
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
