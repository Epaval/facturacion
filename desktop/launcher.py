"""Launcher unificado: soporta --sin-ventana para servicio de fondo."""
import os
import sys
import time
import socket
import webbrowser
from pathlib import Path


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def main():
    sin_ventana = "--sin-ventana" in sys.argv
    usar_puerto = 8020
    for arg in sys.argv:
        if arg.startswith("--puerto="):
            try:
                usar_puerto = int(arg.split("=", 1)[1])
            except ValueError:
                pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()

    from django.core.management import call_command
    from django.conf import settings

    if getattr(sys, "frozen", False):
        os.chdir(Path(sys.executable).resolve().parent)

    call_command("migrate", interactive=False)

    if not sin_ventana:
        print("=" * 58)
        print(f"Facturación corriendo en http://127.0.0.1:{usar_puerto}")
        print("Cierra esta ventana para detener el sistema.")
        print("=" * 58)

    # abrir navegador solo si no es modo servicio
    if not sin_ventana:
        webbrowser.open(f"http://127.0.0.1:{usar_puerto}")

    from waitress.server import create_server
    from waitress import serve
    from django.core.wsgi import get_wsgi_application

    app = get_wsgi_application()
    serve(app, host="127.0.0.1", port=usar_puerto, threads=8,
          _quiet=sin_ventana)


if __name__ == "__main__":
    main()
