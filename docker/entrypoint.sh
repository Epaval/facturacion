#!/bin/bash
set -e

echo "Esperando a postgres..."
until pg_isready -h db -p 5432 -U facturacion > /dev/null 2>&1; do sleep 1; done
echo "Postgres listo."

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
U = get_user_model()
if not U.objects.filter(username='admin').exists():
    u = U(username='admin', rol='admin', nombres='Admin', apellidos='Sistema')
    u.is_staff = True
    u.is_superuser = True
    u.set_password(os.environ['DJANGO_SUPERUSER_PASSWORD'])
    u.save()
    print('Superuser admin creado')
"
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 90
