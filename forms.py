from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import re
from .models import UserProfile, Appointment

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your full name',
            'id': 'fullname',
            'name': 'fullname'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email',
            'id': 'email',
            'name': 'email'
        })
    )
    mobile = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 10 digit mobile number',
            'id': 'mobile',
            'name': 'mobile',
            'pattern': '[0-9]{10}'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Your address',
            'id': 'address',
            'name': 'address',
            'rows': 2
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password (min 5 letters + 3 numbers)',
            'id': 'password',
            'name': 'password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password',
            'id': 'password2',
            'name': 'password2'
        })
    )


    class Meta:
        model = User
        fields = ('email', 'full_name', 'mobile', 'address', 'password1', 'password2')
    
    def clean_mobile(self):
        """Validate mobile number - must be exactly 10 digits"""
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            # Remove any spaces, + signs, or other characters
            mobile_digits = re.sub(r'[^\d]', '', mobile)
            
            if len(mobile_digits) != 10:
                raise ValidationError("Mobile number must be exactly 10 digits.")
            
            if not mobile_digits.isdigit():
                raise ValidationError("Mobile number must contain only digits.")
                
            return mobile_digits
        return mobile
    
    def clean_email(self):
        """Validate email - must contain @ symbol"""
        email = self.cleaned_data.get('email')
        if email:
            if '@' not in email:
                raise ValidationError("Email must contain @ symbol.")
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError("This email is already registered.")
                
        return email
    
    def clean_password1(self):
        """Validate password - must have at least 5 letters and 3 numbers"""
        password = self.cleaned_data.get('password1')
        if password:
            # Count letters and numbers
            letters = len(re.findall(r'[a-zA-Z]', password))
            numbers = len(re.findall(r'\d', password))
            
            if letters < 5:
                raise ValidationError("Password must contain at least 5 letters.")
            
            if numbers < 3:
                raise ValidationError("Password must contain at least 3 numbers.")
                
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
                
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                mobile=self.cleaned_data['mobile'],
                address=self.cleaned_data.get('address', '')
            )
        return user


class UserLoginForm(forms.Form):
    """Custom login form using username instead of email"""
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your username',
            'id': 'login_username',
            'name': 'username',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'id': 'login_password',
            'name': 'password',
            'class': 'form-control'
        })
    )
    
    def clean(self):
        """Validate login credentials"""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Authenticate using username
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError("Invalid username or password.")
            elif not user.is_active:
                raise ValidationError("This account is inactive.")
            else:
                cleaned_data['user'] = user
        
        return cleaned_data


class AppointmentForm(forms.ModelForm):
    """Form for booking appointments"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove Yoga from therapy options in booking form
        if 'therapy_type' in self.fields:
            self.fields['therapy_type'].choices = [
                (value, label) for value, label in self.fields['therapy_type'].choices
                if value != 'yoga'
            ]
    
    class Meta:
        model = Appointment
        fields = ['full_name', 'email', 'mobile', 'therapy_type', 'appointment_date', 'appointment_time', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Enter your full name',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'class': 'form-control'
            }),
            'mobile': forms.TextInput(attrs={
                'placeholder': 'Enter 10 digit mobile number',
                'class': 'form-control',
                'pattern': '[0-9]{10}'
            }),
            'therapy_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'appointment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': '2025-01-01'
            }),
            'appointment_time': forms.Select(attrs={
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Any specific requirements or health conditions (optional)',
                'class': 'form-control',
                'rows': 3
            })
        }
    
    def clean_mobile(self):
        """Validate mobile number - must be exactly 10 digits"""
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            # Remove any spaces, + signs, or other characters
            mobile_digits = re.sub(r'[^\d]', '', mobile)
            
            if len(mobile_digits) != 10:
                raise ValidationError("Mobile number must be exactly 10 digits.")
            
            if not mobile_digits.isdigit():
                raise ValidationError("Mobile number must contain only digits.")
                
            return mobile_digits
        return mobile
    
    def clean_appointment_date(self):
        """Validate appointment date - must be in the future"""
        from datetime import date
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date:
            if appointment_date < date.today():
                raise ValidationError("Appointment date cannot be in the past.")
        return appointment_date


class RescheduleAppointmentForm(forms.Form):
    """Form to request rescheduling an existing appointment (allows therapy change)"""
    therapy_type = forms.ChoiceField(
        choices=[(value, label) for value, label in Appointment.THERAPY_CHOICES if value != 'yoga'],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    appointment_time = forms.ChoiceField(
        choices=Appointment.TIME_SLOTS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Reason for rescheduling (optional)',
            'class': 'form-control',
            'rows': 3
        })
    )

    def clean_appointment_date(self):
        from datetime import date
        new_date = self.cleaned_data.get('appointment_date')
        if new_date and new_date < date.today():
            raise ValidationError('New appointment date cannot be in the past.')
        return new_date