from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import DonorRegistrationForm, BloodRequestForm
from .models import Donor, BloodRequest
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from django.db.models import Count , Q
from datetime import timedelta
from django.utils import timezone



def home(request):
    return render(request, 'donors/home.html')


def register(request):
    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            donor = form.save(commit=False)
            donor.user = user
            donor.save()
            messages.success(request, "Registration is successfully done !! Thank you for becoming a donor.")
            return redirect('home')
    else:
        form = DonorRegistrationForm()
    return render(request, 'donors/register.html', {'form': form})

def donor_list(request):
    donors = Donor.objects.all().order_by('-created_at')

    blood_group = request.GET.get('blood_group', '')
    city = request.GET.get('city', '').strip()
    available_only = request.GET.get('available') == '1'

    if blood_group:
        donors = donors.filter(blood_group=blood_group)
    if city:
        donors = donors.filter(city__icontains=city)
    if available_only:
        cutoff = timezone.localdate() - timedelta(days=Donor.DONATION_GAP_DAYS)
        donors = donors.filter(
            Q(last_donation_date__isnull=True) | Q(last_donation_date__lte=cutoff)
        )

    context = {
        'donors': donors,
        'blood_groups': [choice[0] for choice in Donor.BLOOD_GROUP_CHOICES],
        'selected_blood_group': blood_group,
        'searched_city': city,
        'available_only': available_only,
    }
    return render(request, 'donors/donor_list.html', context)

def donor_detail(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    return render(request, 'donors/donor_detail.html', {'donor': donor})

def statistics(request):
    # Start every blood group at 0 so groups with no donors still appear on the chart
    counts = {group: 0 for group, _ in Donor.BLOOD_GROUP_CHOICES}

    data = Donor.objects.values('blood_group').annotate(total=Count('id'))
    for row in data:
        counts[row['blood_group']] = row['total']

    # Build the bar chart
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(list(counts.keys()), list(counts.values()), color='#c0392b')
    ax.set_title('Donors per Blood Group')
    ax.set_xlabel('Blood Group')
    ax.set_ylabel('Number of Donors')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.bar_label(bars)
    fig.tight_layout()

    # Convert the chart to a base64 string so it can be shown in HTML
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png')
    plt.close(fig)
    chart = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'chart': chart,
        'total_donors': Donor.objects.count(),
    }
    return render(request, 'donors/statistics.html', context)


def request_list(request):
    requests_qs = BloodRequest.objects.filter(is_fulfilled=False).order_by('-created_at')

    blood_group = request.GET.get('blood_group', '')
    city = request.GET.get('city', '').strip()

    if blood_group:
        requests_qs = requests_qs.filter(blood_group=blood_group)
    if city:
        requests_qs = requests_qs.filter(city__icontains=city)

    context = {
        'blood_requests': requests_qs,
        'blood_groups': [choice[0] for choice in Donor.BLOOD_GROUP_CHOICES],
        'selected_blood_group': blood_group,
        'searched_city': city,
    }
    return render(request, 'donors/request_list.html', context)


@login_required
def request_create(request):
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.requester = request.user
            blood_request.save()
            messages.success(request, "Your blood request has been posted.")
            return redirect('request_list')
    else:
        form = BloodRequestForm()
    return render(request, 'donors/request_form.html', {'form': form})


@login_required
def request_fulfill(request, pk):
    blood_request = get_object_or_404(BloodRequest, pk=pk, requester=request.user)
    if request.method == 'POST':
        blood_request.is_fulfilled = True
        blood_request.save()
        messages.success(request, "Request marked as fulfilled.")
    return redirect('request_list')