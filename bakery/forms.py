from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator, EmailValidator,MaxLengthValidator
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from django.contrib.auth import get_user_model, authenticate

class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter Your E-Mail',
            'class': 'form-input',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Please enter your email',
            'invalid': 'Please enter a valid email address'
        }
    )
    
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
            'class': 'form-input',
            'autocomplete': 'given-name'
        }),
        min_length=2,
        max_length=30,
        error_messages={
            'required': 'Please enter your first name',
            'min_length': 'First name must be at least 2 characters',
            'max_length': 'First name cannot exceed 30 characters'
        },
        validators=[
            RegexValidator(
                regex='^[a-zA-Z ]+$',
                message="Only letters and spaces allowed in first name"
            )
        ]
    )
    
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
            'class': 'form-input',
            'autocomplete': 'family-name'
        }),
        min_length=1,
        max_length=30,
        error_messages={
            'required': 'Please enter your last name',
            'min_length': 'Last name must be at least 1 characters',
            'max_length': 'Last name cannot exceed 30 characters'
        },
        validators=[
            RegexValidator(
                regex='^[a-zA-Z ]+$',
                message="Only letters and spaces allowed in last name"
            )
        ]
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter Your Password',
            'class': 'form-input',
            'autocomplete': 'new-password'
        }),
        error_messages={
            'required': 'Please enter a password'
        },
        validators=[
            MinLengthValidator(8, message="Password must be at least 8 characters."),
            validate_password
        ]
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter Your E-Mail',
            'class': 'form-input',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Please enter your email',
            'invalid': 'Please enter a valid email address'
        }
    )
    
    password = forms.CharField(
    widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Your Password',
        'class': 'form-input',
        'autocomplete': 'new-password',
        'data-validate': 'password'
    }),
    error_messages={
        'required': 'Please enter a password',
    },
    validators=[
        MinLengthValidator(8),
        RegexValidator(
            regex='^(?=.*\d)(?=.*[a-zA-Z]).{8,10}$',
            message="Password must contain both letters and numbers"
        ),
        validate_password
    ]
)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive")
            cleaned_data['user'] = user
        
        return cleaned_data


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter Your E-Mail',
            'class': 'form-input',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Please enter your email',
            'invalid': 'Please enter a valid email address'
        }
    )
    
    new_password = forms.CharField(
    widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter New Password (8-10 characters)',
        'class': 'form-input',
        'autocomplete': 'new-password'
    }),
    error_messages={
        'required': 'Please enter a new password',
        'min_length': 'Password must be 8-10 characters long',
        'max_length': 'Password must be 8-10 characters long'
    },
    validators=[
        MinLengthValidator(8, message="Password must be at least 8 characters."),
        MaxLengthValidator(10, message="Password cannot exceed 10 characters."),
        RegexValidator(
            regex='^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,10}$',
            message="Password must contain: 1 uppercase, 1 lowercase, and 1 number"
        ),
        validate_password
    ],
    min_length=8,
    max_length=10
)
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm New Password',
            'class': 'form-input',
            'autocomplete': 'new-password'
        }),
        error_messages={
            'required': 'Please confirm your new password'
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError({
                'confirm_password': "Passwords do not match"
            })

        if email:
            User = get_user_model()
            if not User.objects.filter(email=email).exists():
                raise ValidationError({
                    'email': "No account found with this email address"
                })

        return cleaned_data