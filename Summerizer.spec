from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path.cwd()
icon_file = project_root / "assets" / "summerizer.ico"

datas = []
binaries = []
hiddenimports = []

for package_name in ("faster_whisper", "ctranslate2", "customtkinter"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package_name)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

env_file = project_root / ".env"
if env_file.exists():
    datas.append((str(env_file), "."))

ffmpeg_dir = project_root / "ffmpeg" / "bin"
if ffmpeg_dir.exists():
    for binary_name in ("ffmpeg.exe", "ffprobe.exe"):
        binary_path = ffmpeg_dir / binary_name
        if binary_path.exists():
            binaries.append((str(binary_path), "."))


a = Analysis(
    ["gui.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "torchvision", "torchaudio"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="Summerizer",
    icon=str(icon_file) if icon_file.exists() else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
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
    upx_exclude=[],
    name="Summerizer",
)
