# Post_collector

### Описание

Проект представляет собой сайт для публикации постов различного содержания, возможно даже с картинками.
Читать посты могут все, сохранять и создавать группы только авторизованные пользователи.
Есть возможность комментировать посты, подписываться на пользователей.

### Stack

Python 3.7, Django 2.2.16

### Установка, Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

https://github.com/Alex386386/post_collector

```
git@github.com:Alex386386/post_collector
```

```
cd hw_05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Создать суперюзера:

```
python3 manage.py createsuperuser
```

Загрузить данные в БД:

```
python3 manage.py load_all_data
```

Запустить проект:

```
python3 manage.py runserver
```

Автор:
- [Александр Мамонов](https://github.com/Alex386386) 