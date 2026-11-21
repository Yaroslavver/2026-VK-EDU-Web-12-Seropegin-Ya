from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

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


class QuestionActionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.author = users.create_user(username='author')
        cls.member = users.create_user(username='member')
        cls.item = Question.objects.create(title='Вопрос', text='Описание', author=cls.author)

    def test_only_signed_in_users_publish_questions_and_tag_count_is_validated(self):
        self.assertRedirects(self.client.get('/ask/'), '/login/?next=/ask/', fetch_redirect_response=False)
        self.client.force_login(self.member)
        payload = {'title': 'Как настроить Django?', 'text': 'Описание настройки.'}
        response = self.client.post('/ask/', {**payload, 'tags': 'one,two,three,four'})
        form = response.context['form']
        self.assertIn('tags', form.errors)
        self.assertEqual(form['title'].value(), payload['title'])
        self.assertEqual(Question.objects.count(), 1)

        existing = Tag.objects.create(name='django')
        response = self.client.post('/ask/', {**payload, 'tags': ' Django , ORM, django '})
        saved = Question.objects.get(title=payload['title'])
        self.assertRedirects(response, saved.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(saved.author, self.member)
        self.assertEqual(list(saved.tags.values_list('name', flat=True)), ['django', 'orm'])
        self.assertTrue(saved.tags.filter(pk=existing.pk).exists())

    def test_answer_redirects_to_its_actual_ranked_page_and_anchor(self):
        url = self.item.get_absolute_url()
        denied = self.client.post(url, {'text': 'Ответ гостя'})
        self.assertRedirects(denied, f'/login/?next={url}', fetch_redirect_response=False)
        self.assertFalse(self.item.answers.exists())

        answers = Answer.objects.bulk_create([
            Answer(question=self.item, author=self.author, text=f'Популярный ответ {index}')
            for index in range(30)
        ])
        AnswerLike.objects.bulk_create([
            AnswerLike(answer=answer, user=self.author, value=VoteValue.UP) for answer in answers
        ])
        self.client.force_login(self.member)
        invalid = self.client.post(f'{url}?page=1', {'text': ''})
        self.assertIn('text', invalid.context['form'].errors)
        response = self.client.post(url, {'text': 'Мой новый ответ'})
        new_answer = self.item.answers.get(author=self.member)
        self.assertRedirects(response, f'{url}?page=2#answer-{new_answer.pk}')
        self.assertContains(self.client.get(f'{url}?page=2'), f'id="answer-{new_answer.pk}"')

    def test_votes_are_idempotent_changeable_and_removable_for_both_targets(self):
        answer = self.item.answers.create(text='Ответ', author=self.author)
        self.client.force_login(self.member)
        targets = [
            ('questions:question_vote', self.item),
            ('questions:answer_vote', answer),
        ]
        for name, target in targets:
            url = reverse(name, args=[target.pk])
            for value in (1, 1, -1, 0, 0):
                with self.subTest(url=url, value=value):
                    response = self.client.post(url, {'value': value})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json(), {'rating': value, 'vote': value})
                    self.assertEqual(target.votes.count(), int(value != 0))
                    if value:
                        detail = self.client.get(self.item.get_absolute_url())
                        self.assertContains(detail, f'data-state="{ "up" if value == 1 else "down" }"')

    def test_ajax_returns_json_errors_for_bad_method_input_authentication_and_csrf(self):
        url = reverse('questions:question_vote', args=[self.item.pk])
        self.assertEqual(self.client.get(url).json().keys(), {'error'})
        self.assertEqual(self.client.get(url).status_code, 405)
        guest = self.client.post(url, {'value': 1})
        self.assertEqual(guest.status_code, 401)
        self.assertEqual(guest.json()['login_url'], '/login/')

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        failure = client.post(url, {'value': 1})
        self.assertEqual(failure.status_code, 403)
        self.assertIn('error', failure.json())
        client.get(self.item.get_absolute_url())
        token = client.cookies['csrftoken'].value
        bad_vote = client.post(url, {'value': 4, 'csrfmiddlewaretoken': token})
        self.assertEqual(bad_vote.status_code, 400)
        self.assertIn('value', bad_vote.json()['fields'])
        missing = reverse('questions:question_vote', args=[self.item.pk + 999])
        self.assertEqual(client.post(missing, {'value': 1, 'csrfmiddlewaretoken': token}).status_code, 404)
        self.assertEqual(client.post(url, {'value': 1, 'csrfmiddlewaretoken': token}).status_code, 200)

    def test_only_author_can_set_replace_and_unset_a_related_correct_answer(self):
        first = self.item.answers.create(text='Первый ответ', author=self.member)
        second = self.item.answers.create(text='Второй ответ', author=self.member)
        other = Question.objects.create(title='Другой вопрос', text='Другой текст', author=self.author)
        unrelated = other.answers.create(text='Чужой ответ', author=self.member)
        url = reverse('questions:correct_answer', args=[self.item.pk])
        page_url = self.item.get_absolute_url()

        self.assertNotContains(self.client.get(page_url), 'data-correct-form')
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get(page_url), 'data-correct-form')
        forbidden = self.client.post(url, {'answer_id': first.pk, 'accepted': 1})
        self.assertEqual(forbidden.status_code, 403)
        self.assertFalse(self.item.answers.filter(is_correct=True).exists())

        self.client.force_login(self.author)
        self.assertContains(self.client.get(page_url), 'data-correct-form', count=2)
        self.assertEqual(
            self.client.post(url, {'answer_id': first.pk, 'accepted': 1}).json(),
            {'correct_answer_id': first.pk},
        )
        self.assertEqual(self.client.post(url, {'answer_id': unrelated.pk, 'accepted': 1}).status_code, 404)
        self.assertEqual(
            self.client.post(url, {'answer_id': second.pk, 'accepted': 1}).json(),
            {'correct_answer_id': second.pk},
        )
        self.assertEqual(list(self.item.answers.filter(is_correct=True)), [second])
        self.assertEqual(
            self.client.post(url, {'answer_id': second.pk, 'accepted': 0}).json(),
            {'correct_answer_id': None},
        )
