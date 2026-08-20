from decimal import Decimal

from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import LibroVenta, NotaCredito, Venta


@receiver(post_save, sender=Venta)
def registrar_libro_venta(sender, instance, created, **kwargs):
    """Registra la venta en el libro al crearla (completada)."""
    if not created or instance.estado != "completada":
        return
    if LibroVenta.objects.filter(venta=instance).exists():
        return

    ultimo = LibroVenta.objects.order_by("-id").first()
    siguiente = 1
    if ultimo:
        try:
            siguiente = int(ultimo.numero_control.split("-")[-1]) + 1
        except (ValueError, IndexError):
            siguiente = ultimo.id + 1
    numero_control = f"NC-{siguiente:06d}"

    cliente_nombre = "Consumidor final"
    cliente_rif = ""
    if instance.cliente:
        cliente_nombre = instance.cliente.full_name
        cliente_rif = instance.cliente.ci_nit or ""

    exento = (instance.total - instance.base_imponible - instance.monto_iva).quantize(Decimal("0.01"))

    LibroVenta.objects.create(
        venta=instance,
        numero_control=numero_control,
        numero_factura=f"{instance.numero:06d}",
        fecha_factura=instance.fecha.date(),
        cliente_nombre=cliente_nombre,
        cliente_rif=cliente_rif,
        total_facturado=instance.total,
        exento=max(exento, Decimal("0.00")),
        base_imponible_iva=instance.base_imponible,
        monto_iva=instance.monto_iva,
        alicuota_iva=Decimal("16"),
        notas_credito_total=Decimal("0"),
    )


@receiver(post_save, sender=NotaCredito)
def actualizar_libro_venta_nc(sender, instance, created, **kwargs):
    """Recalcula el total de NC en el libro de la factura afectada."""
    if not created:
        return
    libro = LibroVenta.objects.filter(venta=instance.factura).first()
    if libro:
        total_nc = NotaCredito.objects.filter(factura=instance.factura).aggregate(s=Sum("total"))["s"] or Decimal("0")
        libro.notas_credito_total = total_nc
        libro.save(update_fields=["notas_credito_total"])
