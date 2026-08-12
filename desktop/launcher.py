"""Launcher unificado: soporta --sin-ventana para servicio de fondo."""
import os
import sys
import io
import time
import socket
import webbrowser
import logging
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURACIÓN DE IO PARA EJECUTABLE SIN CONSOLA
# ============================================================
def setup_io():
    """
    Configurar stdout/stderr para funcionar en ejecutable sin consola.
    Esto previene el error: 'NoneType' object has no attribute 'write'
    """
    # Configurar stdout
    if sys.stdout is None:
        try:
            if sys.__stdout__ is not None and hasattr(sys.__stdout__, 'buffer'):
                sys.stdout = io.TextIOWrapper(
                    sys.__stdout__.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                # Fallback: usar StringIO si no hay buffer disponible
                sys.stdout = io.StringIO()
        except Exception:
            sys.stdout = io.StringIO()
    
    # Configurar stderr
    if sys.stderr is None:
        try:
            if sys.__stderr__ is not None and hasattr(sys.__stderr__, 'buffer'):
                sys.stderr = io.TextIOWrapper(
                    sys.__stderr__.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                sys.stderr = io.StringIO()
        except Exception:
            sys.stderr = io.StringIO()
    
    return sys.stdout, sys.stderr

# Ejecutar configuración ANTES de cualquier import de Django
setup_io()

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================
def setup_logging():
    """Configurar logging para registrar errores en archivo"""
    log_dir = Path.home() / 'FacturacionLogs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'facturacion_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stderr) if sys.stderr else logging.NullHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================

def get_free_port():
    """Obtener un puerto libre automáticamente"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def safe_migrate():
    """
    Ejecutar migraciones de Django de forma segura,
    capturando cualquier error y registrándolo
    """
    try:
        from django.core.management import call_command
        
        # Guardar referencias originales
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        try:
            # Asegurar que no sean None para migrate
            if sys.stdout is None:
                sys.stdout = io.StringIO()
            if sys.stderr is None:
                sys.stderr = io.StringIO()
            
            # Ejecutar migraciones con verbosity bajo
            call_command("migrate", interactive=False, verbosity=0)
            logger.info("Migraciones ejecutadas correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando migraciones: {e}")
            # Intentar con verbosity más alto para más detalles
            try:
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()
                call_command("migrate", interactive=False, verbosity=2)
            except Exception as e2:
                logger.error(f"Error detallado en migraciones: {e2}")
            return False
            
        finally:
            # Restaurar stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
    except Exception as e:
        logger.critical(f"Error crítico al configurar migraciones: {e}")
        return False

def main():
    """Función principal del launcher"""
    try:
        # Registrar inicio
        logger.info("=" * 60)
        logger.info(f"Iniciando Facturación - {datetime.now()}")
        logger.info("=" * 60)
        
        # Parsear argumentos
        sin_ventana = "--sin-ventana" in sys.argv
        usar_puerto = 8020
        
        for arg in sys.argv:
            if arg.startswith("--puerto="):
                try:
                    usar_puerto = int(arg.split("=", 1)[1])
                except ValueError:
                    logger.warning(f"Puerto inválido, usando puerto por defecto: {usar_puerto}")
        
        # Cambiar directorio de trabajo si es ejecutable compilado
        if getattr(sys, "frozen", False):
            try:
                new_dir = Path(sys.executable).resolve().parent
                os.chdir(new_dir)
                logger.info(f"Directorio de trabajo cambiado a: {new_dir}")
            except Exception as e:
                logger.warning(f"No se pudo cambiar directorio: {e}")
        
        # Configurar Django
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        
        try:
            import django
            django.setup()
            logger.info("Django configurado correctamente")
        except Exception as e:
            logger.critical(f"Error configurando Django: {e}")
            return 1
        
        # Ejecutar migraciones de forma segura
        if not safe_migrate():
            logger.warning("Hubo problemas con las migraciones, pero continuando...")
        
        # Verificar conexión a base de datos
        try:
            from django.db import connections
            for conn in connections.all():
                conn.ensure_connection()
            logger.info("Conexión a base de datos verificada")
        except Exception as e:
            logger.error(f"Error conectando a base de datos: {e}")
        
        # Mostrar información en consola si no es modo servicio
        if not sin_ventana:
            try:
                print("=" * 58)
                print(f"📦 Facturación corriendo en http://127.0.0.1:{usar_puerto}")
                print("🔄 Cierra esta ventana para detener el sistema.")
                print(f"📝 Logs en: {Path.home() / 'FacturacionLogs'}")
                print("=" * 58)
            except:
                pass
        
        # Abrir navegador solo si no es modo servicio
        if not sin_ventana:
            try:
                webbrowser.open(f"http://127.0.0.1:{usar_puerto}")
                logger.info(f"Navegador abierto en http://127.0.0.1:{usar_puerto}")
            except Exception as e:
                logger.warning(f"No se pudo abrir navegador: {e}")
        
        # Iniciar servidor Waitress
        try:
            from waitress import serve
            from django.core.wsgi import get_wsgi_application
            
            app = get_wsgi_application()
            logger.info(f"Iniciando servidor en puerto {usar_puerto}")
            
            # Iniciar servidor
            serve(
                app,
                host="127.0.0.1",
                port=usar_puerto,
                threads=8,
                _quiet=sin_ventana
            )
            
        except KeyboardInterrupt:
            logger.info("Servidor detenido por el usuario")
            print("\n👋 Servidor detenido.")
            
        except Exception as e:
            logger.critical(f"Error iniciando servidor: {e}")
            if not sin_ventana:
                print(f"\n❌ Error: {e}")
            return 1
            
    except Exception as e:
        logger.critical(f"Error no manejado en main: {e}")
        if not sin_ventana:
            print(f"\n❌ Error crítico: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())