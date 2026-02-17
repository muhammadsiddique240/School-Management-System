from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta
from core.models import DailyAttendance, Result, FeeChallan, StudentProfile

def calculate_student_risk(student):
    """
    Analyzes student data to determine risk level.
    Returns: (risk_level, risk_factors_list)
    """
    risk_factors = []
    
    # 1. Attendance Analysis (Last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    attendance_qs = DailyAttendance.objects.filter(student=student, date__gte=thirty_days_ago)
    total_days = attendance_qs.count()
    if total_days > 0:
        present = attendance_qs.filter(status='Present').count()
        att_pct = (present / total_days) * 100
        if att_pct < 75:
            risk_factors.append(f"Low Attendance ({int(att_pct)}%)")
    
    # 2. Academic Performance
    results = Result.objects.filter(student=student)
    if results.exists():
        avg_score = results.aggregate(avg=Avg('marks_obtained'))['avg'] or 0
        # Assuming max marks per exam is roughly 100 for normalization, or checking failing grades
        # A clearer heuristic: count 'F' grades
        failed_exams = [r for r in results if r.grade == 'F']
        if len(failed_exams) >= 2:
            risk_factors.append(f"Failed {len(failed_exams)} recent exams")
        elif avg_score < 50:
             risk_factors.append(f"Low Average Score ({int(avg_score)})")

    # 3. Financial Status
    unpaid_challans = FeeChallan.objects.filter(
        student=student, 
        status__in=['Unpaid', 'Overdue']
    ).count()
    if unpaid_challans >= 2:
        risk_factors.append(f"{unpaid_challans} Unpaid Feebills")

    # Determine Risk Level
    if len(risk_factors) >= 2:
        risk_level = 'High'
    elif len(risk_factors) == 1:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'

    return risk_level, risk_factors
