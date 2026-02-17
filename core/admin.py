from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, ClassGrade, Subject, TeacherProfile, Timetable, SalarySlip, LeaveApplication,
    StudentProfile, FeeStructure, FeeChallan, DailyAttendance, ExamType, Result
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(ClassGrade)
class ClassGradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'section')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_grade')
    list_filter = ('class_grade',)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'joining_date', 'basic_salary')


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('class_grade', 'subject', 'teacher', 'day', 'time_slot')
    list_filter = ('day', 'class_grade')


@admin.register(SalarySlip)
class SalarySlipAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'month', 'amount', 'deductions', 'bonus', 'net_amount', 'status')
    list_filter = ('status', 'month')


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'from_date', 'to_date', 'status', 'applied_on')
    list_filter = ('status',)


# ── NEW MODELS ─────────────────────────────────────────────

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'class_grade', 'roll_number', 'parent_name', 'parent_phone')
    list_filter = ('class_grade',)
    search_fields = ('user__first_name', 'user__last_name', 'roll_number')


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('class_grade', 'monthly_tuition', 'late_fine_per_day', 'due_day')


@admin.register(FeeChallan)
class FeeChallanAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'total_amount', 'amount_paid', 'status', 'due_date')
    list_filter = ('status', 'month')
    search_fields = ('student__user__first_name', 'student__user__last_name')


@admin.register(DailyAttendance)
class DailyAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'marked_by', 'sms_sent')
    list_filter = ('status', 'date')
    search_fields = ('student__user__first_name',)


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'weightage', 'max_marks', 'academic_year')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'exam_type', 'marks_obtained', 'grade')
    list_filter = ('exam_type', 'subject')
    search_fields = ('student__user__first_name', 'student__user__last_name')

