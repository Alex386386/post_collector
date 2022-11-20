from django.test import TestCase

from core.work_constants import TITLE_LIMITATION
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
        model_str = (
            (self.post.__str__(), self.post.text[:TITLE_LIMITATION]),
            (self.group.__str__(), self.group.title),
        )
        for model_method, expected in model_str:
            with self.subTest(model_method=model_method):
                self.assertEqual(model_method, expected,
                                 '__str__ метод модели'
                                 f'{model_method.__class__.__name__}'
                                 'работает неправильно')

    def test_verbose_name(self):
        """В полях модели post, verbose_name совпадает с ожидаемым."""
        models = [
            (self.post, (
                ('text', 'Текст поста'),
                ('pub_date', 'Дата публикации'),
                ('author', 'Автор'),
                ('group', 'Группа'))),
            (self.group, (
                ('title', 'Название группы'),
                ('slug', 'slug-значение группы'),
                ('description', 'Описание группы'))),
            (self.comment, (
                ('post', 'Комментарий поста'),
                ('author', 'Автор комментария'),
                ('text', 'Текст комментария'))),
            (self.follow, (
                ('user', 'Подписчик'),
                ('author', 'Автор на которого подписываются')))
        ]
        for model, fields in models:
            for value, expected in fields:
                with self.subTest(value=value):
                    self.assertEqual(
                        model._meta.get_field(value).verbose_name,
                        expected
                    )

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
