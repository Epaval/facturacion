# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (
    ['environ', 'django_environ', 'environ.environ']
    + collect_submodules('django')
    + collect_submodules('axes')
    + collect_submodules('simple_history')
    + collect_submodules('whitenoise')
    + collect_submodules('waitress')
    + [
        'django.contrib.auth.backends.ModelBackend',
        'django.contrib.auth.hashers.Argon2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.core.cache.backends.locmem.LocMemCache',
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.template.context_processors.auth',
        'django.template.context_processors.messages',
        'PIL', 'PIL.Image',
    ]
)

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

a = Analysis(
    ['desktop/launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'pytest'],
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
    console=False,
    icon='icons/icono.ico' if __import__('os').path.exists('icons/icono.ico') else None,
    disable_windowed_traceback=False,
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='Facturacion',
)
