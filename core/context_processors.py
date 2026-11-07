from .mock_data import BEST_MEMBERS, POPULAR_TAGS


def sidebar(request):
    """Данные правой колонки нужны на каждой странице — передаём их во все шаблоны сразу."""
    return {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS,
    }
