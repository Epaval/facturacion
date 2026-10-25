"""
Lanzador de Facturacion - Modo Escritorio
"""
import argparse
import os
import socket
import sys
import threading
import traceback
import shutil
import subprocess
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)

# CRÍTICO: Forzar UTF-8 en Windows para evitar UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def exe_dir():
    if FROZEN:
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


EXE_DIR = exe_dir()

if FROZEN:
    DATA_BASE = os.environ.get(
        "FACTURACION_DATA",
        os.path.join(os.path.expanduser("~"), "Facturacion"),
    )
else:
    DATA_BASE = EXE_DIR

ERROR_LOG = os.path.join(DATA_BASE, "launcher_error.log")
ESTACION_CFG = os.path.join(DATA_BASE, "estacion.cfg")


# ==================== FUNCIONES PARA CLOUDFLARE ====================

def configurar_certificado_cloudflare():
    """Copia el certificado de Cloudflare incluido en el instalador al perfil del usuario"""
    try:
        # Buscar el certificado en el directorio de la aplicación
        if FROZEN:
            if hasattr(sys, '_MEIPASS'):
                cert_source = Path(sys._MEIPASS) / '.cloudflared' / 'cert.pem'
            else:
                cert_source = Path(EXE_DIR) / '.cloudflared' / 'cert.pem'
        else:
            cert_source = Path(EXE_DIR) / 'desktop' / 'cloudflared' / 'cert.pem'
        
        if not cert_source.exists():
            print(f"⚠️ Certificado no encontrado en: {cert_source}")
            return False
        
        user_cloudflared = Path(os.environ.get('USERPROFILE', os.path.expanduser('~'))) / '.cloudflared'
        user_cloudflared.mkdir(exist_ok=True)
        cert_dest = user_cloudflared / 'cert.pem'
        
        if not cert_dest.exists():
            shutil.copy2(cert_source, cert_dest)
            print(f"✅ Certificado Cloudflare instalado en {cert_dest}")
            return True
        else:
            if cert_source.stat().st_size != cert_dest.stat().st_size:
                shutil.copy2(cert_source, cert_dest)
                print(f"✅ Certificado Cloudflare actualizado")
            return True
    except Exception as e:
        print(f"❌ Error configurando certificado: {e}")
        return False


def obtener_token_tunel():
    """Obtiene el token del túnel desde archivo o variable de entorno"""
    token_file = Path(EXE_DIR) / 'tunnel_token.txt'
    if token_file.exists():
        token = token_file.read_text().strip()
        if token:
            print(f"✅ Token de túnel encontrado en archivo")
            return token
    
    token = os.environ.get('CLOUDFLARE_TOKEN', '')
    if token:
        print(f"✅ Token de túnel encontrado en variable de entorno")
        return token
    
    return None


def obtener_nombre_tunel():
    """Obtiene el nombre del túnel desde archivo o variable de entorno"""
    name_file = Path(EXE_DIR) / 'tunnel_name.txt'
    if name_file.exists():
        name = name_file.read_text().strip()
        if name:
            print(f"✅ Nombre de túnel encontrado en archivo: {name}")
            return name
    
    name = os.environ.get('CLOUDFLARE_TUNNEL', '')
    if name:
        print(f"✅ Nombre de túnel encontrado en variable de entorno: {name}")
        return name
    
    env_file = Path(EXE_DIR) / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('CLOUDFLARE_TUNNEL='):
                        name = line.strip().split('=', 1)[1].strip()
                        if name:
                            print(f"✅ Nombre de túnel encontrado en .env: {name}")
                            return name
        except Exception:
            pass
    
    return None


