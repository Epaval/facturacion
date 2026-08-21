import time
from decimal import Decimal

_cache = {"tasa": None, "ts": 0.0}


def invalidar_tasa():
    _cache["tasa"] = None
    _cache["ts"] = 0.0


def tasa_actual():
    now = time.time()
    if _cache["tasa"] is None or now - _cache["ts"] > 15:
        from core.models import ConfigNegocio
        _cache["tasa"] = ConfigNegocio.get().tasa_dolar or Decimal("1")
        _cache["ts"] = now
    return _cache["tasa"]


def q2(x):
    return Decimal(str(x)).quantize(Decimal("0.01"))


def precio_bs(producto):
    """Precio de venta del producto expresado en Bs ($ x tasa)."""
    return q2(Decimal(str(producto.precio_venta)) * tasa_actual())


def usd_de_bs(monto_bs):
    t = tasa_actual() or Decimal("1")
    return q2(Decimal(str(monto_bs)) / t)
