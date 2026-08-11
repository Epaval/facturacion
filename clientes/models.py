from django.db import models


class Cliente(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100, blank=True)
    ci_nit = models.CharField("CI/NIT", max_length=30, blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    credito_habilitado = models.BooleanField("¿Habilitado para crédito?", default=False)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notas = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombres"]

    @property
    def full_name(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def __str__(self):
        return self.full_name
