# File: ResumeProject/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include all URLs from builder app
    path('', include('builder.urls')),
]

# Always serve media files (PDF resumes) — required for both dev and simple deployments
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
