source .venv/bin/activate


cd ~/facturacion
git add -A
git commit -m "v0.0.21: impresoras fiscales por caja (registro en panel admin, seleccion obligatoria al abrir caja, serial guardado por venta), modo red LAN servidor/estacion/individual, respaldo de BD solo admin, importacion CSV, por_peso para granel"
git push origin main

git tag v0.0.21
git push origin v0.0.21


cd ~/facturacion
pkill -f desktop.py
python3 desktop.py