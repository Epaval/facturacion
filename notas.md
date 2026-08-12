source .venv/bin/activate
python3 manage.py runserver 8020

python3 -m py_compile ventas/views.py && echo "SINTAXIS OK"