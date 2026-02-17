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

    # ── Fee Revenue Data ──
    from core.models import FeeChallan, DailyAttendance, StudentProfile, Result
    from django.db.models import Sum, Count, Q
    import json

    total_revenue = FeeChallan.objects.filter(status='Paid').aggregate(t=Sum('amount_paid'))['t'] or 0
    pending_fees = FeeChallan.objects.filter(status__in=['Unpaid', 'Overdue']).aggregate(t=Sum('total_amount'))['t'] or 0
    overdue_count = FeeChallan.objects.filter(status='Overdue').count()

    # ── Attendance Today ──
    today = datetime.datetime.now().date()
    today_att = DailyAttendance.objects.filter(date=today)
    today_present = today_att.filter(status='P').count()
    today_absent = today_att.filter(status='A').count()
    today_total = today_att.count()
    attendance_pct = round((today_present / today_total) * 100, 1) if today_total > 0 else 0

    # ── Attendance Trend (last 10 school days for chart) ──
    from django.db.models.functions import TruncDate
    att_trend = (
        DailyAttendance.objects
        .values('date')
        .annotate(
            present=Count('id', filter=Q(status='P')),
            absent=Count('id', filter=Q(status='A')),
            total=Count('id'),
        )
        .order_by('-date')[:10]
    )
    att_trend = list(reversed(list(att_trend)))
    att_labels = [d['date'].strftime('%d %b') for d in att_trend]
    att_present_data = [d['present'] for d in att_trend]
    att_absent_data = [d['absent'] for d in att_trend]

    # ── Fee Collection by Month (for chart) ──
    fee_months = FeeChallan.objects.values('month').annotate(
        collected=Sum('amount_paid'),
        total=Sum('total_amount'),
    ).order_by('month')
    fee_labels = [f['month'] for f in fee_months]
    fee_collected = [float(f['collected'] or 0) for f in fee_months]
    fee_total = [float(f['total'] or 0) for f in fee_months]

    # ── At-Risk Students (attendance < 75% or avg grade < 50%) ──
    at_risk_students = []
    for sp in StudentProfile.objects.select_related('user', 'class_grade').all()[:50]:
        att_records = DailyAttendance.objects.filter(student=sp)
        total_days = att_records.count()
        present_days = att_records.filter(status='P').count()
        att_rate = round((present_days / total_days) * 100, 1) if total_days > 0 else 100

        results = Result.objects.filter(student=sp)
        avg_marks = 0
        if results.exists():
            total_pct = sum(r.percentage for r in results)
            avg_marks = round(total_pct / results.count(), 1)

        risk_score = 0
        if att_rate < 75:
            risk_score += 40
        if avg_marks < 50:
            risk_score += 40
        if att_rate < 60:
            risk_score += 20

        if risk_score >= 40:
            at_risk_students.append({
                'name': sp.user.get_full_name(),
                'class': str(sp.class_grade),
                'attendance': att_rate,
                'avg_grade': avg_marks,
                'risk': 'High' if risk_score >= 60 else 'Medium',
            })

    context = {
        'pending_leaves': pending_leaves,
        'generated_slips': generated_slips,
        'total_teachers': total_teachers,
        'total_students': total_students,
        # Fee
        'total_revenue': total_revenue,
        'pending_fees': pending_fees,
        'overdue_count': overdue_count,
        # Attendance
        'attendance_pct': attendance_pct,
        'today_present': today_present,
        'today_absent': today_absent,
        # Charts
        'att_labels': json.dumps(att_labels),
        'att_present_data': json.dumps(att_present_data),
        'att_absent_data': json.dumps(att_absent_data),
        'fee_labels': json.dumps(fee_labels),
        'fee_collected': json.dumps(fee_collected),
        'fee_total': json.dumps(fee_total),
        # AI
        'at_risk_students': at_risk_students,
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
    from core.models import StudentProfile, FeeChallan, DailyAttendance, Result, ExamType
    from django.db.models import Q
    import json

    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return render(request, 'core/student/dashboard.html', {'no_profile': True})

    # Fee summary
    challans = FeeChallan.objects.filter(student=profile)
    unpaid = challans.filter(status__in=['Unpaid', 'Overdue'])

    # Attendance summary
    att_records = DailyAttendance.objects.filter(student=profile)
    total_days = att_records.count()
    present_days = att_records.filter(status='P').count()
    absent_days = att_records.filter(status='A').count()
    att_pct = round((present_days / total_days) * 100, 1) if total_days > 0 else 0

    # Results
    results = Result.objects.filter(student=profile).select_related('subject', 'exam_type')
    subjects_map = {}
    for r in results:
        key = r.subject.name
        if key not in subjects_map:
            subjects_map[key] = {}
        subjects_map[key][r.exam_type.name] = {
            'marks': float(r.marks_obtained),
            'max': r.exam_type.max_marks,
            'pct': r.percentage,
            'grade': r.grade,
            'weighted': r.weighted_score,
        }

    # Chart data
    subject_labels = list(subjects_map.keys())
    midterm_data = [float(subjects_map[s].get('Midterm', {}).get('pct', 0)) for s in subject_labels]
    final_data = [float(subjects_map[s].get('Final', {}).get('pct', 0)) for s in subject_labels]

    context = {
        'profile': profile,
        'challans': challans[:5],
        'unpaid_count': unpaid.count(),
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'att_pct': att_pct,
        'subjects_map': subjects_map,
        'subject_labels': json.dumps(subject_labels),
        'midterm_data': json.dumps(midterm_data),
        'final_data': json.dumps(final_data),
    }
    return render(request, 'core/student/dashboard.html', context)


# ─────────────────────────────────────────────
# ATTENDANCE — Bulk Mark (for Teachers)
# ─────────────────────────────────────────────

@login_required
@role_required('Teacher')
def teacher_mark_attendance(request):
    from core.models import StudentProfile, DailyAttendance
    classes = ClassGrade.objects.all()
    class_id = request.GET.get('class_id') or request.POST.get('class_id')
    selected_class = None
    students = []
    today = datetime.datetime.now().date()

    if class_id:
        selected_class = ClassGrade.objects.filter(pk=class_id).first()
        if selected_class:
            students = StudentProfile.objects.filter(class_grade=selected_class).select_related('user')

    if request.method == 'POST' and selected_class:
        saved = 0
        for sp in students:
            status = request.POST.get(f'att_{sp.id}', 'P')
            DailyAttendance.objects.update_or_create(
                student=sp, date=today,
                defaults={
                    'status': status,
                    'marked_by': request.user,
                }
            )
            saved += 1
        messages.success(request, f'Attendance saved for {saved} students in {selected_class}!')
        return redirect(f'/teacher/attendance/?class_id={class_id}')

    # Check which are already marked
    existing = {}
    if selected_class:
        for att in DailyAttendance.objects.filter(student__class_grade=selected_class, date=today):
            existing[att.student_id] = att.status

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'students': students,
        'today': today,
        'existing': existing,
    }
    return render(request, 'core/teacher/mark_attendance.html', context)


