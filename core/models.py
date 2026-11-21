from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models


def avatar_path(instance, filename):
    return f'avatars/{uuid4().hex}{Path(filename).suffix.lower()}'


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, models.CASCADE, verbose_name='пользователь',
        related_name='profile',
    )
    nickname = models.CharField('никнейм', max_length=40, blank=True)
    avatar = models.ImageField('аватар', upload_to=avatar_path, blank=True)
    rating = models.IntegerField('рейтинг', default=0)

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return self.nickname or self.user.get_username()
