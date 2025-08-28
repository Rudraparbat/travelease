from django.contrib import admin
from .models import TravelModes , TravelOptions , PassengerDetails , BookingTrip
# Register your models here.

admin.site.register(TravelModes)
admin.site.register(TravelOptions)
admin.site.register(PassengerDetails)
admin.site.register(BookingTrip)
