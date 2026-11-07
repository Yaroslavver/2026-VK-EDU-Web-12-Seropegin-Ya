from django.shortcuts import render

from .mock_data import MOCK_USER


def login(request):
    return render(request, 'core/login.html')


def signup(request):
    return render(request, 'core/signup.html')


def profile(request):
    return render(request, 'core/profile.html', {'mock_user': MOCK_USER})
