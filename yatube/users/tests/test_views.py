from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PagesTestsUser(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PagesTestsUser.user)

    def test_pages_uses_correct_template_user(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = [
            ('users/signup.html', reverse('users:signup')),
            ('users/login.html', reverse('users:login')),
            ('users/password_change_form.html',
             reverse('users:password_change')),
            ('users/password_change_done.html',
             reverse('users:password_change_done')),
            ('users/password_reset_form.html',
             reverse('users:password_reset')),
            ('users/password_reset_done.html',
             reverse('users:password_reset_done')),
            ('users/password_reset_confirm.html',
             reverse('users:password_reset_confirm',
                     kwargs={'uidb64': 'uidb64', 'token': 'token'})),
            ('users/password_reset_complete.html',
             reverse('users:password_reset_complete')),
            ('users/logged_out.html', reverse('users:logout')),
        ]
        for template, reverse_name in templates_page_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_form_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
