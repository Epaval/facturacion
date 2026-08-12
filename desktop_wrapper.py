"""Wrapper con logging para diagnosticar fallos del .exe"""
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path

# Log junto al ejecutable
if getattr(sys, "frozen", False):
    log_dir = Path(sys.executable).resolve().parent
else:
    log_dir = Path(__file__).resolve().parent

log_file = log_dir / "facturacion_error.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

try:
    log("Iniciando Facturacion...")
    log(f"Python: {sys.version}")
    log(f"Executable: {sys.executable}")
    log(f"Frozen: {getattr(sys, 'frozen', False)}")
    if hasattr(sys, "_MEIPASS"):
        log(f"_MEIPASS: {sys._MEIPASS}")
    
    # Intentar importar desktop
    log("Importando desktop.main...")
    from desktop import main
    
    log("Llamando main()...")
    main()
    
except Exception as e:
    log(f"ERROR: {type(e).__name__}: {e}")
    log(f"Traceback:\n{traceback.format_exc()}")
    
    # Mantener ventana abierta si es consola
    if sys.stdout and sys.stdout.isatty():
        input("\nPresiona Enter para cerrar...")
    
    sys.exit(1)
