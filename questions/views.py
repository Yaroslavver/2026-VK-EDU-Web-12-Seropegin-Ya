from django.http import Http404
from django.shortcuts import render

from core.mock_data import MOCK_USER
from core.utils import paginate

from . import mock_data


def index(request):
    page = paginate(mock_data.QUESTIONS, request)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    page = paginate(mock_data.get_hot_questions(), request)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    page = paginate(mock_data.get_questions_by_tag(tag_name), request)
    return render(request, 'questions/tag.html', {'page': page, 'tag_name': tag_name})


def question(request, question_id):
    item = mock_data.get_question(question_id)
    if item is None:
        raise Http404('Question not found')
    answers_page = paginate(mock_data.get_answers(item), request, per_page=5)
    return render(request, 'questions/question.html', {'question': item, 'page': answers_page})


def ask(request):
    return render(request, 'questions/ask.html', {'mock_user': MOCK_USER})
