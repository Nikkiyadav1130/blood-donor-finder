from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='donors/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('donors/', views.donor_list, name='donor_list'),
    path('donors/<int:pk>/', views.donor_detail, name='donor_detail'),
    path('statistics/', views.statistics, name='statistics'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/new/', views.request_create, name='request_create'),
    path('requests/<int:pk>/fulfill/', views.request_fulfill, name='request_fulfill'),
]