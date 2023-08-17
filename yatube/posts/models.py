from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel
from core.work_constants import TITLE_LIMITATION

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
    )
    slug = models.SlugField(
        unique=True,
        max_length=20,
        verbose_name='slug-значение группы'
    )
    description = models.TextField(
        verbose_name='Описание группы',
    )

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:TITLE_LIMITATION]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        related_name='comments',
        verbose_name='Комментарий поста',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария',
    )
    
    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор на которого подписываются',
    )
