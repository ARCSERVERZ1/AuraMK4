from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import *

# --- Forms for adding and changing users in admin ---

class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username','email', 'family_name', 'imap_password','payment_methods' , 'auto_data_log','alerts')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('username','email', 'family_name', 'imap_password', 'payment_methods' ,  'auto_data_log','alerts', 'password', 'is_active', 'is_staff', 'is_superuser')

# --- Custom UserAdmin ---

class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = ('username','email', 'family_name', 'auto_data_log','payment_methods' , 'alerts', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'auto_data_log','alerts')

    fieldsets = (
        (None, {'fields': ('username','email', 'password')}),
        ('Personal Info', {'fields': ('family_name', 'imap_password','payment_methods' ,  'auto_data_log','alerts')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username','email', 'family_name', 'imap_password', 'payment_methods' , 'auto_data_log','alerts', 'password1', 'password2'),
        }),
    )

    search_fields = ('username','email', 'family_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

# Register the custom UserAdmin
admin.site.register(User, UserAdmin)
admin.site.register(ExpenseCategory)
admin.site.register(ExpenseCategoryPlan)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    readonly_fields = (
        'timestamp',
        'created_at',
        'updated_at',
    )