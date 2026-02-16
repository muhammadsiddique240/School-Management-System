# School-Management-System 🎓

A comprehensive **School ERP System** built with Django, featuring role-based access control for Principal, HR, Teachers, and Students.

## 🚀 Features

### 🏆 Principal
- **Dashboard**: Overview of school stats (teachers, students, pending leaves).
- **Leave Management**: Approve or reject leave applications from staff.
- **Salary Approval**: Review and approve generated salary slips before payment.

### 💼 HR (Human Resources)
- **Staff Management**: Add new teachers with detailed profiles.
- **Academic Management**: Manage Classes and Subjects.
- **Timetable**: Create class schedules with conflict detection.
- **Payroll System**: Generate monthly salary slips for all staff.
- **Printable Reports**: Generate print-ready timetables with break periods.

### 📚 Teacher
- **My Schedule**: View personal weekly timetable.
- **Leave Application**: Apply for leave and track status.
- **Salary Slips**: View and download approved salary slips.

### 🎓 Student
- **Dashboard**: View announcements and basic profile info.
- *(Coming Soon)*: Fee status and Exam results.

---

## 🛠️ Tech Stack
- **Backend:** Django 4.2 (Python)
- **Database:** SQLite (Default) / PostgreSQL (Ready)
- **Frontend:** Bootstrap 5, FontAwesome, Google Fonts (Inter)
- **Styling:** Custom CSS with responsive design

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/muhammadsiddique240/School-Management-System.git
   cd School-Management-System
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django
   # Or if requirements.txt exists: pip install -r requirements.txt
   ```

4. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

5. **Seed Dummy Data (Optional)**
   Populate the database with realistic test data (Teachers, Students, Classes, Timetable, etc.):
   ```bash
   python manage.py seed_data
   ```
   *(Creates admin users: `principal`, `hr` with password `admin123`)*

6. **Run Server**
   ```bash
   python manage.py runserver
   ```
   Access the app at `http://127.0.0.1:8000/`.

---

## 📸 Screenshots

*(Add your screenshots here)*

---

## 🤝 Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License
This project is licensed under the MIT License.
