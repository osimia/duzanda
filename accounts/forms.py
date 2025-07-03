from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User  # если у тебя кастомный User

from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    ROLE_CHOICES = (
        ('buyer', 'Покупатель'),
        ('master', 'Мастер'),
    )
    email = forms.EmailField()
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'address', 'avatar']

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
