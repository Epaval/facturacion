
cat > ventas/migrations/0015_venta_numero_control.py <<'PYEOF'
from django.db import migrations, models


def rellenar(apps, schema_editor):
    Venta = apps.get_model("ventas", "Venta")
    for v in Venta.objects.filter(numero_control=""):
        v.numero_control = f"00-{v.numero:06d}"
        v.save(update_fields=["numero_control"])


class Migration(migrations.Migration):
    dependencies = [("ventas", "0014_libroventa")]
    operations = [
        migrations.AddField(
            model_name="venta",
            name="numero_control",
            field=models.CharField(blank=True,
                                   help_text="UNO SOLO: serial de caja (fiscal) o 00-000000 (correlativo)",
                                   max_length=20, verbose_name="N° de Control"),
        ),
        migrations.RunPython(rellenar, migrations.RunPython.noop),
    ]
