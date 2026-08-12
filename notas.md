source .venv/bin/activate
python3 manage.py runserver 8020

python3 -m py_compile ventas/views.py && echo "SINTAXIS OK"

git add desktop/launcher.py
git commit -m "Add button de import data CSV"
git push origin main

git tag v0.0.15
git push origin v0.0.15