# ─────────────────────────────────────────────
# HR — Fee Management
# ─────────────────────────────────────────────

@login_required
@role_required('HR')
def hr_fee_management(request):
    from core.models import FeeChallan, FeeStructure, StudentProfile
    from django.db.models import Sum, F
    from django.core.paginator import Paginator

    challans = FeeChallan.objects.select_related('student__user', 'student__class_grade').all()

    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        challans = challans.filter(status=status_filter)

    # Annotate balance on each challan
    challans = challans.annotate(balance=F('total_amount') - F('amount_paid'))

    total_collected = FeeChallan.objects.aggregate(t=Sum('amount_paid'))['t'] or 0
    total_pending = challans.exclude(status='Paid').aggregate(t=Sum('balance'))['t'] or 0

    # Pagination
    paginator = Paginator(challans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'challans': page_obj,
        'page_obj': page_obj,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'status_filter': status_filter,
    }
    return render(request, 'core/hr/fee_management.html', context)


@login_required
@role_required('HR')
def hr_collect_fee(request, challan_id):
    from core.models import FeeChallan
    challan = get_object_or_404(FeeChallan, pk=challan_id)
    if request.method == 'POST':
        amount = request.POST.get('amount', 0)
        try:
            amount = float(amount)
        except ValueError:
            amount = 0
        challan.amount_paid = challan.amount_paid + int(amount)
        challan.paid_date = datetime.datetime.now().date()
        challan.save()
        messages.success(request, f'Rs. {amount:.0f} collected from {challan.student.user.get_full_name()}.')
    return redirect('hr_fee_management')


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
