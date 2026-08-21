from decimal import Decimal
from django import template
from core import moneda as _m

register = template.Library()


@register.filter
def bs(valor):
    """USD -> Bs"""
    return _m.q2(Decimal(str(valor)) * _m.tasa_actual())


@register.filter
def usd(valor):
    """Bs -> USD"""
    return _m.usd_de_bs(valor)
