from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClassGrade, Subject, TeacherProfile, Timetable, SalarySlip, LeaveApplication


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
