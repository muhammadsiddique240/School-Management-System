# PythonAnywhere Deployment Guide (Full Steps) 🐍

PythonAnywhere Django projects ke liye best hai kyunki ye setup mein asaan hai aur SQLite database ko support karta hai.

### 1. Account Banayein
[pythonanywhere.com](https://www.pythonanywhere.com/) par jayein aur ek **Free Beginner Account** banayein.

### 2. Code GitHub se Le Kar Ayein
PythonAnywhere dashboard par **Consoles** tab mein jayein aur **Bash** par click karein. Wahan ye commands chalaein:
```bash
git clone https://github.com/muhammadsiddique240/School-Management-System.git
cd School-Management-System
```

### 3. Virtual Environment aur Django Setup
Bash console mein hi rehte hue:
```bash
mkvirtualenv --python=python3.10 my-env  # Environment banayein
pip install django django-bootstrap5 whitenoise gunicorn # Zaruri cheezein install karein
```

### 4. Web App Configure Karein
1. Dashboard mein **Web** tab par jayein.
2. **Add a new web app** par click karein.
3. **Manual Configuration** select karein (Django option mat chuna kyunki hum model customize kar chuke hain).
4. **Python 3.10** select karein.

### 5. Paths aur Environment Set Karein
Web tab ke andar:
- **Source code**: `/home/yourusername/School-Management-System`
- **Working directory**: `/home/yourusername/School-Management-System`
- **Virtualenv**: `/home/yourusername/.virtualenvs/my-env`

### 6. WSGI File Update Karein
Web tab mein "WSGI configuration file" ke link par click karein. Wahan sab kuch delete karke ye paste karein:
```python
import os
import sys

path = '/home/yourusername/School-Management-System'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'school_project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```
*(Note: `yourusername` ki jagah apna PythonAnywhere wala username likhna)*.

### 7. Static Files Setup
Web tab mein neeche **Static Files** section mein:
- **URL**: `/static/`
- **Path**: `/home/yourusername/School-Management-System/staticfiles`

Bash console mein ja kar ye command chalaein:
```bash
python manage.py collectstatic
```

### 8. Database Seed Karein
Bash console mein hi:
```bash
python manage.py migrate
python manage.py seed_data
```

### 9. ALLOWED_HOSTS Check Karein
`settings.py` mein check karein ke:
```python
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
```

### 10. Reload Karein
Web tab mein sab se upar **Reload** button par click karein. Aap ka project live ho jaye ga!
