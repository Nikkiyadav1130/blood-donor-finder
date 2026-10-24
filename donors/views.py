from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone
from .models import Donor, BloodRequest
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
    all_donors = Donor.objects.all()

    cutoff = timezone.localdate() - timedelta(days=Donor.DONATION_GAP_DAYS)
    available_donors = all_donors.filter(
        Q(last_donation_date__isnull=True) | Q(last_donation_date__lte=cutoff)
    ).order_by('-created_at')[:5]

    # Recent activity: latest donors and requests merged (no personal names shown)
    activity = [
        {'text': f"New donor registered ({d.blood_group}, {d.city})", 'time': d.created_at, 'kind': 'donor'}
        for d in all_donors.order_by('-created_at')[:3]
    ]
    activity += [
        {'text': f"Blood request: {r.blood_group} needed in {r.city}", 'time': r.created_at, 'kind': 'request'}
        for r in BloodRequest.objects.order_by('-created_at')[:3]
    ]
    activity.sort(key=lambda a: a['time'], reverse=True)

    context = {
        'total_donors': all_donors.count(),
        'blood_groups_count': all_donors.values('blood_group').distinct().count(),
        'cities_count': all_donors.values('city').distinct().count(),
        'fulfilled_count': BloodRequest.objects.filter(is_fulfilled=True).count(),
        'available_donors': available_donors,
        'activity': activity[:5],
        'blood_groups': [choice[0] for choice in Donor.BLOOD_GROUP_CHOICES],
    }
    return render(request, 'donors/home.html', context)


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

def _fig_to_base64(fig):
    """Convert a Matplotlib figure to a base64 PNG string for embedding in HTML."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=130, transparent=True, bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def statistics(request):
    from matplotlib.lines import Line2D

    groups = [g for g, _ in Donor.BLOOD_GROUP_CHOICES]

    # Soft pastel colours, close to the reference design
    bar_colors = {
        'A+': '#a99cf0', 'A-': '#cdbff3', 'B+': '#8ebcf9', 'B-': '#8fd9bf',
        'O+': '#f9a1b2', 'O-': '#fdc27c', 'AB+': '#c9a3ea', 'AB-': '#86c8f5',
    }
    pie_colors = {
        'O+': '#f4657e', 'A+': '#fdbb6a', 'B+': '#6fcf97', 'A-': '#7db8f7',
        'B-': '#a08fdc', 'AB+': '#cba6ea', 'AB-': '#7ec8f0', 'O-': '#f6a35c',
    }

    counts = {g: 0 for g in groups}
    for row in Donor.objects.values('blood_group').annotate(total=Count('id')):
        counts[row['blood_group']] = row['total']
    total = sum(counts.values())

    chart = pie_chart = ''

    if total > 0:
        # 1. Bar chart: donors per blood group
        fig, ax = plt.subplots(figsize=(7, 4.2))
        bars = ax.bar(groups, [counts[g] for g in groups],
                      color=[bar_colors[g] for g in groups], width=0.58)
        ax.bar_label(bars, padding=4, fontsize=11, color='#475569')
        ax.set_ylim(0, max(counts.values()) * 1.25 + 1)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=4))
        ax.spines[['top', 'right']].set_visible(False)
        ax.spines[['left', 'bottom']].set_color('#e2e8f0')
        ax.tick_params(colors='#64748b', length=0, labelsize=10)
        fig.tight_layout()
        chart = _fig_to_base64(fig)

        # 2. Pie chart with a coloured legend on the right
        used = sorted([g for g in groups if counts[g] > 0], key=lambda g: -counts[g])
        fig, ax = plt.subplots(figsize=(6.5, 4.2))
        wedges, _, autotexts = ax.pie(
            [counts[g] for g in used],
            colors=[pie_colors[g] for g in used],
            startangle=90,
            counterclock=False,
            autopct=lambda p: f'{p:.0f}%' if p >= 6 else '',
            pctdistance=0.68,
            wedgeprops=dict(edgecolor='white', linewidth=1.5),
        )
        for t in autotexts:
            t.set_color('white')
            t.set_fontweight('bold')
            t.set_fontsize(10)
        handles = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor=pie_colors[g], markersize=11)
            for g in used
        ]
        labels = [f'{g}      {counts[g] * 100 / total:.0f}%' for g in used]
        ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1.0, 0.5),
                  frameon=False, fontsize=11, labelcolor='#475569', handletextpad=0.8)
        pie_chart = _fig_to_base64(fig)

    # Numbers for the stat cards
    cutoff = timezone.localdate() - timedelta(days=Donor.DONATION_GAP_DAYS)
    available_count = Donor.objects.filter(
        Q(last_donation_date__isnull=True) | Q(last_donation_date__lte=cutoff)
    ).count()

    context = {
        'chart': chart,
        'pie_chart': pie_chart,
        'total_donors': total,
        'groups_count': sum(1 for g in groups if counts[g] > 0),
        'available_count': available_count,
        'fulfilled_count': BloodRequest.objects.filter(is_fulfilled=True).count(),
        'emergency_count': BloodRequest.objects.filter(
            is_fulfilled=False, urgency__in=['urgent', 'critical']
        ).count(),
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