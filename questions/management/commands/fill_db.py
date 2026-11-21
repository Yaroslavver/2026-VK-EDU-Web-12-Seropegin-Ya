from datetime import timedelta
from itertools import batched, islice
from random import choice, random, randrange, sample
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.test.utils import override_settings
from django.utils import timezone
from faker import Faker

from core.models import Profile
from core.sidebar import refresh_sidebar

from ...demo_tags import available_demo_tag_names
from ...models import Answer, AnswerLike, Question, QuestionLike, Tag, VoteValue

BATCH_SIZE = 2000
ANSWERS_PER_QUESTION = 10


def write_batches(model, objects):
    for batch in batched(objects, BATCH_SIZE):
        model.objects.bulk_create(batch)


def make_votes(model, target_field, targets, user_ids, count):
    votes_per_target, remainder = divmod(count, len(targets))
    for index, target in enumerate(targets):
        offset = randrange(len(user_ids))
        for vote_index in range(votes_per_target + (index < remainder)):
            yield model(
                **{target_field: target.pk},
                user_id=user_ids[(offset + vote_index) % len(user_ids)],
                value=VoteValue.UP if random() < 0.75 else VoteValue.DOWN,
            )


class Command(BaseCommand):
    help = 'Добавляет в PostgreSQL тестовые данные. Для полного объёма используйте ratio=10001.'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    @override_settings(DEBUG=False)  # Не сохраняем в памяти SQL всех пакетных вставок.
    def handle(self, *args, ratio, **options):
        if ratio < 2:
            raise CommandError(
                'Укажите ratio не меньше 2. Один пользователь не может поставить 200 уникальных '
                'оценок для 10 вопросов и 100 ответов.',
            )

        fake = Faker('ru_RU')
        run_id = uuid4().hex[:12]
        now = timezone.now()
        earliest = now - timedelta(days=30)
        question_count = ratio * 10
        answer_count = question_count * ANSWERS_PER_QUESTION
        question_vote_count = min(ratio * 100, question_count * ratio)
        answer_vote_count = ratio * 200 - question_vote_count

        with transaction.atomic():
            # Проверяем FK в каждом INSERT, чтобы не накапливать проверки до конца транзакции.
            with connection.cursor() as cursor:
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')
            user_ids = self.create_users(fake, ratio, run_id, earliest)
            tag_ids = self.create_tags(ratio)
            questions = self.create_questions(fake, question_count, user_ids, tag_ids, earliest, now)
            write_batches(
                QuestionLike,
                make_votes(QuestionLike, 'question_id', questions, user_ids, question_vote_count),
            )
            self.stdout.write(f'Добавлено вопросов: {question_count}')
            self.create_answers(fake, questions, user_ids, now, answer_count, answer_vote_count)
            refresh_sidebar()

        self.stdout.write(self.style.SUCCESS(
            f'Добавлено: {ratio} пользователей и профилей, {ratio} тегов, '
            f'{question_count} вопросов, {answer_count} ответов, {ratio * 200} оценок.',
        ))

    def create_users(self, fake, ratio, run_id, earliest):
        user_model = get_user_model()
        user_ids = []
        for indices in batched(range(ratio), BATCH_SIZE):
            users = user_model.objects.bulk_create([
                user_model(
                    username=f'demo_{run_id}_{index}',
                    email=f'demo_{run_id}_{index}@example.com',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    password=make_password(None),
                    date_joined=earliest - timedelta(days=randrange(365)),
                )
                for index in indices
            ])
            user_ids.extend(user.pk for user in users)
            Profile.objects.bulk_create([
                Profile(user_id=user.pk, nickname=user.get_full_name()[:40]) for user in users
            ])
        return user_ids

    def create_tags(self, ratio):
        tag_ids = []
        names = islice(available_demo_tag_names(), ratio)
        for batch in batched(names, BATCH_SIZE):
            tags = Tag.objects.bulk_create([Tag(name=name) for name in batch])
            tag_ids.extend(tag.pk for tag in tags)
        return tag_ids

    def create_questions(self, fake, count, user_ids, tag_ids, earliest, now):
        links = Question.tags.through
        texts = fake.paragraphs(nb=1000)
        questions = []
        tag_count = min(3, len(tag_ids))
        for indices in batched(range(count), BATCH_SIZE):
            batch = Question.objects.bulk_create([
                Question(
                    title=fake.sentence(nb_words=8)[:120],
                    text=choice(texts),
                    author_id=choice(user_ids),
                    created=earliest + (now - earliest) * random(),
                )
                for _ in indices
            ])
            links.objects.bulk_create([
                links(question_id=question.pk, tag_id=tag_id)
                for question in batch
                for tag_id in sample(tag_ids, tag_count)
            ])
            questions.extend(batch)
        return questions

    def create_answers(self, fake, questions, user_ids, now, answer_count, vote_count):
        texts = fake.paragraphs(nb=2000)
        answers = (
            Answer(
                question_id=question.pk,
                text=choice(texts),
                author_id=choice(user_ids),
                created=question.created + (now - question.created) * random(),
                is_correct=question_index % 3 == 0 and answer_index == 0,
            )
            for question_index, question in enumerate(questions)
            for answer_index in range(ANSWERS_PER_QUESTION)
        )
        votes_per_answer, remainder = divmod(vote_count, answer_count)
        seen = 0
        for batch in batched(answers, BATCH_SIZE):
            saved = Answer.objects.bulk_create(batch)
            count = len(saved) * votes_per_answer + max(0, min(len(saved), remainder - seen))
            write_batches(
                AnswerLike,
                make_votes(AnswerLike, 'answer_id', saved, user_ids, count),
            )
            seen += len(saved)
            if seen % 100_000 == 0:
                self.stdout.write(f'Добавлено ответов: {seen}/{answer_count}')
