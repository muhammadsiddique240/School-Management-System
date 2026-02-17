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


# ═══════════════════════════════════════════════════════════════
#  PHASE 1 — Student Profiles & Fee Management
# ═══════════════════════════════════════════════════════════════

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.SET_NULL, null=True, related_name='students')
    roll_number = models.CharField(max_length=20, blank=True)
    parent_name = models.CharField(max_length=100, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True, help_text="For SMS alerts")
    parent_email = models.EmailField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    admission_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['class_grade', 'roll_number']

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.class_grade or 'Unassigned'}"


class FeeStructure(models.Model):
    """Defines how much each class pays monthly."""
    class_grade = models.OneToOneField(ClassGrade, on_delete=models.CASCADE, related_name='fee_structure')
    monthly_tuition = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    late_fine_per_day = models.DecimalField(max_digits=6, decimal_places=2, default=50,
                                            help_text="Fine charged per day after due date")
    due_day = models.PositiveIntegerField(default=10, help_text="Day of month when fee is due")

    def __str__(self):
        return f"{self.class_grade} — Rs. {self.monthly_tuition}/month"


class FeeChallan(models.Model):
    STATUS_CHOICES = [
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
        ('Partial', 'Partially Paid'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='fee_challans')
    month = models.CharField(max_length=20, help_text="e.g. February 2026")
    tuition_amount = models.DecimalField(max_digits=10, decimal_places=2)
    concession = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                      help_text="Scholarship or sibling discount")
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Unpaid')
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'month']
        ordering = ['-generated_at']

    def save(self, *args, **kwargs):
        self.total_amount = self.tuition_amount - self.concession + self.fine
        if self.amount_paid >= self.total_amount and self.total_amount > 0:
            self.status = 'Paid'
        elif self.amount_paid > 0:
            self.status = 'Partial'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.month} — {self.status}"


# ═══════════════════════════════════════════════════════════════
#  PHASE 2 — Attendance System
# ═══════════════════════════════════════════════════════════════

class DailyAttendance(models.Model):
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('E', 'Excused'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendance_marked')
    remarks = models.CharField(max_length=200, blank=True)
    sms_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.date} — {self.get_status_display()}"


# ═══════════════════════════════════════════════════════════════
#  PHASE 3 — Examination & Report Cards
# ═══════════════════════════════════════════════════════════════

class ExamType(models.Model):
    """e.g. Midterm (20%), Final (80%), Quiz (bonus)"""
    name = models.CharField(max_length=50)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage weight, e.g. 20.00")
    max_marks = models.PositiveIntegerField(default=100)
    academic_year = models.CharField(max_length=20, default='2026')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.weightage}%) — Max: {self.max_marks}"


class Result(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results')
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name='results')
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=200, blank=True)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'subject', 'exam_type']
        ordering = ['student', 'subject']

    @property
    def percentage(self):
        if self.exam_type.max_marks > 0:
            return round((self.marks_obtained / self.exam_type.max_marks) * 100, 2)
        return 0

    @property
    def weighted_score(self):
        """Returns weighted contribution: (marks/max) * weightage"""
        if self.exam_type.max_marks > 0:
            return round((self.marks_obtained / self.exam_type.max_marks) * float(self.exam_type.weightage), 2)
        return 0

    @property
    def grade(self):
        pct = self.percentage
        if pct >= 90: return 'A+'
        if pct >= 80: return 'A'
        if pct >= 70: return 'B'
        if pct >= 60: return 'C'
        if pct >= 50: return 'D'
        return 'F'

    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.subject.name} — {self.exam_type.name}: {self.marks_obtained}"
