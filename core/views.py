from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.csrf import csrf_failure as default_csrf_failure
from django.views.decorators.http import require_http_methods

from .forms import ProfileForm, SignupForm


@require_http_methods(['GET', 'HEAD', 'POST'])
def signup(request):
    if request.user.is_authenticated:
        return redirect('questions:index')
    form = SignupForm(request.POST, request.FILES) if request.method == 'POST' else SignupForm()
    if form.is_bound and form.is_valid():
        login(request, form.save())
        return redirect('questions:index')
    return render(request, 'core/signup.html', {'form': form})


@login_required
@require_http_methods(['GET', 'HEAD', 'POST'])
def profile(request):
    form = (
        ProfileForm(request.POST, request.FILES, user=request.user)
        if request.method == 'POST' else ProfileForm(user=request.user)
    )
    if form.is_bound and form.is_valid():
        form.save()
        messages.success(request, 'Настройки сохранены.')
        return redirect('core:profile')
    return render(request, 'core/profile.html', {'form': form})


def csrf_failure(request, reason=''):
    match = request.resolver_match
    if match and match.view_name in ('questions:question_vote', 'questions:answer_vote', 'questions:correct_answer'):
        return JsonResponse({'error': 'Срок действия формы истёк. Обновите страницу и попробуйте снова.'}, status=403)
    return default_csrf_failure(request, reason=reason)
