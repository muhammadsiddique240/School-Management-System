import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import (
    User, ClassGrade, Subject, TeacherProfile,
    Timetable, SalarySlip, LeaveApplication
)
from .forms import (
    LoginForm, TeacherUserForm, TeacherProfileForm,
    ClassGradeForm, SubjectForm, TimetableForm,
    LeaveApplicationForm
)
from .decorators import role_required


# ─────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
    else:
        form = LoginForm(request)
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ─────────────────────────────────────────────
# DASHBOARD (Role-based redirect)
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    role = request.user.role
    if role == 'Principal':
        return principal_dashboard(request)
    elif role == 'HR':
        return hr_dashboard(request)
    elif role == 'Teacher':
        return teacher_dashboard(request)
    else:
        return student_dashboard(request)


# ─────────────────────────────────────────────
# PRINCIPAL VIEWS
# ─────────────────────────────────────────────

@login_required
@role_required('Principal')
def principal_dashboard(request):
    pending_leaves = LeaveApplication.objects.filter(status='Pending').count()
    generated_slips = SalarySlip.objects.filter(status='Generated').count()
    total_teachers = TeacherProfile.objects.count()
    total_students = User.objects.filter(role='Student').count()
    context = {
        'pending_leaves': pending_leaves,
        'generated_slips': generated_slips,
        'total_teachers': total_teachers,
        'total_students': total_students,
    }
    return render(request, 'core/principal/dashboard.html', context)


@login_required
@role_required('Principal')
def principal_leave_requests(request):
    leaves = LeaveApplication.objects.filter(status='Pending')
    return render(request, 'core/principal/leave_requests.html', {'leaves': leaves})


@login_required
@role_required('Principal')
def principal_leave_action(request, pk, action):
    leave = get_object_or_404(LeaveApplication, pk=pk)
    if action == 'approve':
        leave.status = 'Approved'
        leave.save()
        messages.success(request, f'Leave for {leave.user.get_full_name()} approved.')
    elif action == 'reject':
        leave.status = 'Rejected'
        leave.save()
        messages.warning(request, f'Leave for {leave.user.get_full_name()} rejected.')
    return redirect('principal_leave_requests')


@login_required
@role_required('Principal')
def principal_salary_approval(request):
    slips = SalarySlip.objects.filter(status='Generated')
    return render(request, 'core/principal/salary_approval.html', {'slips': slips})


@login_required
@role_required('Principal')
def principal_approve_salary(request, pk):
    slip = get_object_or_404(SalarySlip, pk=pk)
    slip.status = 'Approved'
    slip.save()
    messages.success(request, f'Salary for {slip.teacher.user.get_full_name()} ({slip.month}) approved.')
    return redirect('principal_salary_approval')


@login_required
@role_required('Principal')
def principal_approve_all_salaries(request):
    count = SalarySlip.objects.filter(status='Generated').update(status='Approved')
    messages.success(request, f'{count} salary slip(s) approved.')
    return redirect('principal_salary_approval')


# ─────────────────────────────────────────────
# HR VIEWS
# ─────────────────────────────────────────────

@login_required
@role_required('HR')
def hr_dashboard(request):
    total_teachers = TeacherProfile.objects.count()
    total_classes = ClassGrade.objects.count()
    total_subjects = Subject.objects.count()
    pending_slips = SalarySlip.objects.filter(status='Generated').count()
    context = {
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_subjects': total_subjects,
        'pending_slips': pending_slips,
    }
    return render(request, 'core/hr/dashboard.html', context)


