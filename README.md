# DevHelp — VK EDU Web

DevHelp — сервис вопросов и ответов для разработчиков в духе Stack Overflow.

- **ДЗ1** — статическая верстка в папке `public/`.
- **ДЗ2** — Django-проект: views с данными-заглушками, маршруты, шаблоны с наследованием, пагинация, Docker.
- **ДЗ3** — PostgreSQL, модели и русскоязычная админка. Листинги и страницы вопросов показывают данные из базы.
- **ДЗ4** — регистрация, вход и выход, настройки профиля, публикация вопросов и ответов, голоса и отметка правильного ответа.

## Запуск через Docker Compose

При первом запуске нужно создать `.env.docker` из `.env.example` и задать значения `SECRET_KEY` и `POSTGRES_PASSWORD`. Затем:

```powershell
docker compose up --build -d --wait
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py fill_db 20
```

Сайт доступен на http://127.0.0.1:8000/, админка на http://127.0.0.1:8000/admin/. Django применяет миграции при запуске контейнера. Команда `docker compose down` останавливает сервисы, сохраняя базу в томе `db_data`.

## Запуск с локальным PostgreSQL

1. Нужно создать `.env.local` из `.env.example`. Заполнить `SECRET_KEY` и `POSTGRES_PASSWORD`.
2. Запустить PostgreSQL. Под администратором PostgreSQL создать роль и базу. В интерактивном `psql` с правами администратора выполнить эти команды и ввести пароль из `.env.local` по приглашению:

```sql
CREATE ROLE devhelp LOGIN;
\password devhelp
CREATE DATABASE devhelp OWNER devhelp;
```

3. Выполнить:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py fill_db 20
.\venv\Scripts\python.exe manage.py runserver
```

## Тестовые данные

`python manage.py fill_db <ratio>` добавляет `ratio` пользователей, профилей и тегов, `10 × ratio` вопросов, `100 × ratio` ответов и `200 × ratio` оценок. Каждый запуск добавляет отдельный набор данных.

- `ratio=20` подходит для быстрой проверки. Чтобы проверить пустые состояния, нужно открыть сайт после миграций, до вызова `fill_db`.
- `ratio=10001` даёт 10 001 пользователя, 10 001 тег, 100 010 вопросов, 1 000 100 ответов и 2 000 200 оценок. Такой запуск рассчитан на отдельную тестовую базу.
- Минимальный коэффициент — 2. При `ratio=1` один пользователь может поставить максимум 110 уникальных оценок.

Команда `fill_db` обновляет популярные теги и лучших участников за неделю. После ручных изменений в админке эту выборку можно пересчитать командой `python manage.py refresh_sidebar`. Страницы читают сохранённый результат из PostgreSQL, поэтому открытие страницы не запускает пересчёт.

Проверки можно запустить через `docker compose exec web python manage.py test`. Для локального запуска тестов роли PostgreSQL потребуется право создавать тестовую базу.

## Проверка ДЗ4 в браузере

Зарегистрируйте аккаунт через `/signup/`, загрузите JPEG или PNG до 2 МБ в `/profile/` и опубликуйте вопрос. Добавьте ответ, проверьте лайк, смену оценки на дизлайк и отмену повторным нажатием текущей кнопки. Автор вопроса может отметить правильный ответ, выбрать другой или снять отметку. Для проверки прав нужно открыть тот же вопрос под другим аккаунтом и как гость.

## Переменные окружения

Пример настроек хранится в `.env.example`. Файлы `.env.local` и `.env.docker` игнорируются Git.

| Переменная | Назначение |
|---|---|
| `SECRET_KEY` | Секретный ключ Django |
| `DEBUG` | Режим отладки. Django Debug Toolbar подключается при `True` |
| `ALLOWED_HOSTS` | Разрешённые адреса приложения через запятую |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | База, роль и пароль PostgreSQL |
| `DB_HOST`, `DB_PORT` | Адрес PostgreSQL. Compose задаёт `db:5432` внутри своей сети |
| `INTERNAL_IPS` | Адреса, с которых доступна Debug Toolbar |

## Страницы и маршруты

| URL | Имя маршрута | Страница |
|---|---|---|
| `/` | `questions:index` | новые вопросы |
| `/hot/` | `questions:hot` | лучшие вопросы |
| `/tag/<tag>/` | `questions:tag` | вопросы по тегу, например `/tag/python/` |
| `/question/<id>/` | `questions:question` | вопрос и ответы, например `/question/35/` |
| `/ask/` | `questions:ask` | новый вопрос |
| `/login/` | `core:login` | вход |
| `/logout/` | `core:logout` | выход (POST) |
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
  models.py             модели и выборки Django ORM
  management/commands/ команда fill_db
  templates/questions/  листинги, страница вопроса, includes/ (карточки, лайки, теги)
  static/questions/     стили карточек и лайков
public/                 статическая верстка ДЗ1
```

## Статическая верстка ДЗ1

Открыть `public/index.html` в браузере.
