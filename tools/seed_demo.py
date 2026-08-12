"""Datos demo: python3 tools/seed_demo.py (no crea superusuario)."""
import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import Empleado
from clientes.models import Cliente
from productos.models import Categoria, Producto

for u, n, a in [("cajero", "Rosa", "Medina"), ("cajero1", "Pedro", "Caja"), ("cajero2", "Luis", "Caja")]:
    e, c = Empleado.objects.get_or_create(username=u, defaults=dict(nombres=n, apellidos=a, rol="cajero"))
    if c:
        e.set_password("cajero123"); e.save()

clientes = [
    ("María", "Pérez", "12345678"), ("Juan", "González", "9876543"),
    ("Ana", "Rodríguez", "15432876"), ("Carlos", "Fernández", "V14523698"),
    ("Luis", "Martínez", "17654321"), ("Carmen", "López", "13987654"),
    ("José", "Ramírez", "V16234579"), ("Rosa", "Torres", "18765432"),
    ("Pedro", "Sánchez", "12987345"), ("Laura", "Díaz", "V19876543"),
    ("Miguel", "Castro", "16543219"), ("Elena", "Vargas", "14321987"),
    ("Jorge", "Rojas", "J40123456"), ("Sofía", "Mendoza", "20123456"),
    ("Andrés", "Silva", "15678234"), ("Beatriz", "Campos", "G20345678"),
]
for n, a, doc in clientes:
    Cliente.objects.get_or_create(ci_nit=doc, defaults=dict(nombres=n, apellidos=a, telefono="555" + doc[-4:]))

cats = {n: Categoria.objects.get_or_create(nombre=n)[0] for n in [
    "Víveres", "Charcutería", "Panadería", "Bebidas",
    "Carnicería", "Limpieza", "Ropa", "Frutas y verduras"]}

P = [
    ("Queso de mano", "Charcutería", "kg", 5500, 12, 5), ("Queso llanero", "Charcutería", "kg", 4800, 15, 5),
    ("Queso paisa", "Charcutería", "kg", 4200, 10, 4), ("Queso amarillo", "Charcutería", "kg", 3900, 10, 4),
    ("Queso de año", "Charcutería", "kg", 6200, 6, 3), ("Jamonada de pollo", "Charcutería", "unidad", 1800, 25, 8),
    ("Jamonada de cerdo", "Charcutería", "unidad", 2200, 20, 8), ("Jamón ahumado", "Charcutería", "kg", 5200, 8, 3),
    ("Chorizo carupano", "Charcutería", "kg", 4600, 9, 3), ("Mortadela", "Charcutería", "kg", 2400, 12, 4),
    ("Pan integral", "Panadería", "unidad", 350, 40, 15), ("Pan blanco", "Panadería", "unidad", 300, 60, 20),
    ("Pan francés", "Panadería", "unidad", 280, 50, 15), ("Pan de jamón", "Panadería", "unidad", 2500, 10, 4),
    ("Refresco cola 1L", "Bebidas", "unidad", 1200, 48, 15), ("Refresco cola 2L", "Bebidas", "unidad", 2200, 36, 12),
    ("Refresco naranja 1L", "Bebidas", "unidad", 1100, 30, 10), ("Refresco naranja 2L", "Bebidas", "unidad", 2100, 24, 8),
    ("Refresco limón 1L", "Bebidas", "unidad", 1100, 28, 10), ("Refresco uva 1L", "Bebidas", "unidad", 1150, 20, 8),
    ("Agua mineral 500ml", "Bebidas", "unidad", 500, 60, 20), ("Jugo de mango 1L", "Bebidas", "unidad", 1400, 18, 6),
    ("Arroz 1kg", "Víveres", "unidad", 1300, 60, 15), ("Arroz 5kg", "Víveres", "unidad", 6200, 25, 8),
    ("Azúcar 1kg", "Víveres", "unidad", 1400, 40, 10), ("Azúcar morena 1kg", "Víveres", "unidad", 1600, 20, 8),
    ("Harina de maíz 1kg", "Víveres", "unidad", 1200, 50, 15), ("Harina de trigo 1kg", "Víveres", "unidad", 1500, 30, 10),
    ("Pasta corta 500g", "Víveres", "unidad", 900, 45, 12), ("Pasta larga 500g", "Víveres", "unidad", 900, 45, 12),
    ("Aceite de maíz 1L", "Víveres", "unidad", 3000, 8, 10), ("Aceite de girasol 1L", "Víveres", "unidad", 2800, 30, 10),
    ("Café molido 500g", "Víveres", "unidad", 4500, 18, 6), ("Leche líquida 1L", "Víveres", "unidad", 1500, 40, 12),
    ("Caraotas negras 1kg", "Víveres", "unidad", 2100, 22, 8), ("Atún en lata", "Víveres", "unidad", 1100, 50, 15),
    ("Sardinas en lata", "Víveres", "unidad", 700, 45, 15), ("Mayonesa 500g", "Víveres", "unidad", 2600, 16, 6),
    ("Sal 1kg", "Víveres", "unidad", 400, 35, 10), ("Papelón", "Víveres", "unidad", 800, 20, 8),
    ("Carne molida de res", "Carnicería", "kg", 3800, 20, 6), ("Pollo entero", "Carnicería", "kg", 2600, 30, 10),
    ("Pechuga de pollo", "Carnicería", "kg", 3400, 22, 8), ("Chuleta de cerdo", "Carnicería", "kg", 4100, 12, 4),
    ("Detergente en polvo 1kg", "Limpieza", "unidad", 2600, 30, 10), ("Cloro 1L", "Limpieza", "unidad", 1200, 8, 12),
    ("Jabón de baño", "Limpieza", "unidad", 600, 60, 20), ("Jabón azul", "Limpieza", "unidad", 500, 50, 15),
    ("Suavizante 1L", "Limpieza", "unidad", 2400, 18, 6), ("Lavaplatos 500ml", "Limpieza", "unidad", 1300, 25, 8),
    ("Camiseta básica", "Ropa", "unidad", 5000, 20, 5), ("Camiseta estampada", "Ropa", "unidad", 6500, 15, 5),
    ("Jeans hombre", "Ropa", "unidad", 15000, 12, 4), ("Jeans mujer", "Ropa", "unidad", 16000, 12, 4),
    ("Tomate", "Frutas y verduras", "kg", 1800, 15, 5), ("Cebolla", "Frutas y verduras", "kg", 1600, 15, 5),
    ("Papa", "Frutas y verduras", "kg", 1200, 25, 8), ("Plátano", "Frutas y verduras", "kg", 900, 20, 6),
]
cod = 7750100
for nombre, cat, un, pv, st, sm in P:
    cod += 1
    venta = Decimal(str(pv))
    compra = (venta * Decimal("0.7")).quantize(Decimal("0.01"))
    Producto.objects.get_or_create(codigo_barras=str(cod), defaults=dict(
        nombre=nombre, categoria=cats[cat], unidad=un,
        precio_venta=venta, precio_compra=compra,
        stock=Decimal(st), stock_minimo=Decimal(sm)))

Producto.objects.filter(nombre="Camiseta básica").update(grava_iva=True)
print("seed listo:", Producto.objects.count(), "productos,", Cliente.objects.count(), "clientes")
