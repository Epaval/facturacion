"""Licencias firmadas con HMAC.
El secreto vive en core/licencia_secret.py (ignorado por git) o en la
variable de entorno LICENSE_SECRET (la inyecta el CI al construir el .exe)."""
import hashlib
import hmac
import os
import platform
from pathlib import Path
import uuid

try:
    from .licencia_secret import LICENSE_SECRET
except ImportError:
    LICENSE_SECRET = os.environ.get("LICENSE_SECRET", "dev-secret-cambiar-en-produccion")


def huella_maquina() -> str:
    """Huella estable: MAC+hostname+SO en desktop; id persistido en web/docker."""
    if os.environ.get("FACTURACION_WEB"):
        ruta = Path(__file__).resolve().parent.parent / "data" / ".maquina_id"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if not ruta.exists():
            ruta.write_text(uuid.uuid4().hex[:16].upper())
        base = ruta.read_text().strip()
    else:
        base = f"{uuid.getnode()}|{platform.node()}|{platform.system()}"
    return hashlib.sha256(base.encode()).hexdigest()[:8].upper()


def _firma(payload: str) -> str:
    return hmac.new(LICENSE_SECRET.encode(), payload.encode(),
                    hashlib.sha256).hexdigest()[:8].upper()


def generar_clave(dias: int, huella: str) -> str:
    """Genera una clave válida solo para la máquina con esa huella."""
    payload = f"{dias:04d}{huella.upper()}"
    raw = payload + _firma(payload)          # 4 + 8 + 8 = 20
    return "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))


def validar_clave(clave: str):
    """Devuelve (dias, huella) si la clave es válida para ESTA máquina, si no None."""
    raw = clave.replace("-", "").upper()
    if len(raw) != 20 or not raw.isalnum():
        return None
    if not raw[:4].isdigit():
        return None
    dias = int(raw[:4])
    huella = raw[4:12]
    sig = raw[12:20]
    if huella != huella_maquina():
        return None
    if not hmac.compare_digest(sig, _firma(raw[:12])):
        return None
    return dias, huella
