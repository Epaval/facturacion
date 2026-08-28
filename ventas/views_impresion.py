from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Venta, Caja
from core.models import ConfigNegocio, ImpresoraFiscal
from core.impresion import ticket_fiscal_texto, enviar_ticket, pdf_factura


def _impresora_de(request):
    caja = Caja.objects.filter(usuario=request.user, estado="abierta").first()
    if caja and caja.impresora:
        return caja.impresora
    return ImpresoraFiscal.objects.filter(activa=True).first()


@login_required
def venta_pdf(request, pk):
    """Modo correlativo → PDF descargable."""
    v = get_object_or_404(Venta, pk=pk)
    data = pdf_factura(v, ConfigNegocio.get())
    r = HttpResponse(data, content_type="application/pdf")
    r["Content-Disposition"] = f'filename="factura_{v.numero:06d}.pdf"'
    return r


@login_required
def venta_ticket(request, pk):
    """Modo fiscal → ticket 80mm por el canal configurado."""
    v = get_object_or_404(Venta, pk=pk)
    imp = _impresora_de(request)
    texto = ticket_fiscal_texto(v, ConfigNegocio.get())
    if not imp or imp.conexion == "txt":
        r = HttpResponse(texto, content_type="text/plain; charset=utf-8")
        r["Content-Disposition"] = f'filename="ticket_{v.numero:06d}.txt"'
        return r
    ok, msg = enviar_ticket(texto, imp)
    if ok:
        messages.success(request, f"🖨 {msg}")
    else:
        messages.error(request, msg)
    return redirect(request.META.get("HTTP_REFERER") or f"/ventas/venta/{pk}/")
