from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class User(AbstractUser):
    ROLE_CHOICES = [
        ('Principal', 'Principal'),
        ('HR', 'HR'),
        ('Teacher', 'Teacher'),
        ('Student', 'Student'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Student')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class ClassGrade(models.Model):
    name = models.CharField(max_length=50, help_text="e.g. Class 9")
    section = models.CharField(max_length=10, help_text="e.g. A, B, C")

    class Meta:
        unique_together = ['name', 'section']
        ordering = ['name', 'section']

    def __str__(self):
        return f"{self.name} - {self.section}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE, related_name='subjects')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.class_grade})"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    designation = models.CharField(max_length=100, default='Lecturer')
    joining_date = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"


class Timetable(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]
    TIME_SLOT_CHOICES = [
        ('08:00-08:45', '08:00 - 08:45'),
        ('08:45-09:30', '08:45 - 09:30'),
        ('09:30-10:15', '09:30 - 10:15'),
        ('10:30-11:15', '10:30 - 11:15'),
        ('11:15-12:00', '11:15 - 12:00'),
        ('12:00-12:45', '12:00 - 12:45'),
        ('01:30-02:15', '01:30 - 02:15'),
        ('02:15-03:00', '02:15 - 03:00'),
    ]

    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE, related_name='timetable_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_entries')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='timetable_entries')
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    time_slot = models.CharField(max_length=15, choices=TIME_SLOT_CHOICES)

    class Meta:
        ordering = ['day', 'time_slot']

    def clean(self):
        # Constraint: A teacher cannot have 2 classes at the same time
        conflict = Timetable.objects.filter(
            teacher=self.teacher, day=self.day, time_slot=self.time_slot
        ).exclude(pk=self.pk)
        if conflict.exists():
            raise ValidationError(
                f"{self.teacher} already has a class on {self.day} at {self.time_slot}."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.class_grade} | {self.subject.name} | {self.teacher.user.get_full_name()} | {self.day} {self.time_slot}"


class SalarySlip(models.Model):
    STATUS_CHOICES = [
        ('Generated', 'Generated'),
        ('Approved', 'Approved by Principal'),
        ('Paid', 'Paid'),
    ]

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='salary_slips')
    month = models.CharField(max_length=20, help_text="e.g. January 2026")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Generated')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['teacher', 'month']
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.net_amount = self.amount - self.deductions + self.bonus
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.month} - {self.status}"


class LeaveApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_applications')
    reason = models.TextField()
    from_date = models.DateField()
    to_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    applied_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_on']

    def clean(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValidationError("'From Date' cannot be after 'To Date'.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} | {self.from_date} to {self.to_date} | {self.status}"
