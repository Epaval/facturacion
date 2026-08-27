from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0003_confignegocio_tasa_dolar")]
    operations = [
        migrations.AddField(
            model_name="confignegocio",
            name="modo_control",
            field=models.CharField(
                choices=[("fiscal", "Impresora fiscal (serial de caja como control)"),
                         ("correlativo", "Correlativo 00-000000")],
                default="correlativo", max_length=12,
                verbose_name="Modo de número de control (uno solo, excluyente)"),
        ),
    ]
