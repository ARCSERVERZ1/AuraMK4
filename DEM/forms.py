from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User

class UserAdminCreationForm(forms.ModelForm):
    """Form for creating new users in admin"""
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username','email', 'family_name', 'imap_password','payment_methods' , 'auto_data_log' , 'alerts')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class UserAdminChangeForm(forms.ModelForm):
    """Form for updating users in admin"""
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('username','email', 'family_name', 'imap_password', 'payment_methods' , 'auto_data_log', 'alerts','password', 'is_active', 'is_staff', 'is_superuser')