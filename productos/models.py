from django.conf import settings
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    UNIDADES = [
        ("unidad", "Unidad"), ("kg", "Kilogramo"), ("g", "Gramo"),
        ("lb", "Libra"), ("l", "Litro"), ("ml", "Mililitro"),
        ("docena", "Docena"), ("paquete", "Paquete"), ("m", "Metro"),
    ]

    nombre = models.CharField(max_length=120)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    codigo_barras = models.CharField(max_length=40, blank=True, null=True, unique=True)
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unidad = models.CharField(max_length=10, choices=UNIDADES, default="unidad")
    por_peso = models.BooleanField(default=False, verbose_name="Se vende por peso (granel)")
    activo = models.BooleanField(default=True)
    grava_iva = models.BooleanField("Paga IVA (16%)", default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"], name="idx_prod_nombre"),
            models.Index(fields=["codigo_barras"], name="idx_prod_codigo"),
            models.Index(fields=["categoria"], name="idx_prod_categoria"),
            models.Index(fields=["activo"], name="idx_prod_activo"),
        ]

    @property
    def es_pesable(self):
        return self.unidad in ("kg", "g", "lb")

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    def __str__(self):
        return self.nombre


class MovimientoStock(models.Model):
    """Kardex: todo movimiento de inventario queda auditado."""
    TIPOS = [
        ("venta", "Venta"),
        ("compra", "Compra/Entrada"),
        ("ajuste_pos", "Ajuste +"),
        ("ajuste_neg", "Ajuste -"),
        ("conteo", "Conteo fisico"),
        ("inicial", "Stock inicial"),
    ]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=12, choices=TIPOS)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    stock_resultante = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    motivo = models.CharField(max_length=200, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_stock")
    venta = models.ForeignKey("ventas.Venta", null=True, blank=True, on_delete=models.SET_NULL, related_name="movimientos_stock")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.producto.nombre} {self.tipo} {self.cantidad}"
