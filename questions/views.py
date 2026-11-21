from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.utils import paginate

from .forms import AnswerForm, QuestionForm
from .models import ANSWERS_PER_PAGE, Answer, Question, Tag


def render_question_list(request, template, questions, **context):
    page = paginate(questions.with_user_vote(request.user), request)
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


def get_question(request, question_id):
    return get_object_or_404(Question.objects.with_details().with_user_vote(request.user), pk=question_id)


def render_question(request, item, form):
    answers = Answer.objects.for_question(item).with_user_vote(request.user)
    page = paginate(answers, request, per_page=ANSWERS_PER_PAGE)
    return render(request, 'questions/question.html', {'question': item, 'page': page, 'form': form})


@require_http_methods(['GET', 'HEAD', 'POST'])
def question(request, question_id):
    if request.method == 'POST':
        return post_answer(request, question_id)
    item = get_question(request, question_id)
    return render_question(request, item, AnswerForm(question=item, author=request.user))


@login_required
def post_answer(request, question_id):
    item = get_question(request, question_id)
    form = AnswerForm(request.POST, question=item, author=request.user)
    if form.is_valid():
        return redirect(form.save())
    return render_question(request, item, form)


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
def ask(request):
    form = QuestionForm(request.POST if request.method == 'POST' else None, author=request.user)
    if form.is_bound and form.is_valid():
        return redirect(form.save())
    return render(request, 'questions/ask.html', {'form': form})
