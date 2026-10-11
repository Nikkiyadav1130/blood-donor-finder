from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Donor , BloodRequest
from datetime import timedelta
from django.utils import timezone


def create_donor(username, blood_group='O+', city='Moradabad', full_name='Test Donor'):
    """Helper that creates a User and a linked Donor profile."""
    user = User.objects.create_user(username=username, password='Test@12345')
    return Donor.objects.create(
        user=user,
        full_name=full_name,
        age=25,
        gender='M',
        blood_group=blood_group,
        phone='9876543210',
        city=city,
    )


class DonorModelTests(TestCase):
    def test_string_representation(self):
        donor = create_donor('donor1', blood_group='B+', full_name='Rahul Sharma')
        self.assertEqual(str(donor), 'Rahul Sharma (B+)')


class RegistrationTests(TestCase):
    def setUp(self):
        self.url = reverse('register')
        self.valid_data = {
            'username': 'newdonor',
            'password': 'Test@12345',
            'confirm_password': 'Test@12345',
            'full_name': 'Priya Singh',
            'age': 22,
            'gender': 'F',
            'blood_group': 'O+',
            'phone': '9123456780',
            'city': 'Bareilly',
            'last_donation_date': '',
            'consent_given': True,
        }

    def test_register_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_registration_creates_user_and_donor(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='newdonor').exists())
        self.assertTrue(Donor.objects.filter(full_name='Priya Singh').exists())

    def test_underage_donor_is_rejected(self):
        data = {**self.valid_data, 'age': 15}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('age', response.context['form'].errors)
        self.assertEqual(Donor.objects.count(), 0)

    def test_password_mismatch_is_rejected(self):
        data = {**self.valid_data, 'confirm_password': 'Different@123'}
        response = self.client.post(self.url, data)
        self.assertIn('confirm_password', response.context['form'].errors)
        self.assertEqual(Donor.objects.count(), 0)

    def test_duplicate_username_is_rejected(self):
        create_donor('newdonor')
        response = self.client.post(self.url, self.valid_data)
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(Donor.objects.count(), 1)

    def test_registration_requires_consent(self):
        data = {**self.valid_data}
        data.pop('consent_given')
        response = self.client.post(self.url, data)
        self.assertIn('consent_given', response.context['form'].errors)
        self.assertEqual(Donor.objects.count(), 0)


