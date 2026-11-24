web: python manage.py migrate --noinput && gunicorn slimai_project.wsgi:application --bind 0.0.0.0:8080 --workers 2 --timeout 120
