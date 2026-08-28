"""Motor de impresión: ticket fiscal 80mm, PDF correlativo y envío configurable."""
import os, socket, subprocess, tempfile

ANCHO = 48  # columnas típicas de ticket 80mm


def _centrar(t):
    return t.center(ANCHO).rstrip()


def _linea(ch="-"):
    return ch * ANCHO


def _col(izq, der):
    return (izq + (" " * (ANCHO - len(izq) - len(der))) + der).rstrip()


def ticket_fiscal_texto(venta, cfg):
    """Texto plano formato fiscal 80mm (mayúsculas, columnas, serial y hash)."""
    det = venta.detalle_set.all() if hasattr(venta, "detalle_set") else venta.detalles.all()
    L = [_centrar(cfg.nombre.upper()), _centrar(f"RIF {cfg.rif}"),
         _centrar(cfg.direccion.upper()), _linea(),
         f"DOCUMENTO: {venta.numero:08d}",
         f"CLIENTE: {(venta.cliente.full_name if venta.cliente else 'CONSUMIDOR FINAL').upper()}",
         f"RIF: {(venta.cliente.ci_nit if venta.cliente else '').upper()}",
         f"FECHA: {venta.fecha:%d-%m-%Y %H:%M}", _linea(), "FACTURA"]
    for d in det:
        L.append(f"{d.producto.nombre[:24].upper()} {d.cantidad}")
        L.append(_col("", f"Bs {d.subtotal:,.2f}"))
    L += [_linea(), _col("SUBTOTAL", f"Bs {venta.subtotal:,.2f}"),
          _col(f"BI {16}%", f"Bs {venta.base_imponible:,.2f}"),
          _col("IVA 16%", f"Bs {venta.monto_iva:,.2f}"),
          _col("TOTAL", f"Bs {venta.total:,.2f}"), _linea(),
          cfg.notas_factura.upper(), f"HASH: {venta.hash_factura[:24].upper()}",
          "", venta.numero_control]
    return "\n".join(L)


def enviar_ticket(texto, imp):
    """Envía bytes según conexión configurada. Devuelve (ok, mensaje)."""
    data = texto.encode("cp437", errors="replace")
    try:
        if imp.conexion == "serial":
            import serial
            with serial.Serial(imp.puerto_serial or "COM1", imp.baud or 9600, timeout=3) as s:
                s.write(data)
            return True, f"Enviado por {imp.puerto_serial}"
        if imp.conexion == "red":
            with socket.create_connection((imp.ip, imp.puerto_red or 9100), timeout=5) as s:
                s.sendall(data)
            return True, f"Enviado a {imp.ip}:{imp.puerto_red}"
        if imp.conexion == "compartida":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
                f.write(data)
                tmp = f.name
            if os.name == "nt":
                subprocess.run(f'copy /b "{tmp}" "{imp.nombre_compartido}"',
                               shell=True, check=True)
            else:
                subprocess.run(["lp", "-d", imp.nombre_compartido, tmp], check=True)
            os.unlink(tmp)
            return True, f"Enviado a {imp.nombre_compartido}"
        return False, "Conexión .txt: usa el botón Descargar"
    except Exception as e:
        return False, f"Error: {e}"


def pdf_factura(venta, cfg):
    """PDF A4 simple para modo correlativo."""
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter
    y = h - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, cfg.nombre)
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"{cfg.direccion} · RIF: {cfg.rif} · Tel: {cfg.telefono}")
    y -= 24
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 50, y, f"FACTURA N°: {venta.numero:06d}")
    y -= 14
    c.drawRightString(w - 50, y, f"N° de Control: {venta.numero_control}")
    y -= 14
    c.setFont("Helvetica", 9)
    c.drawRightString(w - 50, y, f"Hash: {venta.hash_factura[:16]}...")
    y -= 14
    c.drawRightString(w - 50, y, f"Fecha: {venta.fecha:%d/%m/%Y %H:%M}")
    y -= 24
    c.setFont("Helvetica", 10)
    cli = venta.cliente
    c.drawString(50, y, f"Cliente: {cli.full_name if cli else 'Consumidor final'}")
    y -= 14
    c.drawString(50, y, f"CI/RIF: {cli.ci_nit if cli else '—'}")
    y -= 24
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "PRODUCTO")
    c.drawRightString(w - 50, y, "SUBTOTAL")
    y -= 6
    c.setLineWidth(0.5)
    c.line(50, y, w - 50, y)
    y -= 14
    c.setFont("Helvetica", 10)
    for d in venta.detalles.all():
        c.drawString(50, y, f"{d.cantidad} x {d.producto.nombre}")
        c.drawRightString(w - 50, y, f"Bs {d.subtotal:,.2f}")
        y -= 14
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 50, y, f"TOTAL: Bs {venta.total:,.2f}")
    y -= 30
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(w / 2, y, cfg.notas_factura)
    c.save()
    return buf.getvalue()