class AuthenticationTests(TestCase):
    def setUp(self):
        create_donor('loginuser')

    def test_login_with_correct_password(self):
        response = self.client.post(
            reverse('login'), {'username': 'loginuser', 'password': 'Test@12345'}
        )
        self.assertRedirects(response, reverse('home'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse('login'), {'username': 'loginuser', 'password': 'wrongpass'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout(self):
        self.client.login(username='loginuser', password='Test@12345')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)


class DonorListAndSearchTests(TestCase):
    def setUp(self):
        create_donor('d1', blood_group='A+', city='Delhi', full_name='Donor One')
        create_donor('d2', blood_group='O+', city='Delhi', full_name='Donor Two')
        create_donor('d3', blood_group='O+', city='Bareilly', full_name='Donor Three')
        self.url = reverse('donor_list')

    def test_list_shows_all_donors(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['donors']), 3)

    def test_filter_by_blood_group(self):
        response = self.client.get(self.url, {'blood_group': 'O+'})
        self.assertEqual(len(response.context['donors']), 2)

    def test_filter_by_city_is_case_insensitive(self):
        response = self.client.get(self.url, {'city': 'delhi'})
        self.assertEqual(len(response.context['donors']), 2)

    def test_filter_by_blood_group_and_city(self):
        response = self.client.get(self.url, {'blood_group': 'O+', 'city': 'Bareilly'})
        donors = response.context['donors']
        self.assertEqual(len(donors), 1)
        self.assertEqual(donors[0].full_name, 'Donor Three')

    def test_search_with_no_match_returns_empty(self):
        response = self.client.get(self.url, {'city': 'xyz'})
        self.assertEqual(len(response.context['donors']), 0)
        self.assertContains(response, 'No donors found matching your search.')


class DonorDetailTests(TestCase):
    def test_detail_page_shows_donor(self):
        donor = create_donor('detailuser', full_name='Amit Kumar')
        response = self.client.get(reverse('donor_detail', args=[donor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amit Kumar')

    def test_detail_page_returns_404_for_invalid_id(self):
        response = self.client.get(reverse('donor_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_phone_hidden_for_anonymous_user(self):
        donor = create_donor('privacyuser')
        response = self.client.get(reverse('donor_detail', args=[donor.pk]))
        self.assertNotContains(response, '9876543210')
        self.assertContains(response, 'Login to view phone number')

    def test_phone_visible_for_logged_in_user(self):
        donor = create_donor('privacyuser2')
        self.client.login(username='privacyuser2', password='Test@12345')
        response = self.client.get(reverse('donor_detail', args=[donor.pk]))
        self.assertContains(response, '9876543210')    


class StatisticsTests(TestCase):
    def test_statistics_page_loads_with_chart(self):
        create_donor('s1', blood_group='B+')
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_donors'], 1)
        self.assertTrue(len(response.context['chart']) > 0)

class AvailabilityTests(TestCase):
    def test_never_donated_is_available(self):
        donor = create_donor('a1')
        self.assertTrue(donor.is_available)

    def test_recent_donation_is_not_available(self):
        donor = create_donor('a2')
        donor.last_donation_date = timezone.localdate() - timedelta(days=30)
        donor.save()
        self.assertFalse(donor.is_available)

    def test_old_donation_is_available(self):
        donor = create_donor('a3')
        donor.last_donation_date = timezone.localdate() - timedelta(days=100)
        donor.save()
        self.assertTrue(donor.is_available)

    def test_exactly_90_days_is_available(self):
        donor = create_donor('a4')
        donor.last_donation_date = timezone.localdate() - timedelta(days=90)
        donor.save()
        self.assertTrue(donor.is_available)

    def test_available_only_filter_hides_recent_donors(self):
        create_donor('a5', full_name='Fresh Donor')
        recent = create_donor('a6', full_name='Recent Donor')
        recent.last_donation_date = timezone.localdate() - timedelta(days=10)
        recent.save()

        response = self.client.get(reverse('donor_list'), {'available': '1'})
        names = [d.full_name for d in response.context['donors']]
        self.assertIn('Fresh Donor', names)
        self.assertNotIn('Recent Donor', names)    


class BloodRequestTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='requester', password='Test@12345')
        self.other = User.objects.create_user(username='other', password='Test@12345')
        self.valid_data = {
            'patient_name': 'Ramesh Kumar',
            'blood_group': 'B+',
            'units_needed': 2,
            'hospital': 'City Hospital',
            'city': 'Moradabad',
            'contact_phone': '9000000001',
            'urgency': 'urgent',
            'note': '',
        }

    def _make_request(self, **overrides):
        data = {**self.valid_data, **overrides}
        data.pop('note', None)
        return BloodRequest.objects.create(requester=self.user, **data)

    def test_create_page_requires_login(self):
        response = self.client.get(reverse('request_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_logged_in_user_can_post_request(self):
        self.client.login(username='requester', password='Test@12345')
        response = self.client.post(reverse('request_create'), self.valid_data)
        self.assertRedirects(response, reverse('request_list'))
        self.assertEqual(BloodRequest.objects.count(), 1)
        self.assertEqual(BloodRequest.objects.first().requester, self.user)

    def test_invalid_units_rejected(self):
        self.client.login(username='requester', password='Test@12345')
        response = self.client.post(reverse('request_create'), {**self.valid_data, 'units_needed': 50})
        self.assertIn('units_needed', response.context['form'].errors)
        self.assertEqual(BloodRequest.objects.count(), 0)

    def test_list_hides_fulfilled_requests(self):
        self._make_request(patient_name='Open Patient')
        done = self._make_request(patient_name='Done Patient')
        done.is_fulfilled = True
        done.save()
        response = self.client.get(reverse('request_list'))
        names = [r.patient_name for r in response.context['blood_requests']]
        self.assertIn('Open Patient', names)
        self.assertNotIn('Done Patient', names)

    def test_list_filters_by_blood_group(self):
        self._make_request(patient_name='B Patient', blood_group='B+')
        self._make_request(patient_name='A Patient', blood_group='A+')
        response = self.client.get(reverse('request_list'), {'blood_group': 'A+'})
        self.assertEqual(len(response.context['blood_requests']), 1)

    def test_contact_hidden_for_anonymous_user(self):
        self._make_request()
        response = self.client.get(reverse('request_list'))
        self.assertNotContains(response, '9000000001')
        self.assertContains(response, 'Login to view contact number')

    def test_owner_can_mark_fulfilled(self):
        req = self._make_request()
        self.client.login(username='requester', password='Test@12345')
        self.client.post(reverse('request_fulfill', args=[req.pk]))
        req.refresh_from_db()
        self.assertTrue(req.is_fulfilled)

    def test_other_user_cannot_mark_fulfilled(self):
        req = self._make_request()
        self.client.login(username='other', password='Test@12345')
        response = self.client.post(reverse('request_fulfill', args=[req.pk]))
        self.assertEqual(response.status_code, 404)
        req.refresh_from_db()
        self.assertFalse(req.is_fulfilled)            
