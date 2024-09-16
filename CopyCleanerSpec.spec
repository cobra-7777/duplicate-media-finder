# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/', 'resources/')],
    hiddenimports=[
        'cv2.VideoCapture', 
        'cv2.CAP_PROP_POS_FRAMES', 
        'cv2.cvtColor', 
        'cv2.COLOR_BGR2RGB', 
        'cv2.CAP_PROP_FPS', 
        'cv2.CAP_PROP_FRAME_HEIGHT', 
        'cv2.CAP_PROP_FRAME_WIDTH', 
        'cv2.CAP_PROP_FRAME_COUNT',
        'numpy',
        'imagehash',
        'PIL',
        'PyQt5',
        'cv2',
        'numpy.core._multiarray_tests',
        'scipy',
    ],
    hookspath=['C:\\Users\\Cobra\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\PyInstaller\\hooks'],
    hooksconfig={},
    runtime_hooks=['multiprocessing_hook.py'],
    excludes=['imp', 
        'termios', 
        'java', 
        'torch',
        'sympy',
        'matplotlib',
        'pandas',
        'pytest',
        'lxml',
        'psutil',
        'jinja2',
        'tensorflow',
        'sklearn',
        'opencv-python'
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CopyCleaner - Easy Media Deduplication',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/IconOnly.ico',
    manifest='app.manifest',
)