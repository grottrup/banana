from django.test import TestCase, Client
from django.core import mail
from users.models import User
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.utils.encoding import force_bytes,force_text,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
# Create your tests here.
class EmailTest(TestCase):
    def test_send_email(self):
        mail.send_mail('Subject here', 'Here is the message.',
            'from@example.com', ['to@example.com'],
            fail_silently=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Subject here')
        self.assertEqual(mail.outbox[0].body, 'Here is the message.')
        self.assertEqual(mail.outbox[0].from_email, 'from@example.com')
        self.assertEqual(mail.outbox[0].to, ['to@example.com'])


class LogInTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'bananamail131@gmail.com',
            'email': 'bananamail131@gmail.com',
            'password':'Bananainc123',
            'email_password': 'Bananainc123'}
            
        User.objects.create_user(**self.credentials)
    def test_login(self):
        # send login data
        response = self.client.post('/login/', self.credentials, follow=True)
        # should be logged in now
        self.assertTrue(response.context['user'].is_active)
        
class TestLogOut(TestCase):
    def test_log_out(self):
        self.client = Client()
        self.client.login(username='bananamail', password='secretpassword')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 200)

class SigninTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='12test12', email_password='12test12',
        email='test@example.com')
        self.user.save()

    def tearDown(self):
        self.user.delete()

    def test_wrong_username(self):
        user = authenticate(username='wrong',password='12test12',email_password='12test12' )
        self.assertFalse(user is not None and user.is_authenticated)

    def test_wrong_pssword(self):
        user = authenticate(username='test' ,password='wrong',email_password='12test12' )
        self.assertFalse(user is not None and user.is_authenticated)

    def test_wrong_email_password(self):
        user = authenticate(username='test',password='12test12',email_password='wrong' )
        self.assertFalse(user is not None and user.is_authenticated)

class SignUpPageTests(TestCase):
    def setUp(self):
        self.register_url=reverse('signup')
        self.login_url=reverse('login')
        self.user={
            'first_name': 'first_name',
            'last_name': 'last_name',
            'username': 'testuser',
            'email': 'testuser@email.com',
            'email_password': 'email_password',
            'password1': 'password1',
            'password2': 'password2'
        }
        self.user_short_password={
            'email':'testemail@gmail.com',
            'username':'username',
            'password':'tes',
            'password2':'tes',
            'name':'fullname'
        }
        self.user_unmatching_password={

            'email':'testemail@gmail.com',
            'username':'username',
            'password':'teslatt',
            'password2':'teslatto',
            'name':'fullname'
        }

        self.user_invalid_email={
            
            'email':'test.com',
            'username':'username',
            'password':'teslatt',
            'password2':'teslatto',
            'name':'fullname'
        }
        return super().setUp()

class SignupTest(SignUpPageTests):
    def test_can_view_page_correctly(self):
        response=self.client.get(self.register_url)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response,'users/signup.html')

    def test_can_register_user(self):
            response=self.client.post(self.register_url,self.user,format='text/html')
            self.assertEqual(response.status_code,200)

    def test_cant_register_user_withshortpassword(self):
            response=self.client.post(self.register_url,self.user_short_password,format='text/html')
            self.assertEqual(response.status_code,200)

    def test_cant_register_user_with_unmatching_passwords(self):
            response=self.client.post(self.register_url,self.user_unmatching_password,format='text/html')
            self.assertEqual(response.status_code,200)
    def test_cant_register_user_with_invalid_email(self):
            response=self.client.post(self.register_url,self.user_invalid_email,format='text/html')
            self.assertEqual(response.status_code,200)

    def test_cant_register_user_with_taken_email(self):
            self.client.post(self.register_url,self.user,format='text/html')
            response=self.client.post(self.register_url,self.user,format='text/html')
            self.assertEqual(response.status_code,200)