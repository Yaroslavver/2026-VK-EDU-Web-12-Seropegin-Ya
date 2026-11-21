from django import forms
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404

from core.forms import BootstrapFields

from .models import Answer, Question, Tag, VoteValue


class QuestionForm(BootstrapFields, forms.ModelForm):
    tags = forms.CharField(
        label='Теги', required=False, max_length=160,
        help_text='До трёх тегов через запятую, например python, django.',
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        widgets = {'text': forms.Textarea(attrs={'rows': 9})}

    def __init__(self, *args, author, **kwargs):
        self.author = author
        super().__init__(*args, **kwargs)

    def clean_tags(self):
        tags = dict.fromkeys(tag.strip().lower() for tag in self.cleaned_data['tags'].split(',') if tag.strip())
        if len(tags) > 3:
            raise forms.ValidationError('Можно указать не более трёх тегов.')
        name_field = Tag._meta.get_field('name')
        return [name_field.clean(tag, None) for tag in tags]

    @transaction.atomic
    def save(self, commit=True):
        self.instance.author = self.author
        return super().save(commit=commit)

    def _save_m2m(self):
        super()._save_m2m()
        # Одинаковый порядок захвата уникальных имён при параллельном создании вопросов.
        tags = [Tag.objects.get_or_create(name=name)[0] for name in sorted(self.cleaned_data['tags'])]
        self.instance.tags.set(tags)


class AnswerForm(BootstrapFields, forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text',)
        labels = {'text': 'Ваш ответ'}
        widgets = {'text': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Напишите ваш ответ…'})}

    def __init__(self, *args, question, author, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.question = question
        if author.is_authenticated:
            self.instance.author = author


class VoteForm(forms.Form):
    value = forms.TypedChoiceField(choices=[*VoteValue.choices, (0, 'Снять оценку')], coerce=int)

    def __init__(self, *args, model, target_id, user, **kwargs):
        self.model = model
        self.target_id = target_id
        self.user = user
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def save(self):
        target = get_object_or_404(self.model.objects.select_for_update(), pk=self.target_id)
        value = self.cleaned_data['value']
        if value:
            target.votes.update_or_create(user=self.user, defaults={'value': value})
        else:
            target.votes.filter(user=self.user).delete()

        rating = self.model.objects.with_rating().values_list('rating', flat=True).get(pk=target.pk)
        return {'rating': rating, 'vote': value}


class CorrectAnswerForm(forms.Form):
    answer_id = forms.IntegerField(min_value=1, max_value=2**63 - 1)
    accepted = forms.TypedChoiceField(choices=[('1', 'Отметить'), ('0', 'Снять отметку')], coerce=int)

    def __init__(self, *args, question_id, user, **kwargs):
        self.question_id = question_id
        self.user = user
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def save(self):
        question = get_object_or_404(Question.objects.select_for_update(), pk=self.question_id)
        if question.author_id != self.user.pk:
            raise PermissionDenied('Только автор вопроса может отметить правильный ответ.')

        answer = get_object_or_404(question.answers, pk=self.cleaned_data['answer_id'])
        correct = question.answers.filter(is_correct=True)
        if self.cleaned_data['accepted']:
            correct.exclude(pk=answer.pk).update(is_correct=False)
            question.answers.filter(pk=answer.pk, is_correct=False).update(is_correct=True)
        else:
            correct.filter(pk=answer.pk).update(is_correct=False)

        return {'correct_answer_id': correct.values_list('pk', flat=True).first()}
