from core.models import ImpresoraFiscal
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Max


class Venta(models.Model):
    METODOS_PAGO = [
        ("efectivo", "Efectivo"), ("transferencia", "Transferencia"),
        ("punto_venta", "Punto de venta"),
        ("bio_pago", "Bio Pago"), ("credito", "Crédito (fiado)"),
        ("mixto", "Mixto"),
    ]
    ESTADOS = [("completada", "Completada"), ("anulada", "Anulada")]

    numero = models.PositiveIntegerField(unique=True, editable=False)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="ventas")
    serial_fiscal = models.CharField(max_length=40, null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ventas")
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    base_imponible = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cambio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=15, choices=METODOS_PAGO, default="efectivo")
    estado = models.CharField(max_length=12, choices=ESTADOS, default="completada")
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-numero"]

    def save(self, *args, **kwargs):
        if not self.numero:
            ultima = Venta.objects.aggregate(m=Max("numero"))["m"]
            self.numero = (ultima or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Venta #{self.numero}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey("productos.Producto", on_delete=models.PROTECT, related_name="detalles")
    cantidad = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"


class Pago(models.Model):
    METODOS = [
        ("efectivo", "Efectivo"), ("transferencia", "Transferencia"),
        ("punto_venta", "Punto de venta"),
        ("bio_pago", "Bio Pago"),
    ]
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="pagos")
    metodo = models.CharField(max_length=15, choices=METODOS)
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.get_metodo_display()} Bs {self.monto}"

class Caja(models.Model):
    ESTADOS = [("abierta", "Abierta"), ("cerrada", "Cerrada")]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cajas")
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_contado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    esperado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default="abierta")
    impresora = models.ForeignKey("core.ImpresoraFiscal", on_delete=models.PROTECT,
                                   related_name="cajas", null=True, blank=True)
    regularizada = models.BooleanField(default=False)
    destino_diferencia = models.CharField(max_length=15, null=True, blank=True, choices=[
        ("cajero", "Asumida por el cajero"),
        ("cliente", "Devuelta al cliente"),
        ("ingreso", "Ingreso extraordinario"),
    ])
    regularizada_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="cajas_regularizadas")
    fecha_regularizacion = models.DateTimeField(null=True, blank=True)
    nota_regularizacion = models.TextField(blank=True)
    cliente_reclamo = models.ForeignKey("clientes.Cliente", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="reclamos_caja")
    historial_regularizacion = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Caja {self.id} · {self.usuario} · {self.get_estado_display()}"
