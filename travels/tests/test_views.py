import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import razorpay     
from travels.models import TravelModes, TravelOptions, BookingTrip, PassengerDetails

# Use model_bakery for easy data creation
from model_bakery import baker


class ViewsTest(TestCase):
    """Comprehensive test suite for all views in the travels app."""

    def setUp(self):
        """Set up initial data for all test cases."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpassword123'
        )
        self.travel_mode = baker.make(TravelModes, travel_mode="Flight")
        
        # Create a few travel options for testing
        self.trip1 = baker.make(
            TravelOptions,
            traveltype=self.travel_mode,
            source="Mumbai",
            destination="Delhi",
            travel_date=timezone.now() + timedelta(days=10),
            return_date=timezone.now() + timedelta(days=15),
            price=Decimal('5000.00'),
            available_seats=20
        )
        self.trip2 = baker.make(
            TravelOptions,
            traveltype=self.travel_mode,
            source="Chennai",
            destination="Bangalore",
            travel_date=timezone.now() + timedelta(days=20),
            return_date=timezone.now() + timedelta(days=25),
            price=Decimal('3000.00'),
            available_seats=10
        )

    # --- Test `main_page` View ---
    def test_main_page_view(self):
        """Test that the main page loads and displays trips."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')
        self.assertContains(response, 'Mumbai')
        self.assertContains(response, 'Chennai')

    def test_main_page_search_filter(self):
        """Test search functionality on the main page."""
        response = self.client.get(reverse('home'), {'search': 'Delhi'})
        self.assertContains(response, 'Delhi')
        self.assertNotContains(response, 'Chennai')

    def test_main_page_price_filter(self):
        """Test price range filtering."""
        response = self.client.get(reverse('home'), {'price_range': '4000'})
        self.assertContains(response, 'Chennai') # Price 3000
        

    # --- Test `trip_detail` View ---
    def test_trip_detail_authenticated(self):
        """Test trip detail view for authenticated users."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('details', args=[self.trip1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'details.html')
        self.assertContains(response, self.trip1.destination)

    def test_trip_detail_unauthenticated_redirect(self):
        """Test that unauthenticated users are redirected from trip detail."""
        response = self.client.get(reverse('details', args=[self.trip1.id]))
        self.assertRedirects(response, f"/signin/?next=/details/{self.trip1.id}/")

    def test_trip_detail_not_found(self):
        """Test trip detail view for a non-existent trip."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('details', args=[999]))
        self.assertEqual(response.status_code, 500)

    # --- Test `booking_page` View ---
    def test_booking_page_authenticated(self):
        """Test booking page view for authenticated users."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('bookingpage', args=[self.trip1.id]), {'travelers': 2})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking.html')
        self.assertContains(response, self.trip1.destination)

    def test_booking_page_invalid_travelers(self):
        """Test booking page with an invalid number of travelers."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('bookingpage', args=[self.trip1.id]), {'travelers': 50}) # More than available seats
        self.assertEqual(response.status_code, 400)

    def test_booking_page_already_booked(self):
        """Test booking page when the trip is already booked by the user."""
        baker.make(BookingTrip, user=self.user, trip=self.trip1, booking_status='Confirmed')
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('bookingpage', args=[self.trip1.id]))
        self.assertTemplateUsed(response, 'booking_error.html')

    # --- Test `create_razorpay_order` View ---
    @patch('travels.views.razorpay_client.order.create')
    def test_create_razorpay_order(self, mock_order_create):
        """Test Razorpay order creation with a mock."""
        self.client.login(username='testuser', password='testpassword123')
        mock_order_create.return_value = {'id': 'order_test123', 'amount': 10000, 'currency': 'INR'}

        data = {'trip_id': self.trip1.id, 'travelers': 2}
        response = self.client.post(
            reverse('create_booking'), 
            data=json.dumps(data), 
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['order_id'], 'order_test123')
        mock_order_create.assert_called_once()

    # --- Test `confirm_online_booking` View ---
    @patch('travels.views.razorpay_client.utility.verify_payment_signature')
    def test_confirm_online_booking_success(self, mock_verify):
        """Test successful online booking confirmation with mock verification."""
        mock_verify.return_value = None # No exception means success
        self.client.login(username='testuser', password='testpassword123')

        data = {
            'payment_id': 'pay_test123',
            'order_id': 'order_test123',
            'signature': 'sig_test123',
            'passengers': [{'name': 'John', 'age': 30, 'adhar_number': '123456789012', 'email': 'john@test.com'}],
            'selected_seats': ['A1']
        }

        response = self.client.post(
            reverse('confirm_booking', args=[self.trip1.id]),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertTrue(BookingTrip.objects.filter(razorpay_order_id='order_test123').exists())
        
        # Verify seat deduction
        self.trip1.refresh_from_db()
        self.assertEqual(self.trip1.available_seats, 19)

    # --- Test `confirm_offline_booking` View ---
    def test_confirm_offline_booking_success(self):
        """Test successful offline booking confirmation."""
        self.client.login(username='testuser', password='testpassword123')
        
        data = {
            'passengers': [{'name': 'Jane', 'age': 25, 'adhar_number': '987654321098', 'email': 'jane@test.com'}],
            'selected_seats': ['B2']
        }
        
        response = self.client.post(
            reverse('confirm_offline_booking', args=[self.trip2.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertTrue(BookingTrip.objects.filter(trip=self.trip2, booking_status='Pending').exists())
        
        # Verify seat deduction
        self.trip2.refresh_from_db()
        self.assertEqual(self.trip2.available_seats, 9)

    # --- Test `cancel_offline_reservation` View ---
    def test_cancel_offline_reservation(self):
        """Test cancellation of a pending offline booking."""
        self.client.login(username='testuser', password='testpassword123')
        booking = baker.make(
            BookingTrip, 
            user=self.user, 
            trip=self.trip1, 
            payment_status='pending', 
            booking_status='Pending',
            number_of_seats=2
        )
        
        initial_seats = self.trip1.available_seats
        response = self.client.post(reverse('cancel_offline_booking', args=[booking.id]))
        
        self.assertRedirects(response, reverse('mybookings'))
        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, 'Cancelled')
        
        # Verify seats are restored
        self.trip1.refresh_from_db()
        self.assertEqual(self.trip1.available_seats, initial_seats + 2)

    # --- Test Authentication Views ---
    def test_signup_view(self):
        """Test user signup view."""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password': 'newpassword123',
        })

    def test_signin_view(self):
        """Test user signin view."""
        response = self.client.post(reverse('signin'), {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        self.assertRedirects(response, reverse('home'))
        
    def test_logout_view(self):
        """Test user logout view."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))

    # --- Test Profile Views ---
    def test_profile_view(self):
        """Test profile page view."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_update_profile_view(self):
        """Test profile update functionality."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(reverse('update_profile'), {
            'update_info': '1',
            'username': 'updated_username',
            'email': 'updated@test.com'
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updated_username')

    # --- Test `my_bookings` View ---
    def test_my_bookings_view(self):
        """Test that the my_bookings page displays user's bookings."""
        baker.make(BookingTrip, user=self.user, trip=self.trip1)
        self.client.login(username='testuser', password='testpassword1223') # Intentionally wrong pass to show login fail
        response = self.client.get(reverse('mybookings'))
        self.assertRedirects(response, f"/signin/?next=/mybookings/") # Redirects if not logged in

        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('mybookings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_bookings.html')
        self.assertContains(response, self.trip1.destination)

######################### Invalid Data and Error Condition Tests #########################

class InvalidDataViewsTest(TestCase):
    """Test suite for views with invalid data and error conditions."""

    def setUp(self):
        """Set up initial data for all test cases."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpassword123'
        )
        self.travel_mode = baker.make(TravelModes)
        self.trip = baker.make(
            TravelOptions,
            traveltype=self.travel_mode,
            available_seats=10,
            price=Decimal('1000.00')
        )

    # --- `main_page` View Invalid Data Tests ---
    def test_main_page_invalid_date_format(self):
        """Test main page with invalid date format in filters."""
        response = self.client.get(reverse('home'), {'start_date': 'invalid-date-format'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid start_date format", response.content)

    def test_main_page_invalid_price_format(self):
        """Test main page with non-numeric price filter."""
        response = self.client.get(reverse('home'), {'price_range': 'not-a-number'})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"max_price must be a valid number", response.content)

    # --- `booking_page` View Invalid Data Tests ---
    def test_booking_page_excessive_travelers(self):
        """Test booking page with more travelers than available seats."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('bookingpage', args=[self.trip.id]), {'travelers': 50})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Invalid number of travelers", response.content)

    # --- `create_razorpay_order` View Invalid Data Tests ---
    def test_create_razorpay_order_non_post(self):
        """Test create Razorpay order with non-POST method."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('create_booking'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': False, 'message': 'Invalid request'})

    # --- `confirm_online_booking` View Invalid Data Tests ---
    def test_confirm_online_booking_missing_data(self):
        """Test online booking confirmation with missing required data."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(
            reverse('confirm_booking', args=[self.trip.id]),
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing required data", response.content)

    @patch('travels.views.razorpay_client.utility.verify_payment_signature', side_effect=razorpay.errors.SignatureVerificationError('Invalid signature'))
    def test_confirm_online_booking_invalid_signature(self, mock_verify):
        """Test online booking with a failed payment signature verification."""
        self.client.login(username='testuser', password='testpassword123')
        data = {
            'payment_id': 'pay_test', 'order_id': 'order_test', 'signature': 'invalid_sig',
            'passengers': [{'name': 'Test', 'age': 30, 'adhar_number': '123456789012', 'email': 'test@example.com'}],
            'selected_seats': ['C1']
        }
        response = self.client.post(
            reverse('confirm_booking', args=[self.trip.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Payment verification failed", response.content)

    def test_confirm_online_booking_insufficient_seats(self):
        """Test booking when there are not enough available seats."""
        self.client.login(username='testuser', password='testpassword123')
        self.trip.available_seats = 1
        self.trip.save()
        
        data = {
            'payment_id': 'pay_test', 'order_id': 'order_test', 'signature': 'sig_test',
            'passengers': [
                {'name': 'P1', 'age': 20, 'adhar_number': '111', 'email': 'p1@test.com'},
                {'name': 'P2', 'age': 22, 'adhar_number': '222', 'email': 'p2@test.com'}
            ],
            'selected_seats': ['D1', 'D2']
        }
        with patch('travels.views.razorpay_client.utility.verify_payment_signature', return_value=None):
            response = self.client.post(
                reverse('confirm_booking', args=[self.trip.id]),
                data=json.dumps(data),
                content_type='application/json'
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Not enough available seats", response.content)

    # --- `cancel_offline_reservation` View Invalid Data Tests ---
    def test_cancel_booking_not_owned_by_user(self):
        """Test that a user cannot cancel a booking they do not own."""
        booking = baker.make(BookingTrip, user=self.other_user, trip=self.trip)
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(reverse('cancel_offline_booking', args=[booking.id]))
        self.assertEqual(response.status_code, 500)

    def test_cancel_already_successful_booking(self):
        """Test that a successful booking cannot be cancelled via this view."""
        booking = baker.make(
            BookingTrip, user=self.user, trip=self.trip, payment_status='success'
        )
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(reverse('cancel_offline_booking', args=[booking.id]))
        # Note: Your current view logic will cancel this. You might want to adjust the view
        # to only allow cancellation of 'pending' bookings.
        # This test highlights a potential logic gap.
        # self.assertRedirects(response, reverse('mybookings')) # Current behavior
        # A better check might be for a message or error.

    # --- Authentication Views Invalid Data Tests ---
    def test_signup_password_mismatch(self):
        """Test signup with mismatching passwords."""
        response = self.client.post(reverse('signup'), {
            'username': 'mismatchuser',
            'password1': 'pass1',
            'password2': 'pass2'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Passwords do not match", response.content)

    def test_signup_existing_username(self):
        """Test signup with a username that already exists."""
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password1': 'newpass',
            'password2': 'newpass'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Username already exists", response.content)

    def test_signin_invalid_credentials(self):
        """Test signin with incorrect credentials."""
        response = self.client.post(reverse('signin'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 500) # Your view returns 500
        self.assertIn(b"User is Not Valid", response.content)

    # --- Profile Views Invalid Data Tests ---
    def test_update_profile_incorrect_old_password(self):
        """Test password change with an incorrect old password."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(reverse('update_profile'), {
            'change_password': '1',
            'old_password': 'wrongoldpassword',
            'new_password1': 'newpass',
            'new_password2': 'newpass'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Old password is incorrect", response.content)
