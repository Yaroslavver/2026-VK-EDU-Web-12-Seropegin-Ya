from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from .models import Profile

User = get_user_model()


class BootstrapFields:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class AvatarField(forms.ImageField):
    help_text = 'JPG или PNG, до 2 МБ.'

    def __init__(self):
        super().__init__(
            label='Аватар', required=False, help_text=self.help_text,
            widget=forms.FileInput(attrs={'accept': 'image/png,image/jpeg'}),
        )

    def to_python(self, data):
        if data is not None and data.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Размер аватара должен быть не больше 2 МБ.')
        image = super().to_python(data)
        if image is not None:
            expected_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG'}
            if expected_format.get(Path(image.name).suffix.lower()) != image.image.format:
                raise forms.ValidationError('Загрузите изображение JPEG или PNG с подходящим расширением.')
        return image


class LoginForm(BootstrapFields, AuthenticationForm):
    username = forms.CharField(
        label='Логин', widget=forms.TextInput(attrs={'autocomplete': 'username', 'autofocus': True}),
    )


class SignupForm(BootstrapFields, UserCreationForm):
    email = forms.EmailField(label='Email', max_length=254)
    nickname = forms.CharField(label='Никнейм', max_length=40)
    avatar = AvatarField()
    field_order = ('username', 'email', 'nickname', 'password1', 'password2', 'avatar')

    class Meta(UserCreationForm.Meta):
        model = User
        labels = {'username': 'Логин'}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            with transaction.atomic():
                user.save()
                Profile.objects.create(
                    user=user,
                    nickname=self.cleaned_data['nickname'],
                    avatar=self.cleaned_data['avatar'] or '',
                )
        return user


class ProfileForm(BootstrapFields, forms.Form):
    email = forms.EmailField(label='Email', max_length=254)
    nickname = forms.CharField(label='Никнейм', max_length=40)
    avatar = AvatarField()

    def __init__(self, *args, user, **kwargs):
        self.user = user
        profile = getattr(user, 'profile', None)
        super().__init__(*args, initial={
            'email': user.email,
            'nickname': profile.nickname if profile and profile.nickname else user.get_username()[:40],
        }, **kwargs)

    @transaction.atomic
    def save(self):
        user = User.objects.select_for_update().get(pk=self.user.pk)
        user.email = self.cleaned_data['email']
        user.save(update_fields=['email'])

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.nickname = self.cleaned_data['nickname']
        fields = ['nickname']
        if avatar := self.cleaned_data['avatar']:
            profile.avatar = avatar
            fields.append('avatar')
        profile.save(update_fields=fields)
        return profile
