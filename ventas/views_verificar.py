from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Venta
import hashlib

@login_required
def verificar_cadena(request):
    """Recalcula todos los hashes y detecta modificaciones."""
    ventas = list(Venta.objects.order_by("numero"))
    errores = []
    prev = "0" * 64
    
    for v in ventas:
        if not v.hash_factura:
            errores.append(f"Venta {v.numero}: sin hash")
            continue
        
        # Recalcular hash esperado
        payload = f"{prev}|{v.numero}|{v.total}|{v.cliente_id or ''}"
        hash_esperado = hashlib.sha256(payload.encode()).hexdigest()
        
        if v.hash_factura != hash_esperado:
            errores.append(f"Venta {v.numero}: hash no coincide (modificada o corrupta)")
        
        # Verificar que hash_prev apunta al hash anterior
        if v.hash_prev != prev:
            errores.append(f"Venta {v.numero}: hash_prev incorrecto (cadena rota)")
        
        prev = v.hash_factura
    
    context = {
        "total": len(ventas),
        "ok": len(ventas) - len(errores),
        "errores": errores,
        "ultimo_hash": ventas[-1].hash_factura if ventas else None,
    }
    return render(request, "ventas/verificar_cadena.html", context)
