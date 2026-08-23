
from django.db import models
from datetime import date

class MealTimeConfig(models.Model):

    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('snack', 'Snack'),
        ('dinner', 'Dinner'),
    ]

    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, unique=True)

    start_time = models.TimeField()
    end_time = models.TimeField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.meal_type} ({self.start_time} - {self.end_time})"

class MealLog(models.Model):
    uid = models.AutoField(primary_key=True)
    user =  models.CharField(max_length=255)
    # Raw User Input
    food_name = models.CharField(max_length=255)
    quantity = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField()

    meal_type = models.CharField(
        max_length=20,
        blank=True
    )
    is_nonveg =  models.CharField(
        max_length=20,
        blank=True
    )
    # AI Estimated Nutrition
    estimated_calories = models.FloatField(null=True, blank=True)
    estimated_protein = models.FloatField(null=True, blank=True)
    estimated_carbs = models.FloatField(null=True, blank=True)
    estimated_fats = models.FloatField(null=True, blank=True)
    estimated_fiber = models.FloatField(null=True, blank=True)
    estimated_sugar = models.FloatField(null=True, blank=True)
    estimated_sodium = models.FloatField(null=True, blank=True)
    # AI metadata
    ai_analytics_req = models.IntegerField(null=True, blank=True, default=1)
    x_field = models.CharField(max_length=255 , default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp'])
        ]
    def __str__(self):
        return f"{self.uid} - {self.food_name} - {self.timestamp}"


class MedicalProfile(models.Model):
    GENDER_CHOICES = [
        ('female', 'Female'),
        ('male', 'Male'),

    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]


    user = models.CharField(max_length=100)

    # Replaced 'age' with 'dob'
    dob = models.DateField(help_text="Format: YYYY-MM-DD")

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)

    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        null=True
    )
    medical_status = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Dynamic property to calculate age
    @property
    def age(self):
        if not self.dob:
            return None
        today = date.today()
        # This boolean math subtracts 1 if the birthday hasn't happened yet this year
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    def __str__(self):
        return f"{self.user}'s Medical Profile"


class MedicalEventLog(models.Model):
    uid = models.AutoField(primary_key=True)
    # Keeping it as CharField to match your other tables' structure
    user_name = models.CharField(max_length=255)

    medical_event = models.CharField(max_length=255)  # e.g., "Headache", "Nausea"
    severity = models.IntegerField(blank=True, null=True)  # e.g., 1 to 10 scale
    remarks = models.TextField(blank=True, null=True)

    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)

    status = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Ongoing", "Resolved"


    # Audit fields (will be excluded from AI)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start']
        indexes = [
            models.Index(fields=['user_name', 'start'])
        ]

    def __str__(self):
        return f"{self.uid} - {self.user_name} - {self.medical_event}"


class HealthAnalysisMeta(models.Model):
    user = models.CharField(max_length=50)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    health_rating = models.CharField(max_length=50)  # e.g., "Fair"
    health_score = models.IntegerField()  # e.g., 62

    health_recommendation = models.TextField()  # Bullet points of actions
    top_problems = models.TextField(blank=True)  # Bullet points of recurring issues
    top_positive_patterns = models.TextField(blank=True)  # Bullet points of good habits

    no_of_meals = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} Analysis: {self.start_time.date()} to {self.end_time.date()}"


class MealAnalysis(models.Model):

    # Link back to the Meta table
    analysis_meta = models.ForeignKey(HealthAnalysisMeta, on_delete=models.CASCADE, related_name='meal_analyses')

    meal_type = models.CharField(max_length=20)

    # ==========================
    # Timing
    # ==========================
    timing_status = models.IntegerField()
    timing_metrics = models.CharField(max_length=100, blank=True,
                                      null=True)  # e.g., "Average: 10:15 | Recommended: 07:00-09:30"
    timing_ai_remarks = models.TextField()

    # ==========================
    # Quantity
    # ==========================
    quantity_status = models.IntegerField()
    quantity_ai_remarks = models.TextField()

    # ==========================
    # Portion
    # ==========================
    portion_status = models.IntegerField()
    portion_ai_remarks = models.TextField()

    # ==========================
    # Nutrition
    # ==========================
    nutrition_status = models.IntegerField()
    nutrition_ai_remarks = models.TextField()

    # ==========================
    # Overall
    # ==========================
    overall_status = models.IntegerField()
    overall_score = models.IntegerField(blank=True, null=True)
    overall_ai_remarks = models.TextField()

    # ==========================
    # Recommendations
    # ==========================
    add_recommendations = models.TextField(blank=True)  # Flat string with bullet points
    avoid_recommendations = models.TextField(blank=True)  # Flat string with bullet points

    def __str__(self):
        return f"{self.meal_type} Analysis for {self.analysis_meta}"