from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard (role-based router)
    path('', views.dashboard, name='dashboard'),

    # Principal
    path('principal/leave-requests/', views.principal_leave_requests, name='principal_leave_requests'),
    path('principal/leave/<int:pk>/<str:action>/', views.principal_leave_action, name='principal_leave_action'),
    path('principal/salary-approval/', views.principal_salary_approval, name='principal_salary_approval'),
    path('principal/approve-salary/<int:pk>/', views.principal_approve_salary, name='principal_approve_salary'),
    path('principal/approve-all-salaries/', views.principal_approve_all_salaries, name='principal_approve_all_salaries'),

    # HR
    path('hr/add-teacher/', views.hr_add_teacher, name='hr_add_teacher'),
    path('hr/classes/', views.hr_manage_classes, name='hr_manage_classes'),
    path('hr/subjects/', views.hr_manage_subjects, name='hr_manage_subjects'),
    path('hr/timetable/', views.hr_create_timetable, name='hr_create_timetable'),
    path('hr/timetable/print/', views.hr_print_timetable, name='hr_print_timetable'),
    path('hr/payroll/', views.hr_payroll, name='hr_payroll'),
    path('hr/generate-payroll/', views.hr_generate_payroll, name='hr_generate_payroll'),

    # Teacher
    path('teacher/timetable/', views.teacher_timetable, name='teacher_timetable'),
    path('teacher/salary/', views.teacher_salary, name='teacher_salary'),
    path('teacher/apply-leave/', views.teacher_apply_leave, name='teacher_apply_leave'),
    path('teacher/attendance/', views.teacher_mark_attendance, name='teacher_mark_attendance'),

    # HR — Fee Management
    path('hr/fees/', views.hr_fee_management, name='hr_fee_management'),
    path('hr/fees/collect/<int:challan_id>/', views.hr_collect_fee, name='hr_collect_fee'),
]
