from django.db import models
from django.contrib.auth.models import User

class ResumeData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    linkedin = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True)
    education = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    projects = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True )

    def __str__(self):
        return f"{self.name} - {self.user.username}"