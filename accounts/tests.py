from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class RegisterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("account_signup")

    def test_signup_page_200(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Inscription")

    def test_signup_success(self):
        r = self.client.post(self.url, {
            "email": "test@example.com",
            "username": "testuser",
            "password1": "MyStr0ng!Pass",
            "password2": "MyStr0ng!Pass",
        })
        self.assertRedirects(r, reverse("counter:dashboard"))
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_signup_password_mismatch(self):
        r = self.client.post(self.url, {
            "email": "test@example.com",
            "username": "testuser",
            "password1": "MyStr0ng!Pass",
            "password2": "different",
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_signup_duplicate_username(self):
        User.objects.create_user(username="testuser", password="pass12345")
        r = self.client.post(self.url, {
            "email": "other@example.com",
            "username": "testuser",
            "password1": "MyStr0ng!Pass",
            "password2": "MyStr0ng!Pass",
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "utilisateur avec ce nom existe")


class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("account_login")
        self.user = User.objects.create_user(
            username="testuser", password="MyStr0ng!Pass"
        )

    def test_login_page_200(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Connexion")

    def test_login_success(self):
        r = self.client.post(self.url, {
            "login": "testuser",
            "password": "MyStr0ng!Pass",
        })
        self.assertRedirects(r, reverse("counter:dashboard"))

    def test_login_wrong_password(self):
        r = self.client.post(self.url, {
            "login": "testuser",
            "password": "wrongpassword",
        })
        self.assertEqual(r.status_code, 200)
        # allauth shows non-field errors for bad credentials
        self.assertIn("form", r.context)
        self.assertTrue(r.context["form"].errors)

    def test_login_nonexistent_user(self):
        r = self.client.post(self.url, {
            "login": "nobody",
            "password": "somepass",
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)


class LogoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("account_logout")
        self.user = User.objects.create_user(username="testuser", password="pass12345")

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)  # shows confirmation page on GET

    def test_logout_success(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse("account_login"))


class AuthenticatedAccessTest(TestCase):
    def test_dashboard_redirects_anonymous(self):
        r = self.client.get(reverse("counter:dashboard"))
        self.assertRedirects(r, f"{reverse('account_login')}?next={reverse('counter:dashboard')}")

    def test_upload_redirects_anonymous(self):
        r = self.client.get(reverse("counter:upload"))
        self.assertRedirects(r, f"{reverse('account_login')}?next={reverse('counter:upload')}")

    def test_history_redirects_anonymous(self):
        r = self.client.get(reverse("counter:history"))
        self.assertRedirects(r, f"{reverse('account_login')}?next={reverse('counter:history')}")
