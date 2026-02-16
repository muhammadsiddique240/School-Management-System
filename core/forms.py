from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, ClassGrade, Subject, TeacherProfile, Timetable, SalarySlip, LeaveApplication


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Username',
        'autofocus': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Password'
    }))


# --- HR Forms ---

class TeacherUserForm(forms.ModelForm):
    """Creates the User account for a teacher."""
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Set a password'
    }))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }


class TeacherProfileForm(forms.ModelForm):
    """Creates the TeacherProfile."""
    class Meta:
        model = TeacherProfile
        fields = ['designation', 'joining_date', 'basic_salary']
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Lecturer'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50000'}),
        }


class ClassGradeForm(forms.ModelForm):
    class Meta:
        model = ClassGrade
        fields = ['name', 'section']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Class 9'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'class_grade']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Physics'}),
            'class_grade': forms.Select(attrs={'class': 'form-select'}),
        }


class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['class_grade', 'subject', 'teacher', 'day', 'time_slot']
        widgets = {
            'class_grade': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'day': forms.Select(attrs={'class': 'form-select'}),
            'time_slot': forms.Select(attrs={'class': 'form-select'}),
        }


# --- Teacher Forms ---

class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['reason', 'from_date', 'to_date']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for leave...'}),
            'from_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'to_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
