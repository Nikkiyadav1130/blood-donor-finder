from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class Donor(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=100)
    last_donation_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    consent_given = models.BooleanField(default=False)

    
    DONATION_GAP_DAYS = 90

    @property
    def next_available_date(self):
        """Date from which the donor can donate again (None if never donated)."""
        if self.last_donation_date is None:
            return None
        return self.last_donation_date + timedelta(days=self.DONATION_GAP_DAYS)

    @property
    def is_available(self):
        """True if the donor has never donated or the 90-day gap has passed."""
        next_date = self.next_available_date
        return next_date is None or next_date <= timezone.localdate()

    def __str__(self):
        return f"{self.full_name} ({self.blood_group})"


class BloodRequest(models.Model):
    URGENCY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_requests')
    patient_name = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=3, choices=Donor.BLOOD_GROUP_CHOICES)
    units_needed = models.PositiveIntegerField(default=1)
    hospital = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=15)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='normal')
    note = models.TextField(blank=True)
    is_fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.patient_name} needs {self.blood_group} in {self.city}"