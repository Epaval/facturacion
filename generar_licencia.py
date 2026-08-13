"""Genera claves de licencia firmadas para una máquina.
Uso:  python3 generar_licencia.py --huella ABCD1234 --dias 365
La huella la muestra la pantalla de licencia del cliente."""
import argparse
from core.licencia_keys import generar_clave

p = argparse.ArgumentParser()
p.add_argument("--huella", required=True, help="Huella de la máquina del cliente")
p.add_argument("--dias", type=int, default=365)
a = p.parse_args()
print(generar_clave(a.dias, a.huella))
