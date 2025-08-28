# tests/test_models.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from django.utils import timezone as django_timezone

from travels.models import TravelModes, TravelOptions, PassengerDetails, BookingTrip


class TravelModesModelTest(TestCase):
    """Test cases for TravelModes model"""
    
    def setUp(self):
        self.travel_mode = TravelModes.objects.create(
            travel_mode="Flight"
        )
    
    def test_travel_mode_creation(self):
        """Test that a travel mode is created properly"""
        self.assertEqual(self.travel_mode.travel_mode, "Flight")
        self.assertIsInstance(self.travel_mode, TravelModes)
    
    def test_travel_mode_str_method(self):
        """Test string representation of TravelModes"""
        self.assertEqual(str(self.travel_mode), "Flight")
    
    def test_travel_mode_max_length(self):
        """Test travel_mode field max length"""
        max_length = self.travel_mode._meta.get_field('travel_mode').max_length
        self.assertEqual(max_length, 100)
    
    def test_travel_mode_unique_entries(self):
        """Test that duplicate travel modes can be created (no unique constraint)"""
        duplicate_mode = TravelModes.objects.create(travel_mode="Flight")
        self.assertEqual(TravelModes.objects.filter(travel_mode="Flight").count(), 2)


class TravelOptionsModelTest(TestCase):
    """Test cases for TravelOptions model"""
    
    def setUp(self):
        self.travel_mode = TravelModes.objects.create(travel_mode="Bus")
        self.future_date = django_timezone.now() + timedelta(days=30)
        self.return_date = self.future_date + timedelta(days=3)
        
        self.travel_option = TravelOptions.objects.create(
            traveltype=self.travel_mode,
            source="Mumbai",
            destination="Delhi",
            travel_date=self.future_date,
            return_date=self.return_date,
            price=Decimal('5000.00'),
            number_of_persons=1,
            available_seats=40
        )
    
    def test_travel_option_creation(self):
        """Test that travel option is created properly"""
        self.assertEqual(self.travel_option.source, "Mumbai")
        self.assertEqual(self.travel_option.destination, "Delhi")
        self.assertEqual(self.travel_option.traveltype, self.travel_mode)
        self.assertEqual(self.travel_option.price, Decimal('5000.00'))
        self.assertEqual(self.travel_option.number_of_persons, 1)
        self.assertEqual(self.travel_option.available_seats, 40)
    
    def test_travel_option_str_method(self):
        """Test string representation"""
        expected = f"{self.travel_option.source} - {self.travel_option.destination} Travel"
        self.assertEqual(str(self.travel_option), expected)
    
    def test_duration_calculation_on_save(self):
        """Test that duration is calculated automatically on save"""
        self.assertIsNotNone(self.travel_option.duration)
        expected_duration = self.return_date - self.future_date
        self.assertEqual(self.travel_option.duration, expected_duration)
    
    def test_days_property(self):
        """Test days property calculation"""
        expected_days = (self.return_date - self.future_date).days
        self.assertEqual(self.travel_option.days, expected_days)
    
    def test_nights_property(self):
        """Test nights property calculation"""
        expected_nights = self.travel_option.days - 1
        self.assertEqual(self.travel_option.nights, expected_nights)
    
    def test_clean_method_valid_dates(self):
        """Test clean method with valid dates"""
        try:
            self.travel_option.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly with valid dates")
    
    def test_clean_method_invalid_dates(self):
        """Test clean method raises ValidationError for return date before travel date"""
        self.travel_option.return_date = self.future_date - timedelta(days=1)
        
        with self.assertRaises(ValidationError) as context:
            self.travel_option.clean()
        
        self.assertIn('return_date', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['return_date'][0],
            "Return must be after start."
        )
    
    def test_auto_timestamps(self):
        """Test that created_at and updated_at are set automatically"""
        self.assertIsNotNone(self.travel_option.created_at)
        self.assertIsNotNone(self.travel_option.updated_at)
    
    def test_ordering_meta(self):
        """Test that model has correct ordering"""
        meta = TravelOptions._meta
        self.assertEqual(meta.ordering, ['-travel_date'])
    
    def test_field_max_lengths(self):
        """Test field max lengths"""
        source_max_length = self.travel_option._meta.get_field('source').max_length
        destination_max_length = self.travel_option._meta.get_field('destination').max_length
        
        self.assertEqual(source_max_length, 100)
        self.assertEqual(destination_max_length, 100)
    
    def test_price_decimal_field(self):
        """Test price field decimal configuration"""
        price_field = self.travel_option._meta.get_field('price')
        self.assertEqual(price_field.max_digits, 10)
        self.assertEqual(price_field.decimal_places, 2)
    
    def test_duration_field_properties(self):
        """Test duration field properties"""
        duration_field = self.travel_option._meta.get_field('duration')
        self.assertFalse(duration_field.editable)
        self.assertTrue(duration_field.null)
    
    def test_model_validation_without_required_fields(self):
        """Test that model validation catches missing required fields"""
        travel_option = TravelOptions(
            traveltype=self.travel_mode,
            source="Test",
            destination="Test2",
            price=Decimal('1000.00'),
            available_seats=10
            # Missing required travel_date and return_date
        )
        
        # Test that full_clean() raises ValidationError for missing required fields
        with self.assertRaises(ValidationError):
            travel_option.full_clean()

