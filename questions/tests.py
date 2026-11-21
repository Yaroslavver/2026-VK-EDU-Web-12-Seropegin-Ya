from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from core.models import Profile

from .models import Answer, AnswerLike, Question, QuestionLike, Tag, VoteValue


class QuestionPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username='author')
        cls.voter = get_user_model().objects.create_user(username='voter')
        cls.tag = Tag.objects.create(name='c++')
        cls.best = Question.objects.create(title='Лучший', text='Текст', author=cls.author)
        cls.newest = Question.objects.create(title='Новый', text='Текст', author=cls.author)
        cls.best.tags.add(cls.tag)
        cls.newest.tags.add(cls.tag)
        QuestionLike.objects.create(question=cls.best, user=cls.voter, value=VoteValue.UP)

    def test_question_lists_sort_and_filter(self):
        self.assertEqual(list(self.client.get('/').context['page']), [self.newest, self.best])
        self.assertEqual(list(self.client.get('/hot/').context['page']), [self.best, self.newest])
        by_tag = self.client.get('/tag/c++/').context['page']
        self.assertEqual(list(by_tag), [self.best, self.newest])

    def test_listing_loads_twenty_cards_with_fixed_query_count(self):
        questions = Question.objects.bulk_create([
            Question(title=f'Вопрос {index}', text='Текст', author=self.author)
            for index in range(21)
        ])
        links = Question.tags.through
        links.objects.bulk_create([links(question_id=item.pk, tag_id=self.tag.pk) for item in questions])

        with self.assertNumQueries(4):  # COUNT, вопросы с авторами, теги и снимок боковой колонки.
            first_page = self.client.get('/').context['page']
            self.assertEqual(len(first_page), 20)
        self.assertEqual(len(self.client.get('/?page=9999').context['page']), 3)
        self.assertEqual(self.client.get('/?page=bad').context['page'].number, 1)
        self.assertEqual(self.client.get('/?page=-2').context['page'].number, 1)

    def test_answers_are_ranked_and_paginated(self):
        answers = Answer.objects.bulk_create([
            Answer(question=self.best, text=f'Ответ {index}', author=self.author)
            for index in range(31)
        ])
        AnswerLike.objects.create(answer=answers[0], user=self.voter, value=VoteValue.UP)
        url = self.best.get_absolute_url()
        first_page = self.client.get(url).context['page']
        self.assertEqual(len(first_page), 30)
        self.assertEqual(first_page[0], answers[0])
        self.assertEqual(len(self.client.get(url, {'page': 2}).context['page']), 1)
        self.assertContains(self.client.get(self.newest.get_absolute_url()), 'Ответов пока нет')

    def test_empty_tag_and_missing_objects(self):
        Tag.objects.create(name='empty')
        self.assertContains(self.client.get('/tag/empty/'), 'Здесь пока нет вопросов')
        for url in ('/tag/unknown/', '/question/999/', '/question/abc/', '/question/-1/'):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), 'Страница не найдена', status_code=404)

    def test_vote_uniqueness_and_value_are_enforced_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestionLike.objects.create(question=self.best, user=self.voter, value=VoteValue.DOWN)

        answer = Answer.objects.create(question=self.best, text='Ответ', author=self.author)
        AnswerLike.objects.create(answer=answer, user=self.voter, value=VoteValue.DOWN)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AnswerLike.objects.create(answer=answer, user=self.voter, value=VoteValue.UP)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AnswerLike.objects.create(answer=answer, user=self.author, value=0)


class FillDatabaseTests(TestCase):
    def test_two_runs_add_exact_counts_and_related_profiles(self):
        for run in range(1, 3):
            call_command('fill_db', 2, stdout=StringIO())

            self.assertEqual(get_user_model().objects.count(), run * 2)
            self.assertEqual(Profile.objects.count(), run * 2)
            self.assertEqual(Tag.objects.count(), run * 2)
            self.assertEqual(Question.objects.count(), run * 20)
            self.assertEqual(Answer.objects.count(), run * 200)
            self.assertEqual(QuestionLike.objects.count() + AnswerLike.objects.count(), run * 400)

        self.assertEqual(
            set(Tag.objects.values_list('name', flat=True)),
            {'python', 'django', 'postgresql', 'javascript'},
        )
