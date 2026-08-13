"""Launcher unificado: individual / servidor LAN / estación."""
import os
import sys
import webbrowser
from pathlib import Path

# Agregar raíz del proyecto al path para encontrar config/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    import io
    # En modo frozen sin consola, stdout/stderr pueden ser None
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()
    if sys.stdin is None:
        sys.stdin = io.StringIO()

    args = sys.argv[1:]
    sin_ventana = "--sin-ventana" in args
    lan = "--lan" in args
    conectar = "--conectar" in args

    frozen = getattr(sys, "frozen", False)
    base_dir = Path(sys.executable).resolve().parent if frozen else Path(__file__).resolve().parent.parent

    puerto = 8020
    for arg in args:
        if arg.startswith("--puerto="):
            try:
                puerto = int(arg.split("=", 1)[1])
            except ValueError:
                pass

    # MODO ESTACIÓN: solo abre el navegador hacia el servidor y sale
    if conectar:
        ip_file = base_dir / "ip_servidor.txt"
        ip = ip_file.read_text().strip() if ip_file.exists() else "127.0.0.1"
        print(f"Conectando con el servidor {ip}:{puerto} ...")
        webbrowser.open(f"http://{ip}:{puerto}")
        return

    # MODO SERVIDOR (individual o LAN)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()

    from django.core.management import call_command
    if frozen:
        os.chdir(base_dir)

    call_command("migrate", interactive=False, stdout=sys.stdout, stderr=sys.stderr)

    host = "0.0.0.0" if lan else "127.0.0.1"

    if not sin_ventana:
        print("=" * 58)
        if lan:
            print(f"SERVIDOR EN RED: http://<IP de esta PC>:{puerto}")
            print(f"Consola local:   http://127.0.0.1:{puerto}")
        else:
            print(f"Facturación corriendo en http://127.0.0.1:{puerto}")
        print("Cierra esta ventana para detener el sistema.")
        print("=" * 58)
        webbrowser.open(f"http://127.0.0.1:{puerto}")

    from waitress import serve
    from django.core.wsgi import get_wsgi_application

    app = get_wsgi_application()
    try:
        serve(app, host=host, port=puerto, threads=8, _quiet=sin_ventana)
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
    finally:
        if not sin_ventana:
            try:
                input("\nPresiona Enter para cerrar esta ventana...")
            except Exception:
                pass


if __name__ == "__main__":
    main()
