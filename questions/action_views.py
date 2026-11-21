from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.urls import reverse

from .forms import CorrectAnswerForm, VoteForm


def submit_action(request, form_class, **kwargs):
    if request.method != 'POST':
        return JsonResponse({'error': 'Используйте POST для этого действия.'}, status=405, headers={'Allow': 'POST'})
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Войдите, чтобы выполнить это действие.',
            'login_url': reverse('core:login'),
        }, status=401)

    form = form_class(request.POST, user=request.user, **kwargs)
    if not form.is_valid():
        return JsonResponse({'error': 'Проверьте параметры запроса.', 'fields': form.errors.get_json_data()}, status=400)

    try:
        return JsonResponse(form.save())
    except PermissionDenied as error:
        return JsonResponse({'error': str(error)}, status=403)
    except Http404:
        return JsonResponse({'error': 'Вопрос или ответ не найден.'}, status=404)


def vote(request, target_id, model):
    return submit_action(request, VoteForm, model=model, target_id=target_id)


def correct_answer(request, question_id):
    return submit_action(request, CorrectAnswerForm, question_id=question_id)
