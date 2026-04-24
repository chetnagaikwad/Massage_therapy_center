from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Doctor(models.Model):
    THERAPY_CHOICES = [
        ('acupuncture', 'Acupuncture Therapy'),
        ('acupressure', 'Acupressure Therapy'),
        ('detox', 'Detox Therapy'),
        ('massage', 'Massage Therapy'),
        ('cupping', 'Cupping Therapy'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Doctor Name")
    phone = models.CharField(max_length=15, verbose_name="Phone Number")
    specialization = models.CharField(
        max_length=20, 
        choices=THERAPY_CHOICES, 
        verbose_name="Primary Specialization"
    )
    secondary_specialization = models.CharField(
        max_length=20, 
        choices=THERAPY_CHOICES, 
        blank=True, 
        null=True,
        verbose_name="Secondary Specialization"
    )
    experience_years = models.PositiveIntegerField(default=1, verbose_name="Years of Experience")
    is_available = models.BooleanField(default=True, verbose_name="Currently Available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        specializations = [self.get_specialization_display()]
        if self.secondary_specialization:
            specializations.append(self.get_secondary_specialization_display())
        return f"Dr. {self.name} - {', '.join(specializations)}"
    
    def get_all_specializations(self):
        """Return list of all specializations"""
        specs = [self.specialization]
        if self.secondary_specialization:
            specs.append(self.secondary_specialization)
        return specs
    
    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"
        ordering = ['name']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.user.email})"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class Appointment(models.Model):
    THERAPY_CHOICES = [
        ('acupuncture', 'Acupuncture Therapy'),
        ('acupressure', 'Acupressure Therapy'),
        ('yoga', 'Yoga Therapy'),
        ('detox', 'Detox Therapy'),
        ('massage', 'Massage Therapy'),
        ('cupping', 'Cupping Therapy'),
    ]
    
    TIME_SLOTS = [
        ('09:00', '09:00 AM'),
        ('10:00', '10:00 AM'),
        ('11:00', '11:00 AM'),
        ('12:00', '12:00 PM'),
        ('14:00', '02:00 PM'),
        ('15:00', '03:00 PM'),
        ('16:00', '04:00 PM'),
        ('17:00', '05:00 PM'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Assigned Doctor")
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    therapy_type = models.CharField(max_length=20, choices=THERAPY_CHOICES)
    appointment_date = models.DateField()
    appointment_time = models.CharField(max_length=5, choices=TIME_SLOTS)
    message = models.TextField(blank=True, null=True, help_text="Any specific requirements or health conditions")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.therapy_type} on {self.appointment_date}"
    
    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ['-created_at']


class RescheduleRequest(Appointment):
    """Proxy model to expose reschedule requests separately in admin."""
    class Meta:
        proxy = True
        verbose_name = "Reschedule Request"
        verbose_name_plural = "Reschedule Requests"
