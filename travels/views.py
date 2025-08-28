
from datetime import date
import json
import os
from pyexpat.errors import messages
from django.core.paginator import Paginator
import razorpay
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate , logout
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseServerError, HttpResponseBadRequest, JsonResponse
from django.db import DatabaseError , transaction
from django.core.exceptions import ValidationError
from django.db import models
from travels.models import BookingTrip, PassengerDetails, TravelModes, TravelOptions
from django.utils.dateparse import parse_date
from django.db.models import Sum, Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from dotenv import load_dotenv
load_dotenv()

razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_SECRET_ID")))

# This is the main page view with all filters , searching 
def main_page(request):
    try:
        search = request.GET.get('search', '').strip()
        travel_mode_id = request.GET.get('travel_mode', None)
        start_date_str = request.GET.get('start_date', None)
        end_date_str = request.GET.get('end_date', None)
        min_price = request.GET.get('min_price', 100)
        max_price = request.GET.get('price_range', None)

        travel_options = TravelOptions.objects.all()

        # Filter by search term over destination or source using icontains for partial match
        if search:
            travel_options = travel_options.filter(
                Q(destination__icontains=search) 
            )

        # Filter by travel_mode foreign key if  valid
        if travel_mode_id and travel_mode_id.isdigit():
            travel_options = travel_options.filter(traveltype=int(travel_mode_id))

        # Filter by date range if provided
        if start_date_str:
            print("startd")
            start_date = parse_date(start_date_str)
            if not start_date:
                return HttpResponseBadRequest("Invalid start_date format. Use YYYY-MM-DD.")
            travel_options = travel_options.filter(travel_date__gte=start_date)

        if end_date_str:
            end_date = parse_date(end_date_str)
            if not end_date:
                return HttpResponseBadRequest("Invalid end_date format. Use YYYY-MM-DD.")
            travel_options = travel_options.filter(return_date__lte=end_date)

        # Filter by price range if provided
        if min_price:
            try:
                min_price_val = float(min_price)
                travel_options = travel_options.filter(price__gte=min_price_val)
            except ValueError:
                return HttpResponseBadRequest("min_price must be a valid number")

        if max_price:
            try:
                max_price_val = float(max_price)
                travel_options = travel_options.filter(price__lte=max_price_val)
            except ValueError:
                return HttpResponseBadRequest("max_price must be a valid number")

        # travel modes list
        travel_modes = TravelModes.objects.all()

        return render(request, 'main.html', {
            'travel_options': travel_options,
            'travel_modes': travel_modes,
        })

    except ValidationError as ve:
        # validation errors
        return HttpResponseServerError(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        # Handle database-specific errors like connection issues or query failures
        return HttpResponseServerError(f"A database error occurred : {db_err}")

    except Exception as e:
        # Catch-all for unexpected errors
        return HttpResponseServerError(f"error occurred : {e}")


# Travel Option Details View 
@login_required(login_url='signin')  
def trip_detail(request, trip_id):
    try:
        # Get the specific trip
        trip = get_object_or_404(TravelOptions, id=trip_id)
    
        # Get related travel modes for context
        travel_modes = TravelModes.objects.all()
        
        return render(request, 'details.html', {
            'trip': trip,
            'travel_modes': travel_modes
        })
        
    except ValidationError as ve:
        return HttpResponseServerError(f"Invalid data encountered: {ve}")
        
    except DatabaseError as db_err:
        return HttpResponseServerError(f"A database error occurred: {db_err}")
        
    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {e}")
    
# Trip Booking Pgae View
@login_required(login_url='signin')  
def booking_page(request, trip_id):
    try:
        trip = get_object_or_404(TravelOptions, id=trip_id)
        travelers = int(request.GET.get('travelers', 1))
        
        # Check if that trip is already booked by that user or not 
        booked_trip = BookingTrip.objects.filter(user=request.user, trip=trip , booking_status__in=['Confirmed', 'Pending'])
        if booked_trip.exists():
            return render(request, "booking_error.html")
        
        # Validate travelers count
        if travelers <= 0 or travelers > trip.available_seats:
            return HttpResponseBadRequest("Invalid number of travelers")
        
        # Calculate total price
        total_price = trip.price * travelers
        
        # Generate seat layout (for demo - 40 seats, 10 rows x 4 seats)
        total_seats = 40
        booked_seats = [5, 12, 23, 31, 37]  # Demo booked seats
        
        return render(request, 'booking.html', {
            'trip': trip,
            'travelers': travelers,
            'total_price': total_price,
            'total_seats': total_seats,
            'booked_seats': booked_seats,
        })
    except ValidationError as ve:
        return HttpResponseBadRequest(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        return HttpResponseServerError("A database error occurred. Please try again later.")
 
    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {e}")
    

@login_required(login_url='signin')
@csrf_exempt
def create_razorpay_order(request):
    """Create Razorpay order before payment"""
    
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            trip_id = data.get('trip_id')
            travelers = data.get('travelers', 1)
            
            trip = get_object_or_404(TravelOptions, id=trip_id)
            total_amount = trip.price * travelers
            
            # Create Razorpay order
            razorpay_order = razorpay_client.order.create({
                'amount': int(total_amount) * 100,  # Amount in paise
                'currency': 'INR',
                'payment_capture': 1  # Auto capture
            })
            
            return JsonResponse({
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': int(total_amount) * 100 ,
                'currency': 'INR',
                'key_id': os.getenv('RAZORPAY_KEY_ID')
            })
        
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    
    

@login_required(login_url='signin')
@csrf_exempt
def confirm_online_booking(request, trip_id): 
    
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
    
    try:
        data = json.loads(request.body)

        razorpay_payment_id = data.get('payment_id')
        razorpay_order_id = data.get('order_id')
        razorpay_signature = data.get('signature')
        passengers_data = data.get('passengers')
        selected_seats = data.get('selected_seats')

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature, passengers_data, selected_seats]):
            return HttpResponseBadRequest("Missing required data")

        # Verify payment signature to ensure payment is authentic
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            return HttpResponseBadRequest("Payment verification failed: Invalid signature")

        trip = get_object_or_404(TravelOptions, id=trip_id)

        number_of_travelers = len(passengers_data)
        total_price = trip.price * number_of_travelers

        # Validate sufficient seats
        if trip.available_seats < number_of_travelers:
            return HttpResponseBadRequest("Not enough available seats")

        with transaction.atomic():
            # Create passenger records
            passenger_objs = []
            for p in passengers_data:
                # Validate each passenger entry here or via forms if preferred
                if PassengerDetails.objects.filter(adhar_number=p['adhar_number']).exists():
                    return HttpResponseBadRequest(f"Duplicate Adhar number: {p['adhar_number']}")

                passenger = PassengerDetails.objects.create(
                    name=p['name'],
                    age=p['age'],
                    adhar_number=p['adhar_number'],
                    email=p['email'],
                    phone_number=p.get('phone_number', '')
                )
                passenger_objs.append(passenger)

            # Create booking record
            booking = BookingTrip.objects.create(
                user=request.user,
                trip=trip,
                number_of_seats=number_of_travelers,
                seat_numbers=selected_seats,
                total_price=total_price,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature,
                booking_status='Confirmed',
            )
            booking.passengers.set(passenger_objs)

            # Deduct seats
            trip.available_seats -= number_of_travelers
            trip.save()

        return JsonResponse({'success': True, 'message': 'Booking confirmed', 'booking_id': booking.id})

    except ValidationError as ve:
        return HttpResponseBadRequest(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        return HttpResponseServerError(f"A database error occurred : {db_err}")

    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {e}")
    
@login_required(login_url='signin')
@csrf_exempt
def confirm_offline_booking(request , trip_id) :

    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
    
    try:
        data = json.loads(request.body)
        passengers_data = data.get('passengers')
        selected_seats = data.get('selected_seats')

        if not all([passengers_data, selected_seats]):
            return HttpResponseBadRequest("Missing required data")

        trip = get_object_or_404(TravelOptions, id=trip_id)

        number_of_travelers = len(passengers_data)
        total_price = trip.price * number_of_travelers

        print("Number of travelers:", number_of_travelers)
        print("Available seats:", trip.available_seats)
        print(passengers_data)
        print(selected_seats)

        # Validate sufficient seats
        if trip.available_seats < number_of_travelers:
            return HttpResponseBadRequest("Not enough available seats")

        with transaction.atomic():
            # Create passenger records
            passenger_objs = []
            for p in passengers_data:
                # Validate each passenger entry here or via forms if preferred
                passenger = PassengerDetails.objects.create(
                    name=p['name'],
                    age=p['age'],
                    adhar_number=p['adhar_number'],
                    email=p['email'],
                    phone_number=p.get('phone_number', '')
                )
                passenger_objs.append(passenger)
            # Create booking    record
            booking = BookingTrip.objects.create(
                user=request.user,
                trip=trip,
                number_of_seats=number_of_travelers,
                seat_numbers = selected_seats,
                total_price=total_price,
                booking_status='Pending',
            )
            booking.passengers.set(passenger_objs)

            # Deduct seats
            trip.available_seats -= number_of_travelers
            trip.save()



        return JsonResponse({'success': True, 'message': 'Booking recorded. Please complete payment at the counter.', 'booking_id': booking.id})

    except ValidationError as ve:
        return HttpResponseBadRequest(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        return HttpResponseServerError("A database error occurred. Please try again later.")

    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {e}")
    
# Cancel Offline Reservation
@login_required(login_url='signin')
@csrf_exempt
def cancel_offline_reservation(request, booking_id):
    """
    Cancel an offline booking and restore the reserved seats to the trip.
    Only pending/offline bookings can be cancelled.
    """
    try :
        booking = get_object_or_404(BookingTrip, id=booking_id, user=request.user)

        # Only allow cancellation if status is pending and payment_method is offline
        if booking.payment_status != 'pending' and  booking.payment_status != 'success':
            return redirect('mybookings')

        # Restore seats
        trip = booking.trip
        if booking.number_of_seats and trip:
            trip.available_seats += booking.number_of_seats
            trip.save()

        # Update booking status
        booking.booking_status = 'Cancelled'
        booking.save(update_fields=["booking_status"])

        return redirect('mybookings')
    
    except ValidationError as ve:
        return HttpResponseBadRequest(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        return HttpResponseServerError("A database error occurred. Please try again later.")

    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {e}")

# This View For User SIgn up 
def sign_up(request):
    try :
        if request.method == "POST":
            username = request.POST.get('username', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')

            # Basic validations
            if not username or not password1 or not password2:
                return HttpResponseBadRequest("Username and password fields are required.")

            if password1 != password2:
                return HttpResponseBadRequest("Passwords do not match.")

            if User.objects.filter(username=username).exists():
                return HttpResponseBadRequest("Username already exists.")

                # Create the user
            user = User.objects.create_user(username=username, password=password1)
            user.full_clean()  # Run model validation if any

                # Authenticate and log in the user immediately
            user = authenticate(request, username=username, password=password1)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to home page (adjust URL name as needed)
            else:
                return HttpResponseServerError("Authentication failed after signup.")
            
        return render(request, 'signup.html')

    except ValidationError as ve:
        return HttpResponseBadRequest(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        return HttpResponseServerError("A database error occurred. Please try again later.")

    except Exception as e:
        return HttpResponseServerError("An unexpected error occurred. Please try again later.")

    

# This View For User SIgn in
def sign_in(request) :
    try :
        if request.method == "POST":
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')

            # Basic validations
            if not username or not password :
                return HttpResponseBadRequest("Username and password fields are required.")

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to home page (adjust URL name as needed)
            else:
                return HttpResponseServerError("User is Not Valid , Please Check Your Credentials")
            
        return render(request, 'signin.html')
    except ValidationError as ve:
        # validation errors
        return HttpResponseServerError(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        # Handle database-specific errors like connection issues or query failures
        return HttpResponseServerError(f"A database error occurred : {db_err}")

    except Exception as e:
        # Catch-all for unexpected errors
        return HttpResponseServerError(f"error occurred : {e}")
    
# This View For User Logout
def logout_user(request) :
    try :
        logout(request)
        return redirect('home')

    except ValidationError as ve:
        # validation errors
        return HttpResponseServerError(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        # Handle database-specific errors like connection issues or query failures
        return HttpResponseServerError(f"A database error occurred : {db_err}")

    except Exception as e:
        # Catch-all for unexpected errors
        return HttpResponseServerError(f"error occurred : {e}")
    

# This View For Not existed Urls or under construction pages
def not_existed_page(request, exception = None):
    return render(request, '404.html', status=404)

# My Profile View
@login_required(login_url='signin')
def profile(request):

    try :

    # Get user statistics
        total_bookings = BookingTrip.objects.filter(user=request.user).count()
        destinations_visited = BookingTrip.objects.filter(
            user=request.user, 
            payment_status='success'
        ).values('trip__destination').distinct().count()
        
        context = {
            'total_bookings': total_bookings,
            'destinations_visited': destinations_visited,
        }
        
        return render(request, 'profile.html', context)
    
    except ValidationError as ve:
        # validation errors
        return HttpResponseServerError(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        # Handle database-specific errors like connection issues or query failures
        return HttpResponseServerError(f"A database error occurred : {db_err}")

    except Exception as e:
        # Catch-all for unexpected errors
        return HttpResponseServerError(f"error occurred : {e}")
    


@login_required(login_url='signin')
def update_profile(request):
    try  :
        if request.method == 'POST':
            user = request.user
            
            # Handle profile info update
            if 'update_info' in request.POST:
                user.username = request.POST.get('username', user.username)
                user.email = request.POST.get('email', user.email)
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                
                try:
                    user.save()
                    return redirect('profile')
                except Exception as e:
                    return HttpResponseBadRequest(f"Error updating profile: {e}")
            
            # Handle password change
            elif 'change_password' in request.POST:
                old_password = request.POST.get('old_password')
                new_password1 = request.POST.get('new_password1')
                new_password2 = request.POST.get('new_password2')
                
                if old_password and new_password1 and new_password2:
                    if not user.check_password(old_password):
                        return HttpResponseBadRequest('Old password is incorrect.')
                    else:
                        user.set_password(new_password1)
                        user.save()
                        update_session_auth_hash(request, user)  # Keep user logged in
                else:
                    return redirect('profile')
            
            return redirect('profile')
        
        return redirect('profile')
    
    except ValidationError as ve:
        # validation errors
        return HttpResponseServerError(f"Invalid data encountered: {ve}")

    except DatabaseError as db_err:
        # Handle database-specific errors like connection issues or query failures
        return HttpResponseServerError(f"A database error occurred : {db_err}")

    except Exception as e:
        # Catch-all for unexpected errors
        return HttpResponseServerError(f"error occurred : {e}")



# My Bookings view
@login_required(login_url='signin')
def my_bookings(request):
    """
    Display all bookings for the current logged-in user
    """
    try:
        # Get all bookings for the current user with related data
        today = date.today()
    
    # Get all user bookings
        all_bookings = BookingTrip.objects.filter(
            user=request.user
        ).select_related('trip').prefetch_related('passengers').order_by('-booked_at')
        
        # UPCOMING BOOKINGS: 
        # - Trip date is in future (>=today)
        # - Booking status is Confirmed OR payment_status is pending
        # - NOT cancelled
        upcoming_bookings = all_bookings.filter(
            trip__travel_date__gte=today
        ).filter(
            models.Q(booking_status='Confirmed') | models.Q(payment_status='pending')
        ).exclude(booking_status='Cancelled')
        
        # PAST BOOKINGS: 
        # - Trip date is in past (<today)
        # - Booking status is Confirmed (trip completed)
        # - NOT cancelled or pending
        past_bookings = all_bookings.filter(
            trip__travel_date__lt=today,
            booking_status='Confirmed'
        ).exclude(booking_status='Cancelled').exclude(payment_status='pending')
        
        # CANCELLED BOOKINGS: 
        # - Booking status is Cancelled (regardless of trip date)
        cancelled_bookings = all_bookings.filter(booking_status='Cancelled')
        
        # Calculate stats
        total_bookings = all_bookings.count()
        successful_bookings = all_bookings.filter(payment_status='success' , booking_status = 'Confirmed').count()
        pending_bookings = all_bookings.filter(payment_status='pending' , booking_status= 'Pending').count()
        total_spent = all_bookings.filter(payment_status='success' , booking_status = 'Confirmed').aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        context = {
            'upcoming_bookings': upcoming_bookings,
            'past_bookings': past_bookings,
            'cancelled_bookings': cancelled_bookings,
            'total_bookings': total_bookings,
            'successful_bookings': successful_bookings,
            'pending_bookings': pending_bookings,
            'total_spent': total_spent,
            'today': today,
        }
        
        return render(request, 'my_bookings.html', context)
        
    except Exception as e:
        return HttpResponseServerError(f"An error occurred : {e}")
    
