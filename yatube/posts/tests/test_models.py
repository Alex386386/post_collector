from django.test import TestCase

from posts.models import Group, Post, Comment, Follow, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        model_str = (
            (post.__str__(), post.text[:15]),
            (group.__str__(), group.title),
        )
        for act, expected in model_str:
            with self.subTest(act=act):
                self.assertEqual(act, expected,
                                 '__str__ метод модели работает неправильно')

    def test_verbose_name_post(self):
        """В полях модели post, verbose_name совпадает с ожидаемым."""
        post = self.post
        field_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_group(self):
        """В полях модели group, verbose_name совпадает с ожидаемым."""
        group = self.group
        field_verbose = {
            'title': 'Название группы',
            'slug': 'slug-значение группы',
            'description': 'Описание группы',
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_comment(self):
        """В полях модели comment, verbose_name совпадает с ожидаемым."""
        comment = self.comment
        field_verbose = {
            'post': 'Комментарий поста',
            'author': 'Автор комментария',
            'text': 'Текст комментария',
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_follow(self):
        """В полях модели follow, verbose_name совпадает с ожидаемым."""
        follow = self.follow
        field_verbose = {
            'user': 'Подписчик',
            'author': 'Автор на которого подписываются',
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """В полях модели post, help_text совпадает с ожидаемым."""
        post = self.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)
