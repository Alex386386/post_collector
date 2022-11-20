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
        cls.index = ('posts:index', None, 'posts/index.html', None)

        cls.group_page = ('posts:group_list', [cls.group.slug],
                          'posts/group_list.html', None)

        cls.profile = ('posts:profile', [cls.user], 'posts/profile.html',
                       None)

        cls.detail = ('posts:post_detail', [cls.post.id],
                      'posts/post_detail.html', None)
        cls.create = ('posts:post_create', None, '/auth/login/?next=/create/',
                      'posts/create_post.html')
        cls.edit = ('posts:post_edit', [cls.post.id],
                    f'/auth/login/?next=/posts/{cls.post.id}/edit/',
                    'posts/create_post.html')
        cls.url_create_detail = (cls.create, cls.detail)
        cls.url_create_edit = (cls.create, cls.edit)
        cls.url_names_code = [cls.index, cls.group_page, cls.profile,
                              cls.detail]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_urls_exists_at_desired_location_posts(self):
        """URL-адрес доступен для неавторизованного пользователя."""
        for address in self.url_names_code:
            with self.subTest(address=address):
                template_address, argument, _, _ = address
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument))
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 'status code не соответствует ожидаемому')

    def test_urls_authorized_exists_at_desired_location_posts(self):
        """URL-адрес доступен для любого посетителя."""
        for address in self.url_create_detail:
            with self.subTest(address=address):
                template_address, argument, _, _ = address
                response = self.authorized_client.get(reverse(template_address,
                                                              args=argument))
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_posts(self):
        """
        Страницы create и edit перенаправляют анонимного пользователя.
        Проверка статус кода.
        """
        for address in self.url_create_edit:
            with self.subTest(address=address):
                template_address, argument, _, _ = address
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument))
                self.assertEqual(response.status_code, HTTPStatus.FOUND,
                                 'status code не соответствует ожидаемому')

    def test_url_redirect_anonymous_address_posts(self):
        """
        Страницы create и edit перенаправляют анонимного пользователя.
        Проверка адреса перенаправления.
        """
        for address in self.url_create_edit:
            with self.subTest(address=address):
                template_address, argument, redirect_address, _ = address
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument),
                                                 follow=True)
                self.assertRedirects(response, redirect_address)

    def test_urls_uses_correct_template_posts(self):
        """
        URL-адреса index, group_page, profile, detail используют
        соответствующий шаблон.
        """
        for address in self.url_names_code:
            with self.subTest(address=address):
                template_address, argument, template, _ = address
                response = self.guest_client.get(reverse(template_address,
                                                         args=argument))
                self.assertTemplateUsed(response, template,
                                        f'не доступен данный адрес {address}')

    def test_urls_user_correct_template_authorized_posts(self):
        """
        URL-адреса create и edit использует соответствующий шаблон
        для авторизованного пользователя
        """
        for address in self.url_create_edit:
            with self.subTest(address=address):
                template_address, argument, _, page = address
                response = self.authorized_client.get(reverse(template_address,
                                                              args=argument))
                self.assertTemplateUsed(response, page,
                                        'не доступен данный адрес')

    def test_url_unexisting_page_posts(self):
        """"Проверка несуществующей страницы"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
