#!/bin/bash
set -e

# Espera a Postgres usando la variable DATABASE_URL real, con límite de intentos
echo "Esperando a postgres..."

MAX_INTENTOS=30
INTENTO=0

# Extrae host y puerto de DATABASE_URL
DB_HOST=$(python -c "import os,urllib.parse as u; print(u.urlparse(os.environ['DATABASE_URL']).hostname)")
DB_PORT=$(python -c "import os,urllib.parse as u; print(u.urlparse(os.environ['DATABASE_URL']).port or 5432)")

until pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; do
  INTENTO=$((INTENTO+1))
  if [ "$INTENTO" -ge "$MAX_INTENTOS" ]; then
    echo "ERROR: Postgres no respondió tras $MAX_INTENTOS intentos. Abortando."
    exit 1
  fi
  echo "Intento $INTENTO/$MAX_INTENTOS..."
  sleep 2
done

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

exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 90