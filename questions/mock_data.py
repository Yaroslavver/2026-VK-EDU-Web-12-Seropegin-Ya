"""Данные-заглушки («рыба») для вопросов и ответов. В ДЗ3 их заменит выборка из базы данных."""

BASE_QUESTIONS = [
    ('ESP8266 перезагружается при подключении дисплея',
     'Подключаю SPI-дисплей, и плата уходит в бесконечный ребут. По питанию вроде всё в порядке. Куда копать?',
     ['arduino', 'esp8266']),
    ('Как сгруппировать данные по месяцам в pandas?',
     'Есть таблица продаж с колонкой date. Нужно посчитать сумму по каждому месяцу, но groupby по дате группирует по дням.',
     ['python', 'pandas']),
    ('Персонаж в Unity проваливается сквозь пол',
     'На персонаже Rigidbody и Capsule Collider, на полу Box Collider. При быстром падении он всё равно иногда пролетает насквозь.',
     ['unity', 'csharp']),
    ('Как отцентрировать блок по вертикали и горизонтали?',
     'Нужно поставить карточку ровно в центр экрана. margin: auto центрирует только по горизонтали. Какой способ сейчас считается правильным?',
     ['css', 'html']),
    ('Android-приложение падает при повороте экрана',
     'При смене ориентации Activity пересоздаётся, и приложение вылетает с NullPointerException. Как сохранить данные при повороте?',
     ['android', 'kotlin']),
    ('Python не видит установленную библиотеку',
     'Пишу pip install requests — установка проходит, но при запуске скрипта получаю ModuleNotFoundError.',
     ['python', 'pip']),
    ('Чем список отличается от кортежа в Python?',
     'Оба хранят набор элементов и умеют индексироваться. В каких случаях лучше брать tuple, а не list?',
     ['python']),
    ('Segmentation fault при работе с массивом в C++',
     'Программа падает на больших входных данных. Массив объявлен внутри функции, размер — миллион элементов.',
     ['c++', 'linux']),
]

AUTHORS = [
    ('null_pointer', 'core/img/avatar-1.svg'),
    ('Pythonista', 'core/img/avatar-2.svg'),
    ('git_push_force', 'core/img/avatar-3.svg'),
    ('CSS Wizard', 'core/img/avatar-4.svg'),
    ('Mira Dev', 'core/img/avatar-5.svg'),
]

ANSWER_TEXTS = [
    'Похоже, проблема в порядке инициализации. Попробуйте сначала настроить зависимости, а потом запускать основную логику — у меня это решило похожую ошибку.',
    'Проверьте версии библиотек: в новых версиях поменялось поведение по умолчанию. В документации к релизу это описано в разделе об изменениях.',
    'Посмотрите полный текст ошибки и строку, на которой она возникает. Чаще всего причина видна прямо в последних строках трейсбека.',
    'Сделайте минимальный пример, который воспроизводит проблему. Если на нём всё работает — значит, дело в остальном коде, и можно искать половинным делением.',
]

QUESTIONS_COUNT = 120


def _vote_state(number):
    """Голос текущего пользователя: up — лайк, down — дизлайк, none — не голосовал."""
    if number % 7 == 1:
        return 'up'
    if number % 7 == 2:
        return 'down'
    return 'none'


def _created(hours):
    if hours < 24:
        return f'{hours} ч назад'
    return f'{hours // 24} дн назад'


def _make_questions():
    questions = []
    for i in range(1, QUESTIONS_COUNT + 1):
        title, text, tags = BASE_QUESTIONS[(i - 1) % len(BASE_QUESTIONS)]
        author, avatar = AUTHORS[(i - 1) % len(AUTHORS)]
        questions.append({
            'id': i,
            'title': title,
            'text': text,
            'tags': tags,
            'author': author,
            'avatar': avatar,
            'rating': (i * 37) % 25 - 5,
            'answers_count': (i * 7) % 30,
            'vote': _vote_state(i),
            'created': _created(i * 3),
        })
    return questions


# Список уже отсортирован от новых к старым
QUESTIONS = _make_questions()


def get_hot_questions():
    return sorted(QUESTIONS, key=lambda q: q['rating'], reverse=True)


def get_questions_by_tag(tag_name):
    return [q for q in QUESTIONS if tag_name in q['tags']]


def get_question(question_id):
    if 1 <= question_id <= len(QUESTIONS):
        return QUESTIONS[question_id - 1]
    return None


def get_answers(question):
    answers = []
    for i in range(1, question['answers_count'] + 1):
        author, avatar = AUTHORS[(question['id'] + i) % len(AUTHORS)]
        answers.append({
            'id': i,
            'text': ANSWER_TEXTS[(question['id'] + i) % len(ANSWER_TEXTS)],
            'author': author,
            'avatar': avatar,
            'rating': (question['id'] * 3 + i * 11) % 15 - 3,
            'vote': _vote_state(question['id'] + i),
            'is_correct': i == 1 and question['id'] % 2 == 0,
            'created': _created(i),
        })
    return answers
