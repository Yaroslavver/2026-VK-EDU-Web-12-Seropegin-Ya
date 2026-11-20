# DevHelp — VK EDU Web

DevHelp — сервис вопросов и ответов для разработчиков в духе Stack Overflow.

- **ДЗ1** — статическая верстка в папке `public/`.
- **ДЗ2** — Django-проект: views с данными-заглушками, маршруты, шаблоны с наследованием, пагинация, Docker.

## Запуск локально (Windows)

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py runserver
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py runserver
```

Сайт откроется на http://127.0.0.1:8000/

## Запуск через Docker Compose

```bash
copy .env.example .env      # на macOS / Linux: cp .env.example .env
docker compose up --build
```

Сайт откроется на http://localhost:8000/ . Остановить — `Ctrl+C`, затем `docker compose down`.

## Переменные окружения

Все настройки читаются из файла `.env` (в Git не хранится). Список переменных — в `.env.example`:

| Переменная | Что это |
|---|---|
| `SECRET_KEY` | секретный ключ Django (для разработки подойдёт любая строка) |
| `DEBUG` | режим отладки: `True` / `False` |
| `ALLOWED_HOSTS` | адреса, на которых работает сайт, через запятую |

## Страницы и маршруты

| URL | Имя маршрута | Страница |
|---|---|---|
| `/` | `questions:index` | новые вопросы |
| `/hot/` | `questions:hot` | лучшие вопросы |
| `/tag/<tag>/` | `questions:tag` | вопросы по тегу, например `/tag/python/` |
| `/question/<id>/` | `questions:question` | вопрос и ответы, например `/question/35/` |
| `/ask/` | `questions:ask` | новый вопрос |
| `/login/` | `core:login` | вход |
| `/signup/` | `core:signup` | регистрация |
| `/profile/` | `core:profile` | настройки профиля |

Все списки разбиты на страницы параметром `?page=N`. Некорректные значения (`?page=abc`, `?page=0`, `?page=999`) не ломают страницу: показывается первая или последняя страница.

## Структура

```
application/            настройки проекта (settings.py, urls.py)
core/                   пользователи: вход, регистрация, профиль; общий layout
  templates/core/       base.html, includes/ (header, sidebar, footer, pagination)
  static/core/          Bootstrap, общие стили, картинки
  utils.py              функция paginate()
questions/              вопросы и ответы
  templates/questions/  листинги, страница вопроса, includes/ (карточки, лайки, теги)
  static/questions/     стили карточек и лайков
  mock_data.py          данные-заглушки (в ДЗ3 их заменит база данных)
public/                 статическая верстка ДЗ1
```

## Статическая верстка ДЗ1

Открыть `public/index.html` в браузере.
