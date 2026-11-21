from django.urls import path

from . import action_views, views
from .models import Answer, Question

app_name = 'questions'

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('question/<int:target_id>/vote/', action_views.vote, {'model': Question}, name='question_vote'),
    path('answer/<int:target_id>/vote/', action_views.vote, {'model': Answer}, name='answer_vote'),
    path('question/<int:question_id>/correct-answer/', action_views.correct_answer, name='correct_answer'),
    path('ask/', views.ask, name='ask'),
]
