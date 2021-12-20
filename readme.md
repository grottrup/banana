


Steps to ensure client works:

Note: python commands in mac can be python3 instead of python

1. cd into src/django_project/
2. create a venv using python3 -m venv venv (if venv is already created skip this step)
3. actiave venv using:
    mac: source venv/bin/activate or source/Scripts/activate
    windows: source venv/Scripts/actiavte (bash), venv\Sripcts\activate.bat (cmd) or venv\Scripts\activate.ps1
4. install requirements.txt using:
    pip install -r requirements.txt
5. create DB:
    python manage.py makemigrations
6. apply changes DB changes:
    python manage.py migrate
7. run the server:
    python manage.py runserver
8. navigate to http://127.0.0.1:8000