class PassengerDetailsModelTest(TestCase):
    """Test cases for PassengerDetails model"""
    
    def setUp(self):
        self.passenger = PassengerDetails.objects.create(
            name="John Doe",
            age=30,
            adhar_number="123456789012",
            email="john@example.com",
            phone_number="9876543210"
        )
    
    def test_passenger_creation(self):
        """Test that passenger is created properly"""
        self.assertEqual(self.passenger.name, "John Doe")
        self.assertEqual(self.passenger.age, 30)
        self.assertEqual(self.passenger.adhar_number, "123456789012")
        self.assertEqual(self.passenger.email, "john@example.com")
        self.assertEqual(self.passenger.phone_number, "9876543210")
    
    def test_passenger_str_method(self):
        """Test string representation"""
        expected = f"{self.passenger.name} - {self.passenger.adhar_number}"
        self.assertEqual(str(self.passenger), expected)
    
    def test_field_max_lengths(self):
        """Test field max lengths"""
        name_max_length = self.passenger._meta.get_field('name').max_length
        adhar_max_length = self.passenger._meta.get_field('adhar_number').max_length
        phone_max_length = self.passenger._meta.get_field('phone_number').max_length
        
        self.assertEqual(name_max_length, 100)
        self.assertEqual(adhar_max_length, 12)
        self.assertEqual(phone_max_length, 15)
    
    def test_phone_number_optional(self):
        """Test that phone number is optional"""
        passenger = PassengerDetails.objects.create(
            name="Jane Doe",
            age=25,
            adhar_number="987654321098",
            email="jane@example.com"
        )
        self.assertIsNone(passenger.phone_number)
    
    def test_email_field_validation(self):
        """Test email field accepts valid email"""
        self.assertIsInstance(
            self.passenger._meta.get_field('email'), 
            type(PassengerDetails._meta.get_field('email'))
        )


