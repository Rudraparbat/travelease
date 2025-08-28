from django.contrib import admin
from django.urls import path , include
from travels import views

urlpatterns = [
    path('', views.main_page, name='home'),
    path('details/<int:trip_id>/', views.trip_detail, name='details'),
    path('bookingpage/<int:trip_id>/', views.booking_page, name='bookingpage'),
    path('create-booking/', views.create_razorpay_order, name='create_booking'),
    path('confirm-booking/<int:trip_id>/', views.confirm_online_booking, name='confirm_booking'),
    path('confirm-offline-booking/<int:trip_id>/', views.confirm_offline_booking, name='confirm_offline_booking'),
    path('signup/', views.sign_up, name='signup'),
    path('signin/', views.sign_in, name='signin'),
    path('logout/', views.logout_user, name='logout'),
    path('404/', views.not_existed_page, name='errorpage'),
    path('mybookings/', views.my_bookings, name='mybookings'),
    path('profile/', views.profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('booking/<int:booking_id>/cancel/', views.cancel_offline_reservation, name='cancel_offline_booking'),


]