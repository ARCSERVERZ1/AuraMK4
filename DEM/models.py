from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    family_name = models.CharField(max_length=100)
    imap_password = models.CharField(max_length=255)
    auto_data_log = models.BooleanField(default=False)
    alerts = models.BooleanField(default=False)
    payment_methods = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email

# DEM/models.py
from django.db import models

class Transaction(models.Model):
    uid = models.AutoField(primary_key=True)  # 👈 auto increment UID

    user = models.CharField(max_length=100)
    date = models.DateField()
    transaction_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    sender_bank = models.CharField(max_length=150)
    receiver_bank = models.CharField(max_length=150)
    message = models.TextField()
    category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100)
    group = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=100)
    status = models.IntegerField(default=1)
    is_auto_cat = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['category']),
            models.Index(fields=['sub_category']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"TXN-{self.uid} | {self.user} | {self.amount}"

class ExpenseCategory(models.Model):

    category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100)
    notes = models.TextField(
        blank=True,
        help_text="Semantic hints / keywords for auto categorisation"
    )
    status = models.CharField(
        max_length=10,
        default='ACTIVE'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expense_category"
        unique_together = ('category', 'sub_category')
        ordering = ['category', 'sub_category']

    def __str__(self):
        return f"{self.category} → {self.sub_category}"




class ExpenseCategoryPlan(models.Model):
    user = models.CharField(
        max_length=100,
        db_index=True
    )

    month = models.DateField(
        help_text="Store first day of month (YYYY-MM-01)",
        db_index=True
    )

    category = models.CharField(
        max_length=100,
        db_index=True
    )

    planned_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "expense_category_plan"
        unique_together = ("user", "month", "category")
        ordering = ["category"]

    def __str__(self):
        return f"{self.user} | {self.month} | {self.category}"
