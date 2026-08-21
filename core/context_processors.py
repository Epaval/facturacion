def tasa(request):
    from core.moneda import tasa_actual
    return {"TASA_ACTUAL": tasa_actual()}
