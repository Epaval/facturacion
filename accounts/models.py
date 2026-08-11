from django.contrib.auth.models import AbstractUser
from django.db import models


class Empleado(AbstractUser):
    ROLES = [
        ('admin', 'Administrador'),
        ('cajero', 'Cajero'),
        ('vendedor', 'Vendedor'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLES, default='vendedor')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    ci = models.CharField(max_length=20, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)

    @property
    def full_name(self):
        return f"{self.nombres} {self.apellidos}"

    def __str__(self):
        return self.full_name
