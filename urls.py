from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.homepage, name='homepage'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    
    
    # Therapy pages
    path('ap/', views.ap, name='ap'),
    path('ac/', views.ac, name='ac'),
    path('yoga/', views.yoga, name='yoga'),
    path('detox/', views.detox, name='detox'),
    path('massage/', views.massage, name='massage'),
    path('cupping/', views.cupping, name='cupping'),
    path('bookappointment/', views.book_appointment, name='bookappointment'),
    path('myappointments/', views.my_appointments, name='myappointments'),
    path('appointment/<int:pk>/reschedule/', views.reschedule_request, name='reschedule'),
    path('receipt/<int:pk>/', views.appointment_receipt_view, name='receipt'),
]