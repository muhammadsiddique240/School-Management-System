from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import StudentProfile, FeeStructure, FeeChallan
import datetime
import calendar

class Command(BaseCommand):
    help = 'Generates monthly fee challans for all active students'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        month_str = now.strftime('%B %Y')
        year_int = now.year
        month_int = now.month

        self.stdout.write(f"Generating fees for: {month_str}")

        students = StudentProfile.objects.select_related('class_grade').all()
        created_count = 0
        skipped_count = 0
        error_count = 0

        for student in students:
            # Check if challan already exists
            if FeeChallan.objects.filter(student=student, month=month_str).exists():
                skipped_count += 1
                continue

            # Get Fee Structure
            try:
                fee_structure = getattr(student.class_grade, 'fee_structure', None)
            except Exception:
                fee_structure = None

            if not fee_structure:
                self.stderr.write(f"Warning: No fee structure for {student} (Class: {student.class_grade})")
                error_count += 1
                continue

            # Calculate Due Date
            try:
                # Get last day of month to avoid invalid date (e.g., Feb 30)
                last_day = calendar.monthrange(year_int, month_int)[1]
                due_day = min(fee_structure.due_day, last_day) 
                due_date = datetime.date(year_int, month_int, due_day)
            except ValueError:
                due_date = datetime.date(year_int, month_int, 10) # Fallback

            # Create Challan
            try:
                challan = FeeChallan(
                    student=student,
                    month=month_str,
                    tuition_amount=fee_structure.monthly_tuition,
                    due_date=due_date,
                    status='Unpaid'
                )
                challan.save() # save() calculates total_amount
                created_count += 1
            except Exception as e:
                self.stderr.write(f"Error creating challan for {student}: {str(e)}")
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done! Created: {created_count}, Skipped: {skipped_count}, Errors: {error_count}"
        ))
