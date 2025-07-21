from django.test import Client, TestCase
from django.urls import reverse
from .models import ContactMessage


class ContactTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_contact_page(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)

    def test_submit_contact_form(self):
        data = {
            'name': 'Tester',
            'email': 'tester@example.com',
            'subject': 'Support',
            'message': 'Hello there',
            'agree': 'on',
        }
        response = self.client.post(reverse('contact'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(email='tester@example.com').exists())


class PrivacyTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_privacy_page(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Privacy Policy')


class TermsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_terms_page(self):
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)
