from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    """Возвращает нужную страницу списка (или QuerySet) по параметру ?page=.

    Некорректные значения заменяются на значения по умолчанию:
    - не число (?page=abc)          -> первая страница;
    - меньше 1 (?page=0, ?page=-5)  -> первая страница;
    - больше числа страниц (?page=999) -> последняя страница.
    Для шаблона пагинатора к странице добавляется page.elided_range —
    список номеров с многоточиями: 1 … 4 5 6 … 12.
    """
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages if int(page_number) > 1 else 1)

    page.elided_range = list(
        paginator.get_elided_page_range(page.number, on_each_side=2, on_ends=1)
    )
    return page
