web: python manage.py migrate --noinput && python seed_data.py && gunicorn slimai_project.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120
