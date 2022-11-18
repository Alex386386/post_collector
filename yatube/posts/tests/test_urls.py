from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User


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
        cls.index = ('posts:index', None)
        cls.group_page = ('posts:group_list', ['test-slug'])
        cls.profile = ('posts:profile', [cls.user])
        cls.detail = ('posts:post_detail', [cls.post.id])
        cls.create = ('posts:post_create', None)
        cls.edit = ('posts:post_edit', [cls.post.id])

        cls.url_create_detail = (cls.create, cls.detail)
        cls.url_create_edit = (cls.create, cls.edit)
        cls.create_redirect = (
            cls.create,
            '/auth/login/?next=/create/',
            'posts/create_post.html',
        )
        cls.edit_redirect = (
            cls.edit,
            f'/auth/login/?next=/posts/{cls.post.id}/edit/',
            'posts/create_post.html',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_urls_exists_at_desired_location_posts(self):
        """URL-адрес доступен для неавторизованного пользователя."""
        url_names_code = [
            self.index,
            self.group_page,
            self.profile,
            self.detail,
        ]
        for address in url_names_code:
            with self.subTest(address=address):
                template_address, argument = address
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument))
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 'status code не соответствует ожидаемому')

    def test_urls_authorized_exists_at_desired_location_posts(self):
        """URL-адрес доступен."""
        for address in self.url_create_detail:
            with self.subTest(address=address):
                template_address, argument = address
                response = self.authorized_client.get(reverse(template_address,
                                                              args=argument))
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_posts(self):
        """Страница перенаправляет анонимного пользователя."""
        for address in self.url_create_edit:
            with self.subTest(address=address):
                template_address, argument = address
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument))
                self.assertEqual(response.status_code, HTTPStatus.FOUND,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_address_posts(self):
        """Страница перенаправляет анонимного пользователя."""
        url_names = (
            self.create_redirect,
            self.edit_redirect,
        )
        for address in url_names:
            with self.subTest(address=address):
                template, redirect_address, _ = address
                template_address, argument = template
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument),
                                                 follow=True)
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
                template_address, argument = address
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument))
                self.assertTemplateUsed(response, template,
                                        f'не доступен данный адрес {address}')

    def test_urls_user_correct_template_authorized_posts(self):
        """
        URL-адрес использует соответствующий шаблон
        для авторизованного пользователя
        """
        templates_url_names = (
            self.create_redirect,
            self.edit_redirect,
        )
        for address in templates_url_names:
            with self.subTest(address=address):
                template, _, page = address
                template_address, argument = template
                response = self.authorized_client.get(reverse(template_address,
                                                              args=argument))
                self.assertTemplateUsed(response, page,
                                        'не доступен данный адрес')

    def test_url_unexisting_page_posts(self):
        """"Проверка несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
