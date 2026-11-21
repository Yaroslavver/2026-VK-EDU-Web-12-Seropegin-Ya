from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

from .models import Profile

User = get_user_model()
PASSWORD = 'Oven-Horizon-Petal-975'


def png_upload(name='portrait.png'):
    image = BytesIO()
    Image.new('RGB', (4, 4)).save(image, format='PNG')
    return SimpleUploadedFile(name, image.getvalue(), content_type='image/png')


class AccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='member', email='member@example.org', password=PASSWORD)

    def setUp(self):
        self.media_root = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=self.media_root))

    def test_login_preserves_username_and_accepts_only_local_redirect(self):
        page = self.client.get('/login/', {'next': '/hot/?page=2'})
        self.assertContains(page, 'name="next" value="/hot/?page=2"')
        credentials = {'username': self.user.username, 'password': PASSWORD}
        invalid = self.client.post('/login/', {**credentials, 'password': 'bad', 'next': '/hot/?page=2'})
        self.assertTrue(invalid.context['form'].non_field_errors())
        self.assertEqual(invalid.context['form']['username'].value(), self.user.username)
        self.assertContains(invalid, 'name="next" value="/hot/?page=2"')

        result = self.client.post('/login/', {**credentials, 'next': '/hot/?page=2'})
        self.assertRedirects(result, '/hot/?page=2', fetch_redirect_response=False)
        result = self.client.post('/login/', {**credentials, 'next': '//elsewhere.example/'})
        self.assertRedirects(result, '/', fetch_redirect_response=False)

    def test_logout_requires_post_and_csrf_and_returns_to_the_page(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        client.get('/hot/?page=2')
        self.assertEqual(client.get('/logout/').status_code, 405)
        self.assertEqual(client.post('/logout/').status_code, 403)
        response = client.post('/logout/', {
            'next': '/hot/?page=2', 'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, '/hot/?page=2', fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', client.session)

    def test_signup_validates_password_then_creates_profile_and_starts_session(self):
        data = {'username': 'new_member', 'email': 'new@example.org', 'nickname': 'Новый участник'}
        response = self.client.post('/signup/', {**data, 'password1': '12345678', 'password2': '12345678'})
        self.assertIn('password2', response.context['form'].errors)
        self.assertEqual(response.context['form']['email'].value(), data['email'])
        self.assertFalse(User.objects.filter(username=data['username']).exists())

        response = self.client.post('/signup/', {**data, 'password1': PASSWORD, 'password2': PASSWORD})
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        user = User.objects.get(username=data['username'])
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.profile.nickname, data['nickname'])
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_profile_requires_login_and_saves_valid_avatar_and_updated_fields(self):
        self.assertRedirects(self.client.get('/profile/'), '/login/?next=/profile/', fetch_redirect_response=False)
        self.client.force_login(self.user)
        profile_page = self.client.get('/profile/')
        self.assertEqual(profile_page.context['form']['email'].value(), self.user.email)
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        self.assertContains(profile_page, 'core/img/avatar-me.svg')

        response = self.client.post('/profile/', {
            'email': 'updated@example.org', 'nickname': 'Новый ник', 'avatar': png_upload(),
        })
        self.assertRedirects(response, '/profile/', fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.org')
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.nickname, 'Новый ник')
        self.assertRegex(profile.avatar.name, r'^avatars/[0-9a-f]{32}\.png$')
        self.assertTrue((Path(self.media_root) / profile.avatar.name).is_file())
        self.assertContains(self.client.get('/profile/'), profile.avatar.url)

    def test_bad_avatar_keeps_posted_form_values_and_leaves_profile_unchanged(self):
        self.client.force_login(self.user)
        for upload in (
            png_upload('portrait.jpg'),
            SimpleUploadedFile('portrait.png', b'x' * (2 * 1024 * 1024 + 1)),
        ):
            with self.subTest(filename=upload.name):
                response = self.client.post('/profile/', {
                    'email': 'new@example.org', 'nickname': 'Ник', 'avatar': upload,
                })
                self.assertIn('avatar', response.context['form'].errors)
                self.assertEqual(response.context['form']['nickname'].value(), 'Ник')
                self.assertFalse(Profile.objects.filter(user=self.user).exists())
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'member@example.org')
