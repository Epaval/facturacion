# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# ==========================================
# HIDDEN IMPORTS
# ==========================================
hiddenimports = [
    'environ', 'django_environ', 'environ.environ',
    'psycopg2', 'psycopg2._psycopg',
    'pyserial', 'serial',
    'openpyxl',
    'requests',
    'qrcode',
    'PIL', 'PIL.Image',
    'argon2', 'argon2.exceptions', 'argon2.low_level',
    'html5lib', 'pypdf', 'svglib', 'tinycss2', 'cssselect2',
]

# Django y terceros (colectar todos los submódulos)
hiddenimports += collect_submodules('django')
hiddenimports += collect_submodules('axes')
hiddenimports += collect_submodules('simple_history')
hiddenimports += collect_submodules('whitenoise')
hiddenimports += collect_submodules('waitress')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += collect_submodules('reportlab')
hiddenimports += collect_submodules('xhtml2pdf')
hiddenimports += collect_submodules('html5lib')
hiddenimports += collect_submodules('pypdf')
hiddenimports += collect_submodules('svglib')
hiddenimports += collect_submodules('tinycss2')
hiddenimports += collect_submodules('cssselect2')
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('qrcode')
hiddenimports += collect_submodules('serial')
hiddenimports += collect_submodules('psycopg2')

# Backends y procesadores de Django
hiddenimports += [
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.core.cache.backends.locmem.LocMemCache',
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.template.context_processors.auth',
    'django.template.context_processors.messages',
]

# ==========================================
# DATAS (archivos no-Python)
# ==========================================
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('accounts', 'accounts'),
    ('clientes', 'clientes'),
    ('productos', 'productos'),
    ('ventas', 'ventas'),
    ('core', 'core'),
    ('config', 'config'),
    ('icons', 'icons'),
]

# Datos de librerías que los necesitan
datas += collect_data_files('reportlab')
datas += collect_data_files('xhtml2pdf')
datas += collect_data_files('qrcode')

# ==========================================
# ANÁLISIS
# ==========================================
a = Analysis(
    ['desktop/launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas', 'pytest',
        'pydoc_data', 'doctest', 'lib2to3', 'idlelib', 'turtle',
        'django.contrib.gis',
        'django.contrib.sites',
        'django.contrib.syndication',
        'django.contrib.sitemaps',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Facturacion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='icons/icono.ico' if __import__('os').path.exists('icons/icono.ico') else None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='Facturacion',
)
