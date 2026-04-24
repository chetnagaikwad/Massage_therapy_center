from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import F
from .models import UserProfile, Appointment, Doctor, RescheduleRequest

# Register your models here.

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'
    fields = ('full_name', 'mobile', 'address', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_full_name', 'get_mobile', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'userprofile__full_name', 'userprofile__mobile')
    
    def get_full_name(self, obj):
        try:
            return obj.userprofile.full_name
        except UserProfile.DoesNotExist:
            return '-'
    get_full_name.short_description = 'Full Name'
    
    def get_mobile(self, obj):
        try:
            return obj.userprofile.mobile
        except UserProfile.DoesNotExist:
            return '-'
    get_mobile.short_description = 'Mobile'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'get_email', 'mobile', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('full_name', 'mobile', 'user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'get_specializations', 'experience_years', 'is_available', 'created_at')
    list_filter = ('specialization', 'secondary_specialization', 'is_available', 'experience_years')
    search_fields = ('name', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_available',)
    
    fieldsets = (
        ('Doctor Information', {
            'fields': ('name', 'phone', 'experience_years', 'is_available')
        }),
        ('Specializations', {
            'fields': ('specialization', 'secondary_specialization'),
            'description': 'Select primary and secondary therapy specializations'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_specializations(self, obj):
        specs = [obj.get_specialization_display()]
        if obj.secondary_specialization:
            specs.append(obj.get_secondary_specialization_display())
        return ', '.join(specs)
    get_specializations.short_description = 'Specializations'

from django.core.mail import send_mail
from django.conf import settings

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'mobile', 'therapy_type', 'get_doctor_name', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('therapy_type', 'doctor', 'status', 'appointment_date', 'created_at')
    search_fields = ('full_name', 'email', 'mobile', 'user__username', 'doctor__name')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user', 'full_name', 'email', 'mobile')
        }),
        ('Appointment Details', {
            'fields': ('therapy_type', 'doctor', 'appointment_date', 'appointment_time', 'status')
        }),
        ('Additional Information', {
            'fields': ('message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.name}" if obj.doctor else "Not Assigned"
    get_doctor_name.short_description = 'Doctor'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def save_model(self, request, obj, form, change):
        # Detect status changes to send notifications to the user
        old_status = None
        if change:
            try:
                old_obj = Appointment.objects.get(pk=obj.pk)
                old_status = old_obj.status
            except Appointment.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

        # If status changed, notify user
        if old_status and old_status != obj.status:
            if obj.email:  # prefer appointment email
                recipient = obj.email
            elif obj.user and obj.user.email:
                recipient = obj.user.email
            else:
                recipient = None

            if recipient:
                subject = "Your appointment reschedule update"
                if obj.status == 'confirmed':
                    message = (
                        f"Hello {obj.full_name},\n\n"
                        f"Your reschedule request has been CONFIRMED.\n"
                        f"Therapy: {obj.get_therapy_type_display()}\n"
                        f"Date: {obj.appointment_date} at {obj.appointment_time}\n"
                        f"Doctor: {('Dr. ' + obj.doctor.name) if obj.doctor else 'To be assigned'}\n\n"
                        f"Thank you,\nPrakriti Niketan"
                    )
                elif obj.status == 'cancelled':
                    message = (
                        f"Hello {obj.full_name},\n\n"
                        f"Your reschedule request has been CANCELED.\n"
                        f"If you have questions or want to try another slot, please reply to this email.\n\n"
                        f"Thank you,\nPrakriti Niketan"
                    )
                else:
                    message = (
                        f"Hello {obj.full_name},\n\n"
                        f"Your appointment status has been updated to: {obj.get_status_display()}.\n\n"
                        f"Thank you,\nPrakriti Niketan"
                    )

                try:
                    send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [recipient], fail_silently=True)
                except Exception:
                    # Avoid admin crash if email backend isn't configured
                    pass


@admin.register(RescheduleRequest)
class RescheduleRequestAdmin(AppointmentAdmin):
    """Show only reschedule requests as a separate admin list using the proxy model."""
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Heuristic: reschedule = pending and updated after initial creation
        return qs.filter(status='pending', updated_at__gt=F('created_at'))

    def has_add_permission(self, request):
        # Reschedule requests are created via user flow, not from admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent accidental deletions here; manage from Appointments if needed
        return False

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
