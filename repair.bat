@echo off & cd /d "%~dp0" & title AI Debate Coach - Repair & venv\Scripts\python.exe -x "%~f0" & echo. & pause & goto :eof
# ---- Everything below is Python (the first line above is for Windows) ----
# Finds package files that were damaged during download (filled with empty
# "null bytes") and re-downloads ONLY the broken packages.
import importlib.metadata as md
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def identify(dist):
    """Name and version of a package, even when its label file is damaged."""
    folder = Path(getattr(dist, "_path", ""))
    stem = folder.name
    for ext in (".dist-info", ".egg-info"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
    guess_name, _, guess_ver = stem.partition("-")
    try:
        name = dist.metadata.get("Name")
        version = dist.metadata.get("Version")
    except Exception:
        name = version = None
    return (name or guess_name), (version or guess_ver), folder


def find_broken():
    broken = {}
    for dist in md.distributions():
        name, version, folder = identify(dist)
        if not name:
            continue
        bad = []
        try:
            label_ok = dist.metadata.get("Name") is not None
        except Exception:
            label_ok = False
        if not label_ok:
            bad.append("package label (METADATA)")
        try:
            files = dist.files or []
        except Exception:
            files = []
        for f in files:
            if f.suffix != ".py":
                continue
            try:
                if b"\x00" in f.locate().read_bytes():
                    bad.append(str(f))
            except OSError:
                bad.append(str(f) + " (missing)")
        if bad:
            broken[name.lower()] = {"version": version, "folder": folder, "files": bad}
    return broken


PENDING = Path("repair_pending.txt")
pending = PENDING.read_text().split() if PENDING.exists() else []

print()
print("  Checking installed packages for damaged files...")
broken = find_broken()

if not broken and pending:
    print("  Finishing a repair that was interrupted last time...")
    if subprocess.call([sys.executable, "-m", "pip", "install", "--no-deps", "--no-cache-dir",
                        "--default-timeout=120", "--retries", "10"] + pending) != 0:
        print("  [PROBLEM] Download failed - check your internet and run repair.bat again.")
        sys.exit(1)
    PENDING.unlink()
elif not broken:
    print("  No damaged files found.")
else:
    print(f"  Found damage in {len(broken)} package(s):")
    for name, info in broken.items():
        print(f"    - {name} {info['version']} ({len(info['files'])} bad file(s))")
    print()
    # Remove the damaged package labels so pip installs fresh copies over the top.
    specs = []
    for name, info in sorted(broken.items()):
        if info["folder"].is_dir():
            shutil.rmtree(info["folder"], ignore_errors=True)
        specs.append(f"{name}=={info['version']}" if info["version"] else name)
    specs = sorted(set(specs + pending))
    PENDING.write_text(" ".join(specs))   # remembered in case the download is interrupted
    print("  Re-downloading just those packages. Don't close this window...")
    print()
    cmd = [sys.executable, "-m", "pip", "install", "--no-deps", "--no-cache-dir",
           "--default-timeout=120", "--retries", "10"] + specs
    if subprocess.call(cmd) != 0:
        print()
        print("  [PROBLEM] Download failed - check your internet and run repair.bat again.")
        sys.exit(1)
    PENDING.unlink()
    still = find_broken()
    if still:
        print()
        print("  [PROBLEM] Some files are STILL damaged:", ", ".join(still))
        print("  Your antivirus may be blocking them. Pause the antivirus for a few minutes,")
        print("  or move the project to C:\\Projects\\ai-debate-coach, then run repair.bat again.")
        sys.exit(1)

print()
print("  Testing that everything loads...")
test = "import fastapi, uvicorn, streamlit, pandas, requests, pydantic; print('ok')"
r = subprocess.run([sys.executable, "-c", test], capture_output=True, text=True)
if r.returncode == 0:
    print()
    print("  ==========================================")
    print("   ALL GOOD! Now double-click run_backend.bat,")
    print("   then run_frontend.bat")
    print("  ==========================================")
else:
    print()
    print("  [PROBLEM] Something still won't load. Send this to Claude:")
    print(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.stdout)
