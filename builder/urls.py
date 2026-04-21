# File: builder/urls.py

from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    # ── Auth ──
    path('', auth_views.register, name='register'),
    path('login/', auth_views.user_login, name='user_login'),
    path('logout/', auth_views.user_logout, name='user_logout'),

    # ── Resume Builder ──
    path('home/', views.home, name='home'),
    path('generate/', views.generate_resume, name='generate_resume'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete/<int:resume_id>/', views.delete_resume, name='delete_resume'),
    path('download/<int:resume_id>/', views.download_resume, name='download_resume'),
    path('rename/<int:resume_id>/', views.rename_resume, name='rename_resume'),

    # ── API ──
    path('enhance/', views.enhance_text, name='enhance_text'),
]