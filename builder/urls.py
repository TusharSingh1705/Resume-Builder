# # File: builder/urls.py
#
# from django.urls import path
# from .views import ResumeProject, dashboard
# from .auth_views import register, user_login, user_logout
#
# urlpatterns = [
#     # Resume Builder (Main Page)
#     path('', ResumeProject, name='ResumeProject'),
#
#     # Authentication
#     path('register/', register, name='register'),
#     path('login/', user_login, name='login'),
#     path('logout/', user_logout, name='logout'),
#
#     # Dashboard
#     path('dashboard/', dashboard, name='dashboard'),
# ]
from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    path('', auth_views.register, name='register'),
    path('generate/', views.generate_resume, name='generate_resume'),
    path('home/', views.home, name='home'),
    path('login/', auth_views.user_login, name='user_login'),
    path('logout/', auth_views.user_logout, name='user_logout'),
path('dashboard/', views.dashboard, name='dashboard'),
    path('enhance/', views.enhance_text, name='enhance_text'), # New AI Endpoint
]