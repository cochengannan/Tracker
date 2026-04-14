#!/usr/bin/env bash
# Render build script for Django backend
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser from env vars if it doesn't exist
python manage.py shell << 'PYEOF'
import os
from django.contrib.auth.models import User
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser "{username}" created.')
else:
    print(f'Superuser "{username}" already exists.')
PYEOF
