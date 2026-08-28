from core.models import ImpresoraFiscal
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Max


class Venta(models.Model):
    impresa = models.BooleanField("Impresa", default=False)
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
    numero_control = models.CharField(
        "N° de Control", max_length=20, blank=True,
        help_text="UNO SOLO: serial de caja (fiscal) o 00-000000 (correlativo)")
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
        indexes = [
            models.Index(fields=["fecha"], name="idx_venta_fecha"),
            models.Index(fields=["estado"], name="idx_venta_estado"),
            models.Index(fields=["usuario", "fecha"], name="idx_venta_usr_fec"),
        ]

    def _generar_control(self):
        from core.models import ConfigNegocio
        cfg = ConfigNegocio.get()
        if cfg.modo_control == "fiscal":
            return (self.serial_fiscal or cfg.serial_impresora_fiscal or "SIN-CAJA")[:20]
        return f"00-{self.numero:06d}"

    def save(self, *args, **kwargs):
        if self.numero:
            if not self.numero_control:
                self.numero_control = self._generar_control()
            super().save(*args, **kwargs)
            return
        from django.db import IntegrityError, transaction
        for _ in range(5):
            try:
                with transaction.atomic():
                    ultima = Venta.objects.aggregate(m=Max("numero"))["m"]
                    self.numero = (ultima or 0) + 1
                    if not self.numero_control:
                        self.numero_control = self._generar_control()
                    super().save(*args, **kwargs)
                    return
            except IntegrityError:
                self.numero = None
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


class NotaCredito(models.Model):
    """Nota de crédito: devolución de productos de una factura."""
    factura = models.ForeignKey(Venta, on_delete=models.PROTECT, related_name='notas_credito')
    caja_procesamiento = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='notas_credito_procesadas')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='notas_credito_creadas')
    autorizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='notas_credito_autorizadas')
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=200)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"NC #{self.id} - Factura #{self.factura.numero}"


class NotaCreditoDetalle(models.Model):
    """Detalle de productos devueltos en una nota de crédito."""
    nota_credito = models.ForeignKey(NotaCredito, on_delete=models.CASCADE, related_name='detalles')
    detalle_venta = models.ForeignKey(DetalleVenta, on_delete=models.PROTECT, related_name='devoluciones')
    cantidad_devuelta = models.DecimalField(max_digits=12, decimal_places=3)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.detalle_venta.producto.nombre} x{self.cantidad_devuelta}"


class LibroVenta(models.Model):
    """Registro fiscal de cada venta para el libro de ventas SENIAT."""
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='libro_venta')
    numero_control = models.CharField("N° de Control", max_length=20, help_text="Número secuencial de control fiscal")
    numero_factura = models.CharField("N° de Factura", max_length=20)
    fecha_factura = models.DateField("Fecha factura")
    
    # Datos del cliente
    cliente_nombre = models.CharField(max_length=200)
    cliente_rif = models.CharField("RIF/CI", max_length=30, blank=True)
    
    # Montos
    total_facturado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    exento = models.DecimalField("Exento", max_digits=12, decimal_places=2, default=0)
    base_imponible_iva = models.DecimalField("Base imponible IVA", max_digits=12, decimal_places=2, default=0)
    monto_iva = models.DecimalField("Monto IVA", max_digits=12, decimal_places=2, default=0)
    alicuota_iva = models.DecimalField("Alícuota IVA %", max_digits=5, decimal_places=2, default=16)
    
    # Retenciones (opcionales)
    iva_retenido = models.DecimalField("IVA retenido", max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    numero_comprobante = models.CharField("N° comprobante retención", max_length=20, blank=True)
    
    # Notas de crédito asociadas
    notas_credito_total = models.DecimalField("Total notas de crédito", max_digits=12, decimal_places=2, default=0)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_factura', '-numero_factura']
        verbose_name = "Libro de Venta"
        verbose_name_plural = "Libro de Ventas"
    
    @property
    def total_neto(self):
        return (self.total_facturado - self.notas_credito_total).quantize(__import__("decimal").Decimal("0.01"))

    def __str__(self):
        return f"Libro Venta #{self.numero_control} - Factura {self.numero_factura}"
