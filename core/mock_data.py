"""Данные-заглушки («рыба») для общих блоков сайта. В ДЗ3 их заменит база данных."""

MOCK_USER = {
    'login': 'byte_master',
    'nickname': 'Byte Master',
    'email': 'byte.master@mail.ru',
    'avatar': 'core/img/avatar-me.svg',
}

# size: s / m / l — размер шрифта в облаке тегов, hot — выделить цветом
POPULAR_TAGS = [
    {'name': 'python', 'size': 'l', 'hot': True},
    {'name': 'c++', 'size': 'm', 'hot': False},
    {'name': 'linux', 'size': 's', 'hot': False},
    {'name': 'javascript', 'size': 'l', 'hot': True},
    {'name': 'css', 'size': 'm', 'hot': False},
    {'name': 'unity', 'size': 's', 'hot': False},
    {'name': 'arduino', 'size': 'm', 'hot': False},
    {'name': 'pandas', 'size': 's', 'hot': False},
    {'name': 'android', 'size': 'm', 'hot': False},
    {'name': 'sql', 'size': 's', 'hot': False},
    {'name': 'regex', 'size': 's', 'hot': False},
]

BEST_MEMBERS = ['null_pointer', 'Pythonista', 'git_push_force', 'CSS Wizard', 'Mira Dev']
