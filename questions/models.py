from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, F, FilteredRelation, Max, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

ANSWERS_PER_PAGE = 30


class TagQuerySet(models.QuerySet):
    def popular(self):
        return (
            self.annotate(usage=Count('questions'))
            .filter(usage__gt=0)
            .order_by('-usage', 'name')
        )


def related_total(queryset, field, aggregate):
    totals = (
        queryset.filter(**{field: OuterRef('pk')}).order_by()
        .values(field).annotate(total=aggregate).values('total')
    )
    return Coalesce(Subquery(totals), 0)


class RatedQuerySet(models.QuerySet):
    def with_user_vote(self, user):
        if not user.is_authenticated:
            return self
        return self.annotate(
            viewer_vote=FilteredRelation('votes', condition=Q(votes__user_id=user.pk)),
            user_vote=F('viewer_vote__value'),
        )

    def top_authors(self, since, limit):
        return (
            self.filter(created__gte=since).with_rating().order_by()
            .values('author_id').annotate(best_rating=Max('rating'))
            .order_by('-best_rating', 'author_id')
            .values_list('author_id', 'best_rating')[:limit]
        )


class QuestionQuerySet(RatedQuerySet):
    def with_rating(self):
        return self.annotate(rating=related_total(QuestionLike.objects, 'question', Sum('value')))

    def with_details(self):
        return self.with_rating().select_related('author__profile').prefetch_related('tags')

    def for_cards(self):
        return self.with_details().annotate(
            answers_count=related_total(Answer.objects, 'question', Count('pk')),
        )

    def newest(self):
        return self.for_cards().order_by('-created', '-pk')

    def best(self):
        return self.for_cards().order_by('-rating', '-created', '-pk')

    def by_tag(self, tag):
        return self.filter(tags=tag).best()


class AnswerQuerySet(RatedQuerySet):
    def with_rating(self):
        return self.annotate(rating=related_total(AnswerLike.objects, 'answer', Sum('value')))

    def for_question(self, question):
        return (
            self.filter(question=question).with_rating().select_related('author__profile')
            .order_by('-rating', '-created', '-pk')
        )

    def page_for(self, answer):
        ranked = self.filter(question_id=answer.question_id).with_rating()
        rating = ranked.values_list('rating', flat=True).get(pk=answer.pk)
        preceding = ranked.filter(
            Q(rating__gt=rating)
            | Q(rating=rating, created__gt=answer.created)
            | Q(rating=rating, created=answer.created, pk__gt=answer.pk),
        ).count()
        return preceding // ANSWERS_PER_PAGE + 1


class Tag(models.Model):
    name = models.CharField(
        'название', max_length=50, unique=True,
        validators=[RegexValidator(r'\A(?!\.{1,2}\Z)[^/\s]+\Z', 'Введите один тег без пробелов и косых черт.')],
    )
    objects = TagQuerySet.as_manager()

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.name


class Question(models.Model):
    title = models.CharField('заголовок', max_length=120)
    text = models.TextField('текст', max_length=5000)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='автор', related_name='questions',
    )
    created = models.DateTimeField('дата создания', default=timezone.now, editable=False)
    tags = models.ManyToManyField(Tag, verbose_name='теги', related_name='questions', blank=True)
    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'
        indexes = [models.Index(fields=['-created', '-id'], name='question_created_idx')]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('questions:question', kwargs={'question_id': self.pk})


class Answer(models.Model):
    question = models.ForeignKey(
        Question, models.CASCADE, verbose_name='вопрос', related_name='answers',
    )
    text = models.TextField('текст', max_length=5000)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='автор', related_name='answers',
    )
    created = models.DateTimeField('дата создания', default=timezone.now, editable=False, db_index=True)
    is_correct = models.BooleanField('правильный ответ', default=False)
    objects = AnswerQuerySet.as_manager()

    class Meta:
        verbose_name = 'ответ'
        verbose_name_plural = 'ответы'
        constraints = [
            models.UniqueConstraint(
                fields=['question'], condition=models.Q(is_correct=True),
                name='one_correct_answer_per_question',
            ),
        ]

    def __str__(self):
        return self.text[:80]

    def get_absolute_url(self):
        page = Answer.objects.page_for(self)
        return f'{self.question.get_absolute_url()}?page={page}#answer-{self.pk}'


class VoteValue(models.IntegerChoices):
    DOWN = -1, 'Дизлайк'
    UP = 1, 'Лайк'


class QuestionLike(models.Model):
    question = models.ForeignKey(
        Question, models.CASCADE, verbose_name='вопрос', related_name='votes', db_index=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='пользователь',
        related_name='question_votes',
    )
    value = models.SmallIntegerField('оценка', choices=VoteValue)

    class Meta:
        verbose_name = 'оценка вопроса'
        verbose_name_plural = 'оценки вопросов'
        constraints = [
            models.UniqueConstraint(fields=['question', 'user'], name='unique_question_vote'),
            models.CheckConstraint(condition=models.Q(value__in=VoteValue.values), name='valid_question_vote'),
        ]

    def __str__(self):
        return self.get_value_display()


class AnswerLike(models.Model):
    answer = models.ForeignKey(
        Answer, models.CASCADE, verbose_name='ответ', related_name='votes', db_index=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='пользователь',
        related_name='answer_votes',
    )
    value = models.SmallIntegerField('оценка', choices=VoteValue)

    class Meta:
        verbose_name = 'оценка ответа'
        verbose_name_plural = 'оценки ответов'
        constraints = [
            models.UniqueConstraint(fields=['answer', 'user'], name='unique_answer_vote'),
            models.CheckConstraint(condition=models.Q(value__in=VoteValue.values), name='valid_answer_vote'),
        ]

    def __str__(self):
        return self.get_value_display()
