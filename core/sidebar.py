from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.utils import timezone

from questions.models import Answer, Question, Tag


def get_sidebar():
    return caches['sidebar'].get('sidebar', {})


def refresh_sidebar():
    since = timezone.now() - timedelta(days=7)
    scores = dict(Question.objects.top_authors(since, 10))
    for author_id, rating in Answer.objects.top_authors(since, 10):
        scores[author_id] = max(rating, scores.get(author_id, rating))

    author_ids = sorted(scores, key=lambda author_id: (-scores[author_id], author_id))[:10]
    authors = get_user_model().objects.select_related('profile').in_bulk(author_ids)
    best_members = []
    for author_id in author_ids:
        if author := authors.get(author_id):
            profile = getattr(author, 'profile', None)
            best_members.append(profile.nickname if profile and profile.nickname else author.get_username())

    caches['sidebar'].set('sidebar', {
        'popular_tags': list(Tag.objects.popular().values_list('name', flat=True)[:20]),
        'best_members': best_members,
    }, timeout=None)