class BookingTripModelTest(TestCase):
    """Test cases for BookingTrip model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.travel_mode = TravelModes.objects.create(travel_mode="Train")
        
        self.trip = TravelOptions.objects.create(
            traveltype=self.travel_mode,
            source="Chennai",
            destination="Bangalore",
            travel_date=django_timezone.now() + timedelta(days=15),
            return_date=django_timezone.now() + timedelta(days=16),
            price=Decimal('800.00'),
            available_seats=30
        )
        
        self.passenger = PassengerDetails.objects.create(
            name="Test Passenger",
            age=25,
            adhar_number="123456789012",
            email="passenger@test.com"
        )
        
    def test_booking_creation(self):
        """Test that booking is created properly"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=2,
            total_price=Decimal('1600.00'),
            booking_status='Confirmed',
            payment_status='success'
        )
        
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.trip, self.trip)
        self.assertEqual(booking.number_of_seats, 2)
        self.assertEqual(booking.total_price, Decimal('1600.00'))
        self.assertEqual(booking.booking_status, 'Confirmed')
        self.assertEqual(booking.payment_status, 'success')
    
    def test_booking_str_method(self):
        """Test string representation"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00')
        )
        
        expected = f"Booking by {self.user.username} for {self.trip}"
        self.assertEqual(str(booking), expected)
    
    def test_auto_booking_reference_generation(self):
        """Test that booking reference is auto-generated"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00')
        )
        
        self.assertIsNotNone(booking.booking_reference)
        self.assertEqual(len(booking.booking_reference), 10)
        self.assertTrue(booking.booking_reference.isupper())
    
    def test_unique_booking_references(self):
        """Test that booking references are unique"""
        booking1 = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00')
        )
        
        booking2 = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00')
        )
        
        self.assertNotEqual(booking1.booking_reference, booking2.booking_reference)
    
    def test_is_paid_method(self):
        """Test is_paid method"""
        # Test successful payment
        paid_booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00'),
            payment_status='success'
        )
        self.assertTrue(paid_booking.is_paid())
        
        # Test pending payment
        pending_booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00'),
            payment_status='pending'
        )
        self.assertFalse(pending_booking.is_paid())
        
        # Test failed payment
        failed_booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00'),
            payment_status='failed'
        )
        self.assertFalse(failed_booking.is_paid())
    
    def test_payment_status_choices(self):
        """Test payment status field choices"""
        payment_field = BookingTrip._meta.get_field('payment_status')
        choices = dict(payment_field.choices)
        
        expected_choices = {
            'pending': 'Pending',
            'success': 'Success',
            'failed': 'Failed'
        }
        
        self.assertEqual(choices, expected_choices)
    
    def test_default_values(self):
        """Test default field values"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00')
        )
        
        self.assertEqual(booking.booking_status, 'Confirmed')
        self.assertEqual(booking.payment_status, 'pending')
        self.assertEqual(booking.seat_numbers, [])
    
    def test_auto_timestamps(self):
        """Test that booked_at is set automatically"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00')
        )
        
        self.assertIsNotNone(booking.booked_at)
    
    def test_many_to_many_passengers(self):
        """Test ManyToMany relationship with passengers"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00')
        )
        
        booking.passengers.add(self.passenger)
        
        self.assertIn(self.passenger, booking.passengers.all())
        self.assertEqual(booking.passengers.count(), 1)
    
    def test_razorpay_fields(self):
        """Test Razorpay payment fields"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00'),
            razorpay_order_id='order_test123',
            razorpay_payment_id='pay_test123',
            razorpay_signature='signature_test123'
        )
        
        self.assertEqual(booking.razorpay_order_id, 'order_test123')
        self.assertEqual(booking.razorpay_payment_id, 'pay_test123')
        self.assertEqual(booking.razorpay_signature, 'signature_test123')
    
    def test_unique_razorpay_order_id(self):
        """Test that razorpay_order_id is unique"""
        BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=1,
            total_price=Decimal('800.00'),
            razorpay_order_id='order_unique123'
        )
        
        # Creating another booking with same razorpay_order_id should raise error
        with self.assertRaises(IntegrityError):
            BookingTrip.objects.create(
                user=self.user,
                trip=self.trip,
                number_of_seats=1,
                total_price=Decimal('800.00'),
                razorpay_order_id='order_unique123'
            )
    
    def test_model_indexes(self):
        """Test that model has correct indexes"""
        indexes = BookingTrip._meta.indexes
        index_fields = []
        
        for index in indexes:
            index_fields.extend(index.fields)
        
        # Check if important fields are indexed
        self.assertIn('user', index_fields)
        self.assertIn('trip', index_fields)
        self.assertIn('booking_status', index_fields)
    
    def test_seat_numbers_json_field(self):
        """Test seat_numbers JSONField"""
        booking = BookingTrip.objects.create(
            user=self.user,
            trip=self.trip,
            number_of_seats=2,
            total_price=Decimal('1600.00'),
            seat_numbers=['A1', 'A2']
        )
        
        self.assertEqual(booking.seat_numbers, ['A1', 'A2'])
        self.assertIsInstance(booking.seat_numbers, list)
    
    def test_decimal_field_precision(self):
        """Test total_price decimal field precision"""
        price_field = BookingTrip._meta.get_field('total_price')
        self.assertEqual(price_field.max_digits, 10)
        self.assertEqual(price_field.decimal_places, 2)


class ModelFieldValidationTest(TestCase):
    """Test field validations and constraints"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.travel_mode = TravelModes.objects.create(travel_mode="Flight")
        self.trip = TravelOptions.objects.create(
            traveltype=self.travel_mode,
            source="Test",
            destination="Test2",
            travel_date=django_timezone.now() + timedelta(days=5),
            return_date=django_timezone.now() + timedelta(days=7),
            price=Decimal('1000.00'),
            available_seats=10
        )
    
    def test_travel_options_required_fields(self):
        """Test that required fields cannot be None"""
        with self.assertRaises(IntegrityError):
            TravelOptions.objects.create(
                # Missing required fields should raise error
                source="Test"
                # Missing traveltype, destination, etc.
            )
    
    def test_booking_required_fields(self):
        """Test that booking required fields cannot be None"""
        with self.assertRaises(IntegrityError):
            BookingTrip.objects.create(
                user=self.user,
                # Missing trip and other required fields
                number_of_seats=1
            )
    
    def test_passenger_required_fields(self):
        """Test that passenger required fields cannot be None"""
        with self.assertRaises(IntegrityError):
            PassengerDetails.objects.create(
                name="Test",
                # Missing age, adhar_number, email
            )
