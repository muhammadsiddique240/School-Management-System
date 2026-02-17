"""
Seed command for the AI-Powered ERP features:
  - StudentProfiles (linked to existing students)
  - FeeStructure (per class)
  - FeeChallan (monthly invoices)
  - DailyAttendance (30 days of history)
  - ExamType (Midterm + Final)
  - Result (marks for every student × subject × exam)
"""
import datetime
import random
from django.core.management.base import BaseCommand
from core.models import (
    User, ClassGrade, Subject, StudentProfile,
    FeeStructure, FeeChallan, DailyAttendance,
    ExamType, Result
)


class Command(BaseCommand):
    help = 'Seed AI-ERP data: student profiles, fees, attendance, exams & results'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🧠 Seeding AI-ERP data...'))

        students = User.objects.filter(role='Student')
        classes = ClassGrade.objects.all()
        hr_user = User.objects.filter(role='HR').first()
        teacher_users = User.objects.filter(role='Teacher')

        if not students.exists():
            self.stdout.write(self.style.ERROR('No students found! Run seed_data first.'))
            return

        # ═══════════════════════════════════════════════════════
        #  1. STUDENT PROFILES
        # ═══════════════════════════════════════════════════════
        parent_names = [
            'Ahmed Khan', 'Bilal Saeed', 'Tariq Shah', 'Farooq Hussain', 'Imran Malik',
            'Noor Muhammad', 'Rashid Ali', 'Saleem Akhtar', 'Waqar Ahmad', 'Zahid Iqbal',
            'Arif Hussain', 'Bashir Khan', 'Daniyal Shah', 'Ehsan Malik', 'Faisal Raza',
            'Ghulam Abbas', 'Habib Khan', 'Irfan Ahmed', 'Javed Akhtar', 'Khalid Mehmood',
            'Latif Shah', 'Mushtaq Ali', 'Nasir Hussain', 'Pervaiz Iqbal', 'Riaz Ahmad',
        ]

        profiles = []
        for i, student in enumerate(students):
            cls = classes[i % len(classes)]
            profile, created = StudentProfile.objects.get_or_create(
                user=student,
                defaults={
                    'class_grade': cls,
                    'roll_number': f'{cls.name[-1]}{cls.section}-{str(i+1).zfill(3)}',
                    'parent_name': parent_names[i % len(parent_names)],
                    'parent_phone': f'0300-{random.randint(1000000, 9999999)}',
                    'parent_email': f'parent{i+1}@edusmart.pk',
                    'date_of_birth': datetime.date(2010 + random.randint(0, 3),
                                                   random.randint(1, 12),
                                                   random.randint(1, 28)),
                }
            )
            profiles.append(profile)
        self.stdout.write(f'  ✅ Created {len(profiles)} student profiles.')

        # ═══════════════════════════════════════════════════════
        #  2. FEE STRUCTURES
        # ═══════════════════════════════════════════════════════
        fee_map = {
            '8': 4000, '9': 5000, '10': 6000,
        }
        for cls in classes:
            grade_num = ''.join(filter(str.isdigit, cls.name))
            tuition = fee_map.get(grade_num, 5000)
            FeeStructure.objects.get_or_create(
                class_grade=cls,
                defaults={
                    'monthly_tuition': tuition,
                    'admission_fee': tuition * 2,
                    'exam_fee': 2000,
                    'late_fine_per_day': 50,
                    'due_day': 10,
                }
            )
        self.stdout.write(f'  ✅ Fee structures set for {classes.count()} classes.')

        # ═══════════════════════════════════════════════════════
        #  3. FEE CHALLANS (Jan & Feb 2026)
        # ═══════════════════════════════════════════════════════
        months_data = [
            ('January 2026', datetime.date(2026, 1, 10), True),
            ('February 2026', datetime.date(2026, 2, 10), False),
        ]
        challan_count = 0
        for month_name, due_date, is_old_month in months_data:
            for profile in profiles:
                try:
                    fee = FeeStructure.objects.get(class_grade=profile.class_grade)
                except FeeStructure.DoesNotExist:
                    continue
                concession = random.choice([0, 0, 0, 500, 1000])  # 40% have no concession
                if is_old_month:
                    # January: most paid, some overdue
                    status = random.choices(['Paid', 'Overdue'], weights=[85, 15])[0]
                    paid = fee.monthly_tuition - concession if status == 'Paid' else 0
                    fine = 50 * random.randint(1, 10) if status == 'Overdue' else 0
                else:
                    # February: mix
                    status = random.choices(['Unpaid', 'Paid', 'Partial'], weights=[50, 30, 20])[0]
                    base = fee.monthly_tuition - concession
                    if status == 'Paid':
                        paid = base
                    elif status == 'Partial':
                        paid = base // 2
                    else:
                        paid = 0
                    fine = 0

                FeeChallan.objects.get_or_create(
                    student=profile, month=month_name,
                    defaults={
                        'tuition_amount': fee.monthly_tuition,
                        'concession': concession,
                        'fine': fine,
                        'amount_paid': paid,
                        'status': status,
                        'due_date': due_date,
                        'paid_date': due_date - datetime.timedelta(days=random.randint(1, 5)) if status == 'Paid' else None,
                    }
                )
                challan_count += 1
        self.stdout.write(f'  ✅ Generated {challan_count} fee challans.')

        # ═══════════════════════════════════════════════════════
        #  4. DAILY ATTENDANCE (Last 20 school days)
        # ═══════════════════════════════════════════════════════
        today = datetime.date(2026, 2, 17)  # Fixed date for reproducibility
        school_days = []
        d = today
        while len(school_days) < 20:
            if d.weekday() < 5:  # Mon-Fri
                school_days.append(d)
            d -= datetime.timedelta(days=1)
        school_days.reverse()

        att_count = 0
        for profile in profiles:
            for day in school_days:
                # 90% present, 5% absent, 3% late, 2% excused
                status = random.choices(
                    ['P', 'A', 'L', 'E'],
                    weights=[90, 5, 3, 2]
                )[0]
                DailyAttendance.objects.get_or_create(
                    student=profile, date=day,
                    defaults={
                        'status': status,
                        'marked_by': random.choice(teacher_users) if teacher_users.exists() else hr_user,
                        'sms_sent': status == 'A',  # SMS sent for absences
                    }
                )
                att_count += 1
        self.stdout.write(f'  ✅ Generated {att_count} attendance records ({len(school_days)} days).')

        # ═══════════════════════════════════════════════════════
        #  5. EXAM TYPES
        # ═══════════════════════════════════════════════════════
        midterm, _ = ExamType.objects.get_or_create(
            name='Midterm', defaults={'weightage': 20.00, 'max_marks': 50, 'academic_year': '2026'}
        )
        final, _ = ExamType.objects.get_or_create(
            name='Final', defaults={'weightage': 80.00, 'max_marks': 100, 'academic_year': '2026'}
        )
        self.stdout.write('  ✅ Exam types: Midterm (20%) & Final (80%).')

        # ═══════════════════════════════════════════════════════
        #  6. RESULTS
        # ═══════════════════════════════════════════════════════
        result_count = 0
        for profile in profiles:
            if not profile.class_grade:
                continue
            class_subjects = Subject.objects.filter(class_grade=profile.class_grade)
            for subject in class_subjects:
                # Midterm results
                mid_marks = round(random.gauss(35, 8), 1)  # Mean 35/50
                mid_marks = max(10, min(50, mid_marks))
                Result.objects.get_or_create(
                    student=profile, subject=subject, exam_type=midterm,
                    defaults={
                        'marks_obtained': mid_marks,
                        'entered_by': random.choice(teacher_users) if teacher_users.exists() else hr_user,
                    }
                )
                result_count += 1

                # Final results (correlated with midterm)
                base_final = (mid_marks / 50) * 100  # Scale to /100
                final_marks = round(base_final + random.gauss(0, 10), 1)
                final_marks = max(15, min(100, final_marks))
                Result.objects.get_or_create(
                    student=profile, subject=subject, exam_type=final,
                    defaults={
                        'marks_obtained': final_marks,
                        'entered_by': random.choice(teacher_users) if teacher_users.exists() else hr_user,
                    }
                )
                result_count += 1

        self.stdout.write(f'  ✅ Generated {result_count} exam results.')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✨ AI-ERP data seeded successfully!'))
        self.stdout.write(self.style.WARNING('Summary:'))
        self.stdout.write(f'  Student Profiles: {StudentProfile.objects.count()}')
        self.stdout.write(f'  Fee Structures:   {FeeStructure.objects.count()}')
        self.stdout.write(f'  Fee Challans:     {FeeChallan.objects.count()}')
        self.stdout.write(f'  Attendance:       {DailyAttendance.objects.count()} records')
        self.stdout.write(f'  Exam Types:       {ExamType.objects.count()}')
        self.stdout.write(f'  Results:          {Result.objects.count()}')
