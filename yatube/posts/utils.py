from django.core.paginator import Paginator

from .models import Post


def run_pag(list_obj, request, filters):
    """
    Функция Paginator для переработки списка постов
    в объект типа page_object
    """
    paginator = Paginator(list_obj, filters)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def post_generator(post_limit, author, group):
    """
    Генератор создания постов с количеством равном принятому аргументу
    """
    for id_text in range(post_limit):
        yield Post(
            author=author,
            text=f'Тестовый пост{id_text}',
            group=group,
        )
        id_text += 1


def create_post(post_limit, author, group):
    """Функция создания постов с использованием генератора"""
    return Post.objects.bulk_create(post_generator(
        post_limit,
        author,
        group,
    ))
