from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()

    def test_create_new_post(self):
        user_count = User.objects.count()
        form_data = {
            'first_name': 'Анатолий',
            'last_name': 'Крымкиннаш',
            'username': 'AN',
            'email': 'test@mail.ru',
            'password1': '12345678ndmM',
            'password2': '12345678ndmM',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), user_count + 1)
