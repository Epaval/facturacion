from django.conf import settings
from django.db import models
from django.utils import timezone


class Licencia(models.Model):
    """Una sola fila (singleton). Controla los 7 días de prueba + 365 días de licencia."""
    clave = models.CharField(max_length=100, blank=True, null=True, unique=True)
    activada = models.BooleanField(default=False)
    fecha_activacion = models.DateTimeField(null=True, blank=True)
    dias_licencia = models.PositiveIntegerField(default=365)

    class Meta:
        verbose_name = "Licencia"

    def save(self, *args, **kwargs):
        # Singleton: solo una fila
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def dias_restantes(self):
        if not self.activada or not self.fecha_activacion:
            return None
        delta = timezone.now() - self.fecha_activacion
        return max(0, self.dias_licencia - delta.days)

    @property
    def esta_vencida(self):
        r = self.dias_restantes
        return r is not None and r <= 0


class ConfigNegocio(models.Model):
    """Datos del negocio para facturas (singleton)."""
    nombre = models.CharField(max_length=120, default="Mi Negocio")
    rif = models.CharField("RIF", max_length=20)
    nit = models.CharField("NIT", max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    serial_impresora_fiscal = models.CharField(
        "Serial de impresora fiscal", max_length=60, blank=True,
        help_text="Se usa como número de control en la factura"
    )
    logo = models.ImageField(upload_to="logo/", null=True, blank=True)
    notas_factura = models.TextField(
        "Notas al pie de la factura", blank=True,
        help_text="Ej: Gracias por su compra · Conserve este documento"
    )
    tasa_dolar = models.DecimalField(
        "Tasa del dólar (Bs por $)", max_digits=12, decimal_places=2,
        default=1, help_text="Actualiza a diario. Todos los precios se venden en Bs = $ x tasa."
    )

    class Meta:
        verbose_name = "Configuración del negocio"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        from core import moneda
        moneda.invalidar_tasa()

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ImpresoraFiscal(models.Model):
    """Impresoras fiscales del negocio. El admin las registra una vez."""
    nombre = models.CharField(max_length=60, help_text="Ej: Caja 1 principal, Respaldo")
    serial = models.CharField(max_length=40, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.serial})"
