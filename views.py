from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.db import models
from .forms import UserRegistrationForm, UserLoginForm, AppointmentForm, RescheduleAppointmentForm
from .models import Appointment, Doctor
from django.contrib.auth.decorators import login_required

# Create your views here.

def homepage(request):
    """View function for homepage2.html"""
    user_name = None
    if request.user.is_authenticated:
        try:
            # Try to get full name from UserProfile
            profile = request.user.userprofile
            if profile.full_name:
                # Display first part of full name
                user_name = profile.full_name.split()[0]
            else:
                # Fallback to first part of email (before @)
                user_name = request.user.username.split('@')[0]
        except:
            # If no profile exists, use first part of email
            user_name = request.user.username.split('@')[0]
    return render(request, 'core/homepage2.html', {'user_name': user_name})

def about(request):
    """View function for about.html"""
    return render(request, 'core/about.html')


def contact(request):
    """View function for contact.html"""
    return render(request, 'core/contact.html')

def ap(request):
    """View function for ap.html - Acupuncture Therapy"""
    return render(request, 'core/ap.html')

def ac(request):
    """View function for ac.html - Acupressure Therapy"""
    return render(request, 'core/ac.html')

def cupping(request):
    """View function for cupping.html - Cupping Therapy"""
    return render(request, 'core/cupping.html')

def detox(request):
    """View function for detox.html - Detox Therapy"""
    return render(request, 'core/detox.html')

def signup_view(request):
    """View function for user registration/signup"""
    # If user is already logged in, redirect to homepage
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('core:homepage')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to Prakriti Niketan.')
                next_page = request.POST.get('next') or request.GET.get('next') or 'core:homepage'
                return redirect(next_page)
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            # Display specific validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/signup.html', {'form': form})

