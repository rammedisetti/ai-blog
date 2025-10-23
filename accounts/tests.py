from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class SignupTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_valid_signup(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "tester",
                "email": "tester@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(username="tester").exists())

    def test_duplicate_email(self):
        User.objects.create_user("u1", "tester@example.com", "pass12345")
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "tester2",
                "email": "tester@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        self.assertContains(response, "email already exists", status_code=200)

    def test_password_mismatch(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "tester3",
                "email": "tester3@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "StrongPass123",
                "password2": "WrongPass123",
            },
        )
        self.assertContains(response, "The two password fields didn", status_code=200)

    def test_weak_password(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "tester4",
                "email": "tester4@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password1": "short",
                "password2": "short",
            },
        )
        self.assertContains(response, "This password is too short", status_code=200)


class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            "loginuser",
            "login@example.com",
            "StrongPass123",
        )

    def test_login_with_username(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "loginuser", "password": "StrongPass123"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@example.com", "password": "StrongPass123"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_invalid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "bad", "password": "wrong"},
        )
        self.assertContains(response, "Please enter a correct", status_code=200)
