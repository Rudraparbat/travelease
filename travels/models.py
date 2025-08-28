from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.utils.crypto import get_random_string
# Create your models here.

# This Model Saves The Travel Modes e.g Flight , Train , Bus , Car etc , with Available Seats Info 
class TravelModes(models.Model):
    travel_mode = models.CharField(max_length=100)
    def __str__(self):
        return self.travel_mode
    

# Model for travel options
# Here The Auto Created Id is The Travel Id
class TravelOptions(models.Model):
    traveltype = models.ForeignKey(TravelModes, on_delete=models.CASCADE)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    travel_date = models.DateTimeField()
    return_date = models.DateTimeField()
    days = models.IntegerField()
    nights = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField(editable=False , default=None , null=True)
    number_of_persons = models.IntegerField(default=1)  
    available_seats = models.IntegerField(null = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def clean(self):
        super().clean()
        if self.travel_date and self.return_date:
            if self.return_date < self.travel_date:
                raise ValidationError({"return_date": "Return must be after start."})

    def save(self, *args, **kwargs):
        if self.travel_date and self.return_date:
            self.duration = self.return_date - self.travel_date
        else:
            self.duration = None
        super().save(*args, **kwargs)

    @property
    def days(self):
        return self.duration.days if self.duration else 0

    @property
    def nights(self):
        return self.days - 1
    
    class Meta:
        ordering = ['-travel_date']

    def __str__(self):
        return f"{self.source} - {self.destination} Travel"

# This Model Saves The Passenger Details While Booking A Trip
class PassengerDetails(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    adhar_number = models.CharField(max_length=12)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15 ,null= True , blank= True)

    def __str__(self):
        return f"{self.name} - {self.adhar_number}"


# Booking Model to Save User Bookings


class BookingTrip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(TravelOptions, on_delete=models.CASCADE)
    passengers = models.ManyToManyField(PassengerDetails)
    number_of_seats = models.IntegerField()
    seat_numbers = models.JSONField(default=list, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booked_at = models.DateTimeField(auto_now_add=True)
    booking_status = models.CharField(max_length=50, default='Confirmed')

    # Razorpay payment fields
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')],
        default='pending',
    )

    booking_reference = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return f"Booking by {self.user.username} for {self.trip}"

    def is_paid(self):
        return self.payment_status == 'success'

    def save(self, *args, **kwargs):
        # Auto-generate unique booking reference if not set
        if not self.booking_reference:
            self.booking_reference = get_random_string(10).upper()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['trip']),
            models.Index(fields=['booking_status']),
        ]