def login_view(request):
    """View function for user login"""
    # If user is already logged in, redirect to homepage
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('core:homepage')
        
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, 'Login successful! Welcome back to Prakriti Niketan.')
            
            # Redirect to next page if specified, otherwise to homepage
            next_page = request.POST.get('next') or request.GET.get('next') or 'core:homepage'
            return redirect(next_page)
        else:
            # Display specific validation errors
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = UserLoginForm()
    
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    """View function for user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:homepage')

def massage(request):
    """View function for massage.html - Massage Therapy"""
    return render(request, 'core/massage.html')

def services(request):
    """View function for services.html"""
    return render(request, 'core/services.html')

def yoga(request):
    """View function for yoga.html - Yoga Therapy"""
    return render(request, 'core/yoga.html')

@login_required
def book_appointment(request):
    """View function for booking appointments (login required)"""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                appointment = form.save(commit=False)
                
                # If user is logged in, associate appointment with user
                if request.user.is_authenticated:
                    appointment.user = request.user
                    # Pre-fill user data if available
                    try:
                        user_profile = request.user.userprofile
                        if not appointment.full_name:
                            appointment.full_name = user_profile.full_name
                        if not appointment.email:
                            appointment.email = request.user.email
                        if not appointment.mobile:
                            appointment.mobile = user_profile.mobile
                    except:
                        pass
                else:
                    # For non-logged in users, create a temporary user or handle differently
                    # For now, we'll allow anonymous bookings
                    appointment.user = None
                
                # Auto-assign doctor based on selected therapy with defaults and fallback
                selected_therapy = appointment.therapy_type
                try:
                    assigned_doctor = None

                    # Default doctor mapping per therapy
                    default_doctors = {
                        'cupping': 'Amit Kumar',
                        'acupressure': 'Priya Patel',
                        'massage': 'Priya Patel',
                        'acupuncture': 'Rajesh',
                        'detox': 'Rajesh',
                    }
                    fallback_doctor_name = 'Amit Kumar'

                    if selected_therapy in default_doctors:
                        target_name = default_doctors[selected_therapy]
                        default_doc = Doctor.objects.filter(name__iexact=target_name).first()
                        if default_doc and default_doc.is_available:
                            assigned_doctor = default_doc
                        else:
                            # Fallback to Amit Kumar if default doc is not available
                            fallback_doc = Doctor.objects.filter(name__iexact=fallback_doctor_name).first()
                            if fallback_doc:
                                assigned_doctor = fallback_doc
                    else:
                        # For therapies without explicit default, pick any available by specialization
                        assigned_doctor = Doctor.objects.filter(
                            models.Q(specialization=selected_therapy) |
                            models.Q(secondary_specialization=selected_therapy),
                            is_available=True
                        ).first()
                        if not assigned_doctor:
                            # Final fallback to Amit Kumar
                            fallback_doc = Doctor.objects.filter(name__iexact=fallback_doctor_name).first()
                            if fallback_doc:
                                assigned_doctor = fallback_doc

                    if assigned_doctor:
                        appointment.doctor = assigned_doctor
                        messages.info(request, f"Dr. {assigned_doctor.name} has been assigned for your {appointment.get_therapy_type_display()} appointment.")
                    else:
                        messages.warning(request, "No doctor is currently available for the selected therapy. We will assign one soon.")
                except Exception as e:
                    messages.warning(request, "Doctor assignment will be done manually by our team.")
                
                appointment.save()

                # Build receipt context
                price_map = {
                    'acupressure': 300,
                    'detox': 700,
                    'acupuncture': 1200,
                    'cupping': 800,
                    'massage': 1000,
                }
                selected_therapy = appointment.therapy_type
                price = price_map.get(selected_therapy)
                payment_mode = request.POST.get('payment_mode', '')

                context = {
                    'appointment': appointment,
                    'payment_mode': payment_mode,
                    'price': price,
                }
                return render(request, 'core/appointment_receipt.html', context)
                
            except Exception as e:
                messages.error(request, f'Booking failed: {str(e)}')
        else:
            # Display specific validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = AppointmentForm()
        
        # Pre-fill form for logged-in users
        if request.user.is_authenticated:
            try:
                user_profile = request.user.userprofile
                form.initial = {
                    'full_name': user_profile.full_name,
                    'email': request.user.email,
                    'mobile': user_profile.mobile,
                }
            except:
                form.initial = {
                    'email': request.user.email,
                }
    
    return render(request, 'core/book_appointment.html', {'form': form})

@login_required
def my_appointments(request):
    """View function to display user's appointments
    - Includes appointments linked to the user
    - Also includes past anonymous bookings made with the same email
    - Auto-links any unlinked appointments with the user's email to the user
    """
    user = request.user
    user_email = user.email

    # Link any unassigned appointments that match the user's email
    Appointment.objects.filter(user__isnull=True, email__iexact=user_email).update(user=user)

    # Show both directly linked and email-matched appointments
    appointments = (
        Appointment.objects
        .filter(models.Q(user=user) | models.Q(email__iexact=user_email))
        .order_by('-created_at')
    )
    return render(request, 'core/my_appointments.html', {
        'appointments': appointments,
    })


@login_required
def reschedule_request(request, pk: int):
    """Allow a user to request rescheduling for their own appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)

    # authorize: owner by user or same email
    if not (appointment.user == request.user or appointment.email.lower() == request.user.email.lower()):
        messages.error(request, "You don't have permission to reschedule this appointment.")
        return redirect('core:myappointments')

    if request.method == 'POST':
        form = RescheduleAppointmentForm(request.POST)
        if form.is_valid():
            new_therapy = form.cleaned_data['therapy_type']
            new_date = form.cleaned_data['appointment_date']
            new_time = form.cleaned_data['appointment_time']
            reason = form.cleaned_data.get('reason', '')

            # Update appointment core fields
            appointment.therapy_type = new_therapy
            appointment.appointment_date = new_date
            appointment.appointment_time = new_time
            appointment.status = 'pending'  # reset to pending for review

            # Optional: reassign doctor if therapy changed
            try:
                assigned_doctor = None
                default_doctors = {
                    'cupping': 'Amit Kumar',
                    'acupressure': 'Priya Patel',
                    'massage': 'Priya Patel',
                    'acupuncture': 'Rajesh',
                    'detox': 'Rajesh',
                }
                fallback_doctor_name = 'Amit Kumar'

                if new_therapy in default_doctors:
                    target_name = default_doctors[new_therapy]
                    default_doc = Doctor.objects.filter(name__iexact=target_name).first()
                    if default_doc and default_doc.is_available:
                        assigned_doctor = default_doc
                    else:
                        fallback_doc = Doctor.objects.filter(name__iexact=fallback_doctor_name).first()
                        if fallback_doc:
                            assigned_doctor = fallback_doc
                else:
                    assigned_doctor = Doctor.objects.filter(
                        models.Q(specialization=new_therapy) |
                        models.Q(secondary_specialization=new_therapy),
                        is_available=True
                    ).first()
                    if not assigned_doctor:
                        fallback_doc = Doctor.objects.filter(name__iexact=fallback_doctor_name).first()
                        if fallback_doc:
                            assigned_doctor = fallback_doc

                if assigned_doctor:
                    appointment.doctor = assigned_doctor
            except Exception:
                pass

            appointment.save(update_fields=['therapy_type', 'appointment_date', 'appointment_time', 'status', 'doctor'])

            messages.success(request, 'Your reschedule request has been sent. You will be informed after approval.')
            return redirect('core:myappointments')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = RescheduleAppointmentForm(initial={
            'therapy_type': appointment.therapy_type,
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
        })

    return render(request, 'core/reschedule_request.html', {
        'form': form,
        'appointment': appointment,
    })

@login_required
def appointment_receipt_view(request, pk: int):
    """View a printable receipt for a specific appointment that belongs to the logged-in user."""
    appointment = get_object_or_404(Appointment, pk=pk)

    # Allow viewing if the appointment belongs to the user or matches user email
    if not (appointment.user == request.user or appointment.email.lower() == request.user.email.lower()):
        messages.error(request, "You don't have permission to view this receipt.")
        return redirect('core:myappointments')

    price_map = {
        'acupressure': 300,
        'detox': 700,
        'acupuncture': 1200,
        'cupping': 800,
        'massage': 1000,
    }
    price = price_map.get(appointment.therapy_type)

    context = {
        'appointment': appointment,
        'payment_mode': '',  # not stored; can be extended later
        'price': price,
    }
    return render(request, 'core/appointment_receipt.html', context)
