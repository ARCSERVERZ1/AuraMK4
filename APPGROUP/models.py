from django.db import models

# Create your models here.


class HomeAutomation(models.Model):
    uid = models.AutoField(primary_key=True)
    user = models.CharField(
        max_length=100,
        default=""
    )
    House = models.CharField(max_length=120)
    room = models.CharField(max_length=100)
    device_name = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    api_url = models.TextField()
    display_order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "home_automation"
        ordering = ["room", "device_name", "display_order"]
        unique_together = ("room", "device_name", "action")

    def __str__(self):
        return f"{self.room} - {self.device_name} - {self.action}"

class UserHouseMapping(models.Model):

    user = models.CharField(max_length=100)
    house = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "house")



class LocationLog(models.Model):


    uid = models.AutoField(primary_key=True)
    user = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visibility = models.IntegerField()
    place_name = models.CharField(max_length=200)
    remarks = models.TextField(blank=True)
    status = models.CharField()
    latitude = models.CharField(max_length=200)
    longitude = models.CharField(max_length=200)
    map_url = models.URLField(blank=True)
    class Meta:
        db_table = "location_log"
        ordering = ["-timestamp"]

    def __str__(self):
        return self.place_name