def iniciar_tunel_cloudflare():
    """Inicia el túnel de Cloudflare en segundo plano"""
    try:
        tunnel_token = obtener_token_tunel()
        
        tunnel_name = None
        if not tunnel_token:
            tunnel_name = obtener_nombre_tunel()
            if not tunnel_name:
                print("️ No se encontró configuración de túnel (token ni nombre)")
                return False
        
        cloudflared_path = None
        
        possible_path = Path(EXE_DIR) / 'cloudflared.exe'
        if possible_path.exists():
            cloudflared_path = str(possible_path)
        
        if not cloudflared_path:
            cloudflared_path = shutil.which('cloudflared.exe')
        
        if not cloudflared_path:
            possible_paths = [
                "C:\\Program Files\\cloudflared\\cloudflared.exe",
                "C:\\Program Files (x86)\\cloudflared\\cloudflared.exe"
            ]
            for path in possible_paths:
                if Path(path).exists():
                    cloudflared_path = path
                    break
        
        if not cloudflared_path:
            print("⚠️ No se encontró cloudflared.exe")
            return False
        
        if tunnel_token:
            cmd = [cloudflared_path, 'tunnel', 'run', '--token', tunnel_token]
            print(f"🔗 Iniciando túnel con token (longitud: {len(tunnel_token)})")
        else:
            cmd = [cloudflared_path, 'tunnel', 'run', tunnel_name]
            print(f"🔗 Iniciando túnel: {tunnel_name}")
        
        if sys.platform == 'win32':
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=EXE_DIR
            )
        else:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=EXE_DIR
            )
        
        print(f"✅ Túnel Cloudflare iniciado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error iniciando túnel: {e}")
        return False


def leer_rol_instalacion():
    """Lee el rol de instalación desde archivo generado por InnoSetup"""
    try:
        rol_file = Path(EXE_DIR) / 'rol.txt'
        if rol_file.exists():
            return rol_file.read_text().strip()
    except Exception:
        pass
    return None


def deberia_iniciar_tunel():
    """Determina si debe iniciarse el túnel (solo en modo servidor o individual)"""
    rol = leer_rol_instalacion()
    return rol in ('servidor', 'individual', None)

# ==================== FIN FUNCIONES CLOUDFLARE ====================


def reportar_error(exc_texto):
    try:
        os.makedirs(DATA_BASE, exist_ok=True)
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(exc_texto + "\n")
    except Exception:
        pass

    print(exc_texto, file=sys.stderr)

    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Error al iniciar Facturacion:\n\n{exc_texto[:800]}\n\n"
            f"Detalle completo en:\n{ERROR_LOG}",
            "Facturacion - Error",
            0x10,
        )
    except Exception:
        pass


def pedir_ip_servidor(ip_actual=""):
    """Asistente gráfico para pedir la IP del servidor (modo estación)"""
    import tkinter as tk
    from tkinter import ttk, messagebox

    resultado = {"ip": None}

    root = tk.Tk()
    root.title("Facturacion - Conectar al servidor")
    root.geometry("460x320")
    root.resizable(False, False)
    root.configure(bg="#f8fafc")

    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    frame = tk.Frame(root, bg="#f8fafc", padx=30, pady=25)
    frame.pack(fill="both", expand=True)

    titulo = tk.Label(
        frame, text="Facturación",
        font=("Segoe UI", 20, "bold"),
        bg="#f8fafc", fg="#0f172a",
    )
    titulo.pack(pady=(0, 5))

    subtitulo = tk.Label(
        frame, text="Conectar como estación",
        font=("Segoe UI", 11),
        bg="#f8fafc", fg="#64748b",
    )
    subtitulo.pack(pady=(0, 20))

    label = tk.Label(
        frame, text="IP del servidor (PC principal):",
        font=("Segoe UI", 10, "bold"),
        bg="#f8fafc", fg="#334155",
        anchor="w",
    )
    label.pack(fill="x", pady=(0, 5))

    entry_ip = ttk.Entry(frame, font=("Consolas", 13))
    entry_ip.insert(0, ip_actual)
    entry_ip.pack(fill="x", ipady=6, pady=(0, 20))
    entry_ip.focus_set()

    def conectar():
        ip = entry_ip.get().strip()
        if not ip:
            messagebox.showwarning("Atención", "Ingresa la IP del servidor")
            return
        resultado["ip"] = ip
        root.destroy()

    def cancelar():
        resultado["ip"] = None
        root.destroy()

    btn_frame = tk.Frame(frame, bg="#f8fafc")
    btn_frame.pack(fill="x", pady=(0, 15))
    btn_frame.columnconfigure(0, weight=1)
    btn_frame.columnconfigure(1, weight=1)

    btn_cancelar = tk.Button(
        btn_frame, text="Cancelar", command=cancelar,
        font=("Segoe UI", 10),
        bg="#e2e8f0", fg="#334155",
        activebackground="#cbd5e1",
        relief="flat",
        padx=20, pady=10,
        cursor="hand2",
    )
    btn_cancelar.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    btn_conectar = tk.Button(
        btn_frame, text="Conectar", command=conectar,
        font=("Segoe UI", 10, "bold"),
        bg="#0ea5e9", fg="white",
        activebackground="#0284c7", activeforeground="white",
        relief="flat",
        padx=20, pady=10,
        cursor="hand2",
    )
    btn_conectar.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    entry_ip.bind("<Return>", lambda e: conectar())

    nota = tk.Label(
        frame,
        text="Pregunta la IP de la PC principal.\nSe guardará para no volver a pedirla.",
        font=("Segoe UI", 8),
        bg="#f8fafc", fg="#94a3b8",
        justify="center",
    )
    nota.pack(fill="x", pady=(5, 0))

    root.update_idletasks()
    req_w = max(root.winfo_reqwidth() + 20, 460)
    req_h = max(root.winfo_reqheight() + 20, 340)
    root.geometry(f"{req_w}x{req_h}")
    try:
        root.eval("tk::PlaceWindow . center")
    except Exception:
        pass

    root.protocol("WM_DELETE_WINDOW", cancelar)
    root.mainloop()

    return resultado["ip"]


