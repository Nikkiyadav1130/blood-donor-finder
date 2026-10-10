from django.contrib import admin
from .models import Donor ,BloodRequest


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'blood_group', 'city', 'phone', 'last_donation_date')
    list_filter = ('blood_group', 'city')
    search_fields = ('full_name', 'city', 'phone')

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'blood_group', 'city', 'urgency', 'is_fulfilled', 'created_at')
    list_filter = ('blood_group', 'urgency', 'is_fulfilled')
    search_fields = ('patient_name', 'city', 'hospital')    