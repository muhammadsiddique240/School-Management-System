import datetime
import random
from django.core.management.base import BaseCommand
from core.models import (
    User, ClassGrade, Subject, TeacherProfile,
    Timetable, SalarySlip, LeaveApplication
)


class Command(BaseCommand):
    help = 'Seed the database with realistic dummy data for all roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🌱 Seeding database...'))

        # ── USERS ──────────────────────────────────────────
        principal, _ = User.objects.get_or_create(
            username='principal',
            defaults={
                'first_name': 'Dr. Ahmed',
                'last_name': 'Khan',
                'email': 'principal@edusmart.pk',
                'role': 'Principal',
                'is_staff': True,
            }
        )
        principal.set_password('admin123')
        principal.save()
        self.stdout.write(f'  ✅ Principal: {principal}')

        hr, _ = User.objects.get_or_create(
            username='hr',
            defaults={
                'first_name': 'Ayesha',
                'last_name': 'Malik',
                'email': 'hr@edusmart.pk',
                'role': 'HR',
                'is_staff': True,
            }
        )
        hr.set_password('admin123')
        hr.save()
        self.stdout.write(f'  ✅ HR: {hr}')

        # ── TEACHERS ───────────────────────────────────────
        teachers_data = [
            # Original 3
            {'username': 'teacher1', 'first_name': 'Ali', 'last_name': 'Raza',
             'email': 'ali@edusmart.pk', 'designation': 'Senior Lecturer',
             'salary': 75000, 'joining': datetime.date(2022, 3, 15)},
            {'username': 'teacher2', 'first_name': 'Fatima', 'last_name': 'Noor',
             'email': 'fatima@edusmart.pk', 'designation': 'Lecturer',
             'salary': 60000, 'joining': datetime.date(2023, 8, 1)},
            {'username': 'teacher3', 'first_name': 'Hassan', 'last_name': 'Iqbal',
             'email': 'hassan@edusmart.pk', 'designation': 'Assistant Professor',
             'salary': 90000, 'joining': datetime.date(2021, 1, 10)},
            # New Teachers
            {'username': 'teacher4', 'first_name': 'Zarah', 'last_name': 'Sheikh',
             'email': 'zarah@edusmart.pk', 'designation': 'Lecturer',
             'salary': 55000, 'joining': datetime.date(2023, 11, 5)},
            {'username': 'teacher5', 'first_name': 'Bilal', 'last_name': 'Ahmed',
             'email': 'bilal@edusmart.pk', 'designation': 'Senior Lecturer',
             'salary': 72000, 'joining': datetime.date(2022, 6, 20)},
            {'username': 'teacher6', 'first_name': 'Sana', 'last_name': 'Mir',
             'email': 'sana@edusmart.pk', 'designation': 'Lecturer',
             'salary': 58000, 'joining': datetime.date(2024, 1, 15)},
            {'username': 'teacher7', 'first_name': 'Usama', 'last_name': 'Khan',
             'email': 'usama@edusmart.pk', 'designation': 'Lab Instructor',
             'salary': 45000, 'joining': datetime.date(2023, 9, 1)},
            {'username': 'teacher8', 'first_name': 'Maria', 'last_name': 'Yousaf',
             'email': 'maria@edusmart.pk', 'designation': 'Lecturer',
             'salary': 62000, 'joining': datetime.date(2023, 2, 28)},
        ]

        teacher_profiles = []
        for td in teachers_data:
            user, _ = User.objects.get_or_create(
                username=td['username'],
                defaults={
                    'first_name': td['first_name'],
                    'last_name': td['last_name'],
                    'email': td['email'],
                    'role': 'Teacher',
                }
            )
            user.set_password('admin123')
            user.save()
            profile, _ = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    'designation': td['designation'],
                    'basic_salary': td['salary'],
                    'joining_date': td['joining'],
                }
            )
            teacher_profiles.append(profile)
            self.stdout.write(f'  ✅ Teacher: {user}')

        # ── STUDENTS ───────────────────────────────────────
        students_names = [
            ('Zain', 'Ahmed'), ('Sara', 'Bilal'), ('Usman', 'Tariq'), ('Hira', 'Shah'), ('Omar', 'Farooq'),
            ('Amina', 'Khan'), ('Bilal', 'Saeed'), ('Dania', 'Imran'), ('Fahad', 'Mustafa'), ('Gia', 'Rasool'),
            ('Hamza', 'Ali'), ('Iman', 'Khalid'), ('Junaid', 'Jamshed'), ('Kiran', 'Malik'), ('Laila', 'Zafar'),
            ('Musa', 'Riaz'), ('Nida', 'Yasir'), ('Osman', 'Ghani'), ('Parveen', 'Shakir'), ('Qasim', 'Ali'),
            ('Rida', 'Ishtiaq'), ('Saad', 'Rafique'), ('Taha', 'Shahid'), ('Uzma', 'Gillani'), ('Waleed', 'Hassan'),
        ]
        
        for i, (fname, lname) in enumerate(students_names, 1):
            username = f'student{i}'
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': fname,
                    'last_name': lname,
                    'email': f"{username}@edusmart.pk",
                    'role': 'Student',
                }
            )
            user.set_password('admin123')
            user.save()
            if i <= 5: # Only log first 5 to avoid spam
                self.stdout.write(f'  ✅ Student: {user}')
        self.stdout.write(f'  ... and {len(students_names)-5} more students.')

        # ── CLASSES ────────────────────────────────────────
        classes_data = [
            ('Class 8', 'A'), ('Class 8', 'B'),
            ('Class 9', 'A'), ('Class 9', 'B'),
            ('Class 10', 'A'), ('Class 10', 'B'),
        ]
        classes = []
        for name, section in classes_data:
            cls, _ = ClassGrade.objects.get_or_create(name=name, section=section)
            classes.append(cls)
            self.stdout.write(f'  ✅ Class: {cls}')

        # ── SUBJECTS ───────────────────────────────────────
        subjects_map = {
            'Mathematics': classes, # All classes
            'English': classes,     # All classes
            'Physics': [c for c in classes if '9' in c.name or '10' in c.name],
            'Chemistry': [c for c in classes if '9' in c.name or '10' in c.name],
            'Biology': [c for c in classes if '9' in c.name or '10' in c.name],
            'Science': [c for c in classes if '8' in c.name],
            'History': [c for c in classes if '8' in c.name],
            'Computer Science': [c for c in classes if 'A' in c.section], # Only section A
            'Islamiat': classes,
        }
        all_subjects = []
        for subj_name, cls_list in subjects_map.items():
            for cls in cls_list:
                subj, _ = Subject.objects.get_or_create(name=subj_name, class_grade=cls)
                all_subjects.append(subj)
        self.stdout.write(f'  ✅ Created {len(all_subjects)} subjects across all classes.')

        # ── TIMETABLE ──────────────────────────────────────
        # Use simple round-robin to fill slots
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        time_slots = [
            '08:00-08:45', '08:45-09:30', '09:30-10:15', 
            '10:30-11:15', '11:15-12:00', '12:00-12:45',
            '01:30-02:15', '02:15-03:00'
        ]
        
        count = 0
        # Try to fill 3 slots per day per class
        for day in days:
            for cls in classes:
                # Get subjects for this class
                class_subjects = Subject.objects.filter(class_grade=cls)
                if not class_subjects.exists():
                    continue
                
                # Assign 4 periods per day
                for i in range(4): 
                    slot = time_slots[i + (1 if i > 2 else 0)] # Skip break/lunch roughly
                    subj = class_subjects[i % len(class_subjects)]
                    
                    # Round robin teachers (basic conflict avoidance by using teacher index based on subject char length)
                    t_idx = (len(subj.name) + i) % len(teacher_profiles)
                    teacher = teacher_profiles[t_idx]
                    
                    # Check basic conflict
                    if not Timetable.objects.filter(teacher=teacher, day=day, time_slot=slot).exists():
                         Timetable.objects.get_or_create(
                            class_grade=cls, subject=subj, teacher=teacher,
                            day=day, time_slot=slot,
                        )
                         count += 1
        
        self.stdout.write(f'  ✅ Generated {count} timetable entries.')

        # ── SALARY SLIPS ───────────────────────────────────
        months = ['January 2026', 'February 2026']
        for month in months:
            status = 'Paid' if 'Jan' in month else 'Generated'
            for profile in teacher_profiles:
                SalarySlip.objects.get_or_create(
                    teacher=profile, month=month,
                    defaults={
                        'amount': profile.basic_salary,
                        'deductions': random.choice([0, 1000, 2000, 500]),
                        'bonus': random.choice([0, 0, 5000, 2000]),
                        'status': status
                    }
                )
        self.stdout.write(f'  ✅ Generated salary slips for Jan & Feb 2026.')

        # ── LEAVE APPLICATIONS ─────────────────────────────
        reasons = [
            'Family wedding', 'Medical emergency', 'Personal work', 'Sick leave', 
            'Urgent piece of work', 'Attending conference', 'Child sick'
        ]
        statuses = ['Approved', 'Rejected', 'Pending']
        
        for _ in range(15): # Create 15 random leaves
            user = random.choice(teacher_profiles).user
            start_day = random.randint(1, 25)
            LeaveApplication.objects.get_or_create(
                user=user,
                from_date=datetime.date(2026, 2, start_day),
                to_date=datetime.date(2026, 2, start_day + random.randint(0, 2)),
                defaults={
                    'reason': random.choice(reasons),
                    'status': random.choice(statuses)
                }
            )
        self.stdout.write(f'  ✅ Created 15 random leave applications.')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✨ Database seeded successfully with EXTENDED data!'))