def leer_ip_guardada():
    try:
        return open(ESTACION_CFG, "r", encoding="utf-8").read().strip()
    except Exception:
        return ""


def guardar_ip(ip):
    try:
        os.makedirs(os.path.dirname(ESTACION_CFG), exist_ok=True)
        with open(ESTACION_CFG, "w", encoding="utf-8") as f:
            f.write(ip)
    except Exception:
        pass


def abrir_ventana(url, mantener_vivo=False):
    """Abre la app en ventana nativa; si no hay GUI, usa el navegador"""
    try:
        import webview
        webview.create_window(
            "Facturación", url,
            width=1360, height=860, min_size=(1024, 700),
        )
        webview.start()
    except Exception:
        import webbrowser
        print(f"[i] Sin GUI nativa: abriendo navegador en {url}")
        webbrowser.open(url)
        if mantener_vivo and not FROZEN:
            import time
            while True:
                time.sleep(3600)


def main():
    if FROZEN:
        sys.path.insert(0, getattr(sys, "_MEIPASS", EXE_DIR))
    else:
        sys.path.insert(0, EXE_DIR)

    parser = argparse.ArgumentParser(description="Facturacion - Modo Escritorio")
    parser.add_argument("--lan", action="store_true")
    parser.add_argument("--puerto", type=int, default=8020)
    parser.add_argument("--sin-ventana", action="store_true")
    parser.add_argument(
        "--conectar", nargs="?", const="pedir", metavar="IP_PUERTO",
        help="Modo estacion. Sin argumento: pide la IP. Con argumento: conecta directo.",
    )
    args = parser.parse_args()

    # ==================== CONFIGURAR TÚNEL (SOLO SERVIDOR/INDIVIDUAL) ====================
    if deberia_iniciar_tunel():
        print("🔧 Configurando acceso remoto...")
        configurar_certificado_cloudflare()
        
        print("🔗 Iniciando túnel Cloudflare...")
        threading.Thread(target=iniciar_tunel_cloudflare, daemon=True).start()
    # ==================== FIN CONFIGURACIÓN TÚNEL ====================

    # Modo estacion: conectar al servidor
    if args.conectar is not None:
        ip_puerto = args.conectar

        if ip_puerto == "pedir":
            ip_puerto = leer_ip_guardada()
            if not ip_puerto:
                try:
                    with open(os.path.join(os.path.dirname(sys.executable), "ip_servidor.txt"), encoding="utf-8") as f:
                        ip_puerto = f.read().strip() or None
                except Exception:
                    ip_puerto = None
            if not ip_puerto:
                ip_puerto = pedir_ip_servidor()
                if not ip_puerto:
                    sys.exit(0)
                guardar_ip(ip_puerto)

        url = ip_puerto
        if not url.startswith("http"):
            url = "http://" + url

        resto = url.split("://", 1)[1]
        if ":" not in resto:
            url += ":8020"

        abrir_ventana(url)
        sys.exit(0)

    os.environ["FACTURACION_MODO"] = "escritorio"
    os.environ["FACTURACION_BASE"] = DATA_BASE
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    django.setup()

    from django.core.management import call_command
    call_command("migrate", interactive=False, verbosity=0)

    host = "0.0.0.0" if args.lan else "127.0.0.1"

    from waitress import serve
    from django.core.wsgi import get_wsgi_application

    threading.Thread(
        target=serve,
        kwargs={"app": get_wsgi_application(), "host": host,
                "port": args.puerto, "threads": 8},
        daemon=True,
    ).start()

    url = f"http://127.0.0.1:{args.puerto}"

    if args.lan:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "TU_IP"
        print("=" * 60)
        print("  Facturación disponible en la red local:")
        print(f"  → Esta PC:   {url}")
        print(f"  → Otras PCs: http://{ip}:{args.puerto}")
        print("=" * 60)

    if args.sin_ventana:
        print(f"Servidor activo en {url}  (Ctrl+C para salir)")
        
        if args.lan:
            import tkinter as tk
            from tkinter import messagebox
            
            ventana = tk.Tk()
            ventana.title("Facturación - Servidor Activo")
            ventana.geometry("480x280")
            ventana.resizable(False, False)
            ventana.configure(bg="#f8fafc")
            ventana.attributes("-topmost", True)
            
            try:
                ventana.eval("tk::PlaceWindow . center")
            except Exception:
                pass
            
            frame = tk.Frame(ventana, bg="#f8fafc", padx=30, pady=25)
            frame.pack(fill="both", expand=True)
            
            tk.Label(
                frame, text="Facturación",
                font=("Segoe UI", 20, "bold"),
                bg="#f8fafc", fg="#0f172a",
            ).pack(pady=(0, 5))
            
            tk.Label(
                frame, text="Servidor activo en la red local",
                font=("Segoe UI", 11),
                bg="#f8fafc", fg="#059669",
            ).pack(pady=(0, 15))
            
            try:
                ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                ip = "TU_IP"
            
            tk.Label(
                frame, text=f"IP del servidor: {ip}",
                font=("Consolas", 12, "bold"),
                bg="#f8fafc", fg="#1e40af",
            ).pack(pady=(0, 5))
            
            tk.Label(
                frame, text=f"Puerto: {args.puerto}",
                font=("Segoe UI", 10),
                bg="#f8fafc", fg="#64748b",
            ).pack(pady=(0, 20))
            
            tk.Label(
                frame, text="Esta ventana debe quedar abierta.",
                font=("Segoe UI", 9),
                bg="#f8fafc", fg="#64748b",
            ).pack()

            tk.Label(
                frame, text="Las estaciones se conectan usando esta IP.",
                font=("Segoe UI", 9),
                bg="#f8fafc", fg="#64748b",
            ).pack(pady=(0, 20))
            
            def detener():
                ventana.destroy()
                import os, signal
                os.kill(os.getpid(), signal.SIGTERM)
            
            btn = tk.Button(
                frame, text="Detener servidor",
                command=detener,
                font=("Segoe UI", 10, "bold"),
                bg="#dc2626", fg="white",
                activebackground="#b91c1c",
                relief="flat",
                padx=20, pady=8,
                cursor="hand2",
            )
            btn.pack()
            
            ventana.update_idletasks()
            req_w = max(ventana.winfo_reqwidth() + 20, 480)
            req_h = max(ventana.winfo_reqheight() + 20, 300)
            ventana.geometry(f"{req_w}x{req_h}")
            try:
                ventana.eval("tk::PlaceWindow . center")
            except Exception:
                pass

            ventana.protocol("WM_DELETE_WINDOW", detener)
            ventana.mainloop()
        else:
            import time
            while True:
                time.sleep(3600)

    abrir_ventana(url, mantener_vivo=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        reportar_error(traceback.format_exc())
        sys.exit(1)