@login_required
@role_required('HR')
def hr_add_teacher(request):
    if request.method == 'POST':
        user_form = TeacherUserForm(request.POST)
        profile_form = TeacherProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'Teacher'
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, f'Teacher "{user.get_full_name()}" created successfully!')
            return redirect('dashboard')
    else:
        user_form = TeacherUserForm()
        profile_form = TeacherProfileForm()
    return render(request, 'core/hr/add_teacher.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
@role_required('HR')
def hr_manage_classes(request):
    if request.method == 'POST':
        form = ClassGradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class added successfully!')
            return redirect('hr_manage_classes')
    else:
        form = ClassGradeForm()
    classes = ClassGrade.objects.all()
    return render(request, 'core/hr/manage_classes.html', {'form': form, 'classes': classes})


@login_required
@role_required('HR')
def hr_manage_subjects(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully!')
            return redirect('hr_manage_subjects')
    else:
        form = SubjectForm()
    subjects = Subject.objects.all()
    return render(request, 'core/hr/manage_subjects.html', {'form': form, 'subjects': subjects})


@login_required
@role_required('HR')
def hr_create_timetable(request):
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Timetable entry created!')
                return redirect('hr_create_timetable')
            except ValidationError as e:
                messages.error(request, str(e.message))
    else:
        form = TimetableForm()
    entries = Timetable.objects.all()[:20]
    return render(request, 'core/hr/create_timetable.html', {'form': form, 'entries': entries})


@login_required
@role_required('HR')
def hr_payroll(request):
    slips = SalarySlip.objects.all()
    teachers = TeacherProfile.objects.all()
    return render(request, 'core/hr/payroll.html', {'slips': slips, 'teachers': teachers})


@login_required
@role_required('HR')
def hr_generate_payroll(request):
    now = datetime.datetime.now()
    month_str = now.strftime('%B %Y')
    teachers = TeacherProfile.objects.all()
    created = 0
    for t in teachers:
        _, was_created = SalarySlip.objects.get_or_create(
            teacher=t, month=month_str,
            defaults={'amount': t.basic_salary, 'deductions': 0, 'bonus': 0}
        )
        if was_created:
            created += 1
    if created:
        messages.success(request, f'{created} salary slip(s) generated for {month_str}.')
    else:
        messages.info(request, f'Salary slips for {month_str} already exist.')
    return redirect('hr_payroll')


# ─────────────────────────────────────────────
# TEACHER VIEWS
# ─────────────────────────────────────────────

@login_required
@role_required('Teacher')
def teacher_dashboard(request):
    profile = get_object_or_404(TeacherProfile, user=request.user)
    today = datetime.datetime.now().strftime('%A')
    todays_classes = Timetable.objects.filter(teacher=profile, day=today)
    pending_leaves = LeaveApplication.objects.filter(user=request.user, status='Pending').count()
    context = {
        'profile': profile,
        'todays_classes': todays_classes,
        'pending_leaves': pending_leaves,
    }
    return render(request, 'core/teacher/dashboard.html', context)


@login_required
@role_required('Teacher')
def teacher_timetable(request):
    profile = get_object_or_404(TeacherProfile, user=request.user)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    timetable = {}
    for day in days:
        timetable[day] = Timetable.objects.filter(teacher=profile, day=day)
    return render(request, 'core/teacher/timetable.html', {'timetable': timetable, 'days': days})


@login_required
@role_required('Teacher')
def teacher_salary(request):
    profile = get_object_or_404(TeacherProfile, user=request.user)
    slips = SalarySlip.objects.filter(
        teacher=profile, status__in=['Approved', 'Paid']
    )
    return render(request, 'core/teacher/salary.html', {'slips': slips, 'profile': profile})


@login_required
@role_required('Teacher')
def teacher_apply_leave(request):
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user
            leave.save()
            messages.success(request, 'Leave application submitted!')
            return redirect('teacher_apply_leave')
    else:
        form = LeaveApplicationForm()
    my_leaves = LeaveApplication.objects.filter(user=request.user)
    return render(request, 'core/teacher/apply_leave.html', {'form': form, 'my_leaves': my_leaves})


# ─────────────────────────────────────────────
# STUDENT VIEW (basic placeholder)
# ─────────────────────────────────────────────

@login_required
@role_required('Student')
def student_dashboard(request):
    return render(request, 'core/student/dashboard.html')


@login_required
@role_required('HR')
def hr_print_timetable(request):
    classes = ClassGrade.objects.all()
    class_id = request.GET.get('class_id')
    if class_id:
        class_grade = ClassGrade.objects.filter(pk=class_id).first() or classes.first()
    else:
        class_grade = classes.first()

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # Full schedule with breaks inserted
    full_schedule = [
        {'label': '08:00 - 08:45', 'slot': '08:00-08:45'},
        {'label': '08:45 - 09:30', 'slot': '08:45-09:30'},
        {'label': '09:30 - 10:15', 'slot': '09:30-10:15'},
        {'label': '10:15 - 10:30', 'is_break': True, 'is_lunch': False},
        {'label': '10:30 - 11:15', 'slot': '10:30-11:15'},
        {'label': '11:15 - 12:00', 'slot': '11:15-12:00'},
        {'label': '12:00 - 12:45', 'slot': '12:00-12:45'},
        {'label': '12:45 - 01:30', 'is_break': True, 'is_lunch': True},
        {'label': '01:30 - 02:15', 'slot': '01:30-02:15'},
        {'label': '02:15 - 03:00', 'slot': '02:15-03:00'},
    ]

    entries = Timetable.objects.filter(class_grade=class_grade).select_related('subject', 'teacher__user')
    lookup = {}
    for e in entries:
        lookup[(e.day, e.time_slot)] = e

    schedule = []
    for item in full_schedule:
        if item.get('is_break'):
            schedule.append(item)
        else:
            cells = []
            for day in days:
                entry = lookup.get((day, item['slot']))
                if entry:
                    cells.append({'subject': entry.subject.name, 'teacher': entry.teacher.user.get_full_name()})
                else:
                    cells.append({'subject': None, 'teacher': None})
            schedule.append({'label': item['label'], 'cells': cells, 'is_break': False})

    context = {
        'class_grade': class_grade,
        'classes': classes,
        'days': days,
        'schedule': schedule,
        'generated_date': datetime.datetime.now().strftime('%d %b %Y'),
    }
    return render(request, 'core/hr/print_timetable.html', context)
