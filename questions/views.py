from django.shortcuts import get_object_or_404, render

from core.utils import paginate

from .models import Answer, Question, Tag


def render_question_list(request, template, questions, **context):
    page = paginate(questions, request)
    return render(request, template, {'page': page, **context})


def index(request):
    return render_question_list(request, 'questions/index.html', Question.objects.newest())


def hot(request):
    return render_question_list(request, 'questions/hot.html', Question.objects.best())


def tag(request, tag_name):
    current_tag = get_object_or_404(Tag, name=tag_name)
    return render_question_list(
        request, 'questions/tag.html', Question.objects.by_tag(current_tag), tag_name=current_tag.name,
    )


def question(request, question_id):
    item = get_object_or_404(Question.objects.with_details(), pk=question_id)
    page = paginate(Answer.objects.for_question(item), request, per_page=30)
    return render(request, 'questions/question.html', {'question': item, 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
