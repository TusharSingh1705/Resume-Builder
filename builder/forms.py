from django import forms
from .models import ResumeData


class ResumeForm(forms.ModelForm):
    class Meta:
        model = ResumeData
        fields = ['name', 'email', 'phone', 'linkedin', 'summary', 'skills']

        widgets = {
            'summary': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Short professional summary (optional)'}),
            'skills': forms.Textarea(
                attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Python, Django, React, Machine Learning'}),
        }

