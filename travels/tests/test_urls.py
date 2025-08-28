from django.test import SimpleTestCase
from django.urls import reverse, resolve
from travels import views

class UrlsTest(SimpleTestCase):
    """Test cases for all URL patterns in the travels app."""

    def test_home_url_resolves(self):
        """Test that the 'home' URL resolves to the main_page view."""
        url = reverse('home')
        self.assertEqual(resolve(url).func, views.main_page)

    def test_trip_detail_url_resolves(self):
        """Test that the 'details' URL with an ID resolves to the trip_detail view."""
        url = reverse('details', args=[1])  # Use a sample trip_id
        self.assertEqual(resolve(url).func, views.trip_detail)

    def test_booking_page_url_resolves(self):
        """Test that the 'bookingpage' URL resolves to the booking_page view."""
        url = reverse('bookingpage', args=[1])
        self.assertEqual(resolve(url).func, views.booking_page)

    def test_create_booking_url_resolves(self):
        """Test that the 'create_booking' URL resolves to the create_razorpay_order view."""
        url = reverse('create_booking')
        self.assertEqual(resolve(url).func, views.create_razorpay_order)

    def test_confirm_booking_url_resolves(self):
        """Test that the 'confirm_booking' URL resolves to the confirm_online_booking view."""
        url = reverse('confirm_booking', args=[1])
        self.assertEqual(resolve(url).func, views.confirm_online_booking)
        
    def test_confirm_offline_booking_url_resolves(self):
        """Test that the 'confirm_offline_booking' URL resolves to the correct view."""
        url = reverse('confirm_offline_booking', args=[1])
        self.assertEqual(resolve(url).func, views.confirm_offline_booking)

    def test_signup_url_resolves(self):
        """Test that the 'signup' URL resolves to the sign_up view."""
        url = reverse('signup')
        self.assertEqual(resolve(url).func, views.sign_up)

    def test_signin_url_resolves(self):
        """Test that the 'signin' URL resolves to the sign_in view."""
        url = reverse('signin')
        self.assertEqual(resolve(url).func, views.sign_in)

    def test_logout_url_resolves(self):
        """Test that the 'logout' URL resolves to the logout_user view."""
        url = reverse('logout')
        self.assertEqual(resolve(url).func, views.logout_user)

    def test_errorpage_url_resolves(self):
        """Test that the 'errorpage' URL resolves to the not_existed_page view."""
        url = reverse('errorpage')
        self.assertEqual(resolve(url).func, views.not_existed_page)

    def test_mybookings_url_resolves(self):
        """Test that the 'mybookings' URL resolves to the my_bookings view."""
        url = reverse('mybookings')
        self.assertEqual(resolve(url).func, views.my_bookings)

    def test_profile_url_resolves(self):
        """Test that the 'profile' URL resolves to the profile view."""
        url = reverse('profile')
        self.assertEqual(resolve(url).func, views.profile)

    def test_update_profile_url_resolves(self):
        """Test that the 'update_profile' URL resolves to the update_profile view."""
        url = reverse('update_profile')
        self.assertEqual(resolve(url).func, views.update_profile)

    def test_cancel_booking_url_resolves(self):
        """Test that the 'cancel_offline_booking' URL resolves to the correct view."""
        url = reverse('cancel_offline_booking', args=[1])
        self.assertEqual(resolve(url).func, views.cancel_offline_reservation)
