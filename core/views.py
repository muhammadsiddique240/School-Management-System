import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import (
    User, ClassGrade, Subject, TeacherProfile,
    Timetable, SalarySlip, LeaveApplication,
    FeeChallan, DailyAttendance, StudentProfile, Result
)
from django.db.models import Sum, Count, Q
from .utils_ai import calculate_student_risk
import json
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

    # ── Fee Revenue Data (Matches HR logic) ──
    from django.db.models import Sum, F
    all_challans = FeeChallan.objects.all()
    total_revenue = all_challans.aggregate(t=Sum('amount_paid'))['t'] or 0
    pending_fees = all_challans.exclude(status='Paid').annotate(
        balance=F('total_amount') - F('amount_paid')
    ).aggregate(t=Sum('balance'))['t'] or 0
    overdue_count = all_challans.filter(status='Overdue').count()

    # ── Attendance Today ──
    today = datetime.datetime.now().date()
    today_att = DailyAttendance.objects.filter(date=today)
    today_present = today_att.filter(status='P').count()
    today_absent = today_att.filter(status='A').count()
    today_total = today_att.count()
    attendance_pct = round((today_present / today_total) * 100, 1) if today_total > 0 else 0

    # ── Attendance Trend (last 10 school days) ──
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

    # ── Fee Collection by Month ──
    fee_months = FeeChallan.objects.values('month').annotate(
        collected=Sum('amount_paid'),
        total=Sum('total_amount'),
    ).order_by('month')
    fee_labels = [f['month'] for f in fee_months]
    fee_collected = [float(f['collected'] or 0) for f in fee_months]
    fee_total = [float(f['total'] or 0) for f in fee_months]

    # ── At-Risk Students (attendance < 75% or avg grade < 50%) ──
    # AI Driven Insights
    at_risk_students = []
    
    # Analyze all students for risk
    all_students = StudentProfile.objects.select_related('user', 'class_grade')
    for sp in all_students:
        risk_level, risk_factors = calculate_student_risk(sp)
        if risk_level == 'High':
            at_risk_students.append({
                'name': sp.user.get_full_name(),
                'class': str(sp.class_grade),
                'risk': risk_level,
                'factors': risk_factors
            })


    # ── Fallback for Empty Data (Demo Mode) ──
    if not att_labels:
        att_labels = ["10 Feb", "11 Feb", "12 Feb", "13 Feb", "14 Feb", "15 Feb", "16 Feb", "17 Feb"]
        att_present_data = [20, 22, 21, 23, 19, 24, 25, 23]
        att_absent_data = [2, 1, 3, 0, 4, 1, 0, 2]
    
    if not fee_labels:
        fee_labels = ["Jan", "Feb", "Mar"]
        fee_collected = [45000, 32000, 0]
        fee_total = [50000, 50000, 50000]

    # Ensure Students count is at least something if profiles exist but roles are mismatched
    if total_students == 0 and StudentProfile.objects.exists():
        total_students = StudentProfile.objects.count()

    context = {
        'pending_leaves': pending_leaves,
        'generated_slips': generated_slips,
        'total_teachers': total_teachers,
        'total_students': total_students,
        # Fee
        'total_revenue': total_revenue or 0,
        'pending_fees': pending_fees or 0,
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
    
    
@login_required
@role_required('Teacher')
def teacher_enter_results(request):
    from core.models import StudentProfile, Subject, ExamType, Result
    classes = ClassGrade.objects.all()
    subjects = Subject.objects.all()
    exam_types = ExamType.objects.all()

    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')
    exam_type_id = request.GET.get('exam_type_id')

    selected_class = None
    selected_subject = None
    selected_exam_type = None
    students_data = []

    if class_id and subject_id and exam_type_id:
        selected_class = ClassGrade.objects.filter(pk=class_id).first()
        selected_subject = Subject.objects.filter(pk=subject_id).first()
        selected_exam_type = ExamType.objects.filter(pk=exam_type_id).first()
        
        if selected_class and selected_subject and selected_exam_type:
            students = StudentProfile.objects.filter(class_grade=selected_class).select_related('user')
            
            # Fetch existing results
            existing_results_qs = Result.objects.filter(
                student__class_grade=selected_class,
                subject=selected_subject,
                exam_type=selected_exam_type
            )
            existing_results = {r.student_id: r for r in existing_results_qs}
            
            for s in students:
                res = existing_results.get(s.id)
                students_data.append({
                    'student': s,
                    'result': res,
                    'marks': res.marks_obtained if res else ''
                })

            if request.method == 'POST':
                saved_count = 0
                for item in students_data:
                    student = item['student']
                    marks = request.POST.get(f'marks_{student.id}')
                    
                    if marks:
                        try:
                            Result.objects.update_or_create(
                                student=student,
                                subject=selected_subject,
                                exam_type=selected_exam_type,
                                defaults={
                                    'marks_obtained': float(marks),
                                    'entered_by': request.user
                                }
                            )
                            saved_count += 1
                        except ValueError:
                            pass # Skip invalid input
                
                messages.success(request, f'Results saved for {saved_count} students!')
                # Keep the selection
                return redirect(f'{request.path}?class_id={class_id}&subject_id={subject_id}&exam_type_id={exam_type_id}')

    context = {
        'classes': classes,
        'subjects': subjects,
        'exam_types': exam_types,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'selected_exam_type': selected_exam_type,
        'students_data': students_data,
        'class_id': int(class_id) if class_id else None,
        'subject_id': int(subject_id) if subject_id else None,
        'exam_type_id': int(exam_type_id) if exam_type_id else None,
    }
    return render(request, 'core/teacher/enter_results.html', context)


@login_required
@role_required('Student')
def student_download_report_card(request):
    from core.models import Result
    from core.utils_pdf import render_to_pdf
    
    student = request.user.student_profile
    # Fetch all results
    results = Result.objects.filter(student=student).select_related('subject', 'exam_type')

    # Organize by Subject -> ExamType
    subjects_map = {}
    for r in results:
        sub_name = r.subject.name
        if sub_name not in subjects_map:
            subjects_map[sub_name] = {'weighted_total': 0, 'grade': 'F'}
        
        subjects_map[sub_name][r.exam_type.name] = {
            'marks': r.marks_obtained,
            'max': r.exam_type.max_marks,
            'weightage': r.exam_type.weightage
        }
        # Add to weighted total
        subjects_map[sub_name]['weighted_total'] += float(r.weighted_score)

    # Calculate final grades
    for sub, data in subjects_map.items():
        total = data['weighted_total']
        if total >= 90: data['grade'] = 'A+'
        elif total >= 80: data['grade'] = 'A'
        elif total >= 70: data['grade'] = 'B'
        elif total >= 60: data['grade'] = 'C'
        elif total >= 50: data['grade'] = 'D'
        else: data['grade'] = 'F'
        
        # Round for display
        data['weighted_total'] = round(total, 2)

    context = {
        'student': student,
        'results': subjects_map,
    }
    
    pdf = render_to_pdf('core/student/report_card_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Report_Card_{student.user.username}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error rendering PDF", status=400)


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
        from core.utils import send_sms
        saved = 0
        sms_sent = 0
        for sp in students:
            status = request.POST.get(f'att_{sp.id}', 'P')
            obj, created = DailyAttendance.objects.update_or_create(
                student=sp, date=today,
                defaults={
                    'status': status,
                    'marked_by': request.user,
                }
            )
            saved += 1
            
            # Send SMS if Absent and was not already Absent (or is new record)
            # Simplified logic: If status is 'A', send SMS. Using a flag to avoid spamming in real app would be better.
            # Here, we send every time 'A' is submitted for demo purposes.
            if status == 'A' and sp.parent_phone:
                msg = f"Dear Parent, your child {sp.user.get_full_name()} is absent today ({today.strftime('%d %b %Y')}). - EduSmart"
                if send_sms(sp.parent_phone, msg):
                    sms_sent += 1
                    
        messages.success(request, f'Attendance saved for {saved} students! {sms_sent} SMS sent.')
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
def hr_generate_fees(request):
    from django.core.management import call_command
    import io
    
    out = io.StringIO()
    try:
        call_command('generate_fees', stdout=out)
        result = out.getvalue()
        if "Errors" in result and "Errors: 0" not in result:
             messages.warning(request, f'Fees generated with some warnings: {result}')
        else:
             messages.success(request, f'Fees generated successfully! {result}')
    except Exception as e:
        messages.error(request, f'Error generating fees: {str(e)}')
    
    return redirect('hr_fee_management')


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
