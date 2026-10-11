from django import forms
from django.contrib.auth.models import User
from .models import Donor, BloodRequest


class DonorRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    consent_given = forms.BooleanField(
        required=True,
        label="I agree to share my contact details with logged-in users of this site.",
        error_messages={'required': "You must agree to share your contact details to register."},
    )

    class Meta:
        model = Donor
        fields = ['full_name', 'age', 'gender', 'blood_group',
                  'phone', 'city', 'last_donation_date', 'consent_given']
        widgets = {
            'last_donation_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_age(self):
        age = self.cleaned_data['age']
        if age < 18 or age > 60:
            raise forms.ValidationError("Donor age must be between 18 and 60.")
        return age

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['patient_name', 'blood_group', 'units_needed', 'hospital',
                  'city', 'contact_phone', 'urgency', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_units_needed(self):
        units = self.cleaned_data['units_needed']
        if units < 1 or units > 10:
            raise forms.ValidationError("Units needed must be between 1 and 10.")
        return units    