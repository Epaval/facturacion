"""Arranque de escritorio: python desktop.py (o el .exe empaquetado)."""
import os
import threading
import webbrowser

import django


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    from django.core.management import call_command
    call_command("migrate", interactive=False)
    call_command("collectstatic", interactive=False, verbosity=0)

    from django.core.wsgi import get_wsgi_application
    from waitress import serve

    threading.Timer(2.0, lambda: webbrowser.open("http://127.0.0.1:8020")).start()
    print("=" * 50)
    print("Facturación corriendo en http://127.0.0.1:8020")
    print("Cierra esta ventana para detener el sistema.")
    print("=" * 50)
    serve(get_wsgi_application(), host="127.0.0.1", port=8020)


if __name__ == "__main__":
    main()
