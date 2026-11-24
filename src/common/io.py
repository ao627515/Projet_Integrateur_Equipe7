"""Opérations système et I/O atomiques partagées."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Écriture atomique via fichier temporaire + os.replace (anti-corruption)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calcule l'empreinte SHA-256 d'un fichier par blocs."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Charge un fichier JSON Lines ; retourne une liste vide s'il n'existe pas."""
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    """Sérialise une liste d'objets en JSON Lines de manière atomique."""
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    atomic_write_text(path, content, encoding="utf-8")


def register_nvidia_dll_dirs() -> None:
    """Enregistre les dossiers DLL NVIDIA de l'environnement virtuel (Windows CUDA/cuDNN)."""
    nvidia_dir = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    if not nvidia_dir.exists():
        return
    for dll_dir in sorted({p.parent for p in nvidia_dir.rglob("*.dll")}):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(dll_dir))
        cur_path = os.environ.get("PATH", "")
        if str(dll_dir) not in cur_path:
            os.environ["PATH"] = str(dll_dir) + os.pathsep + cur_path


@contextmanager
def process_lock(lock_path: Path):
    """Verrou exclusif anti-double-lancement avec nettoyage automatique des verrous orphelins."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        try:
            meta = json.loads(lock_path.read_text(encoding="utf-8"))
            old_pid = int(meta.get("pid", -1))
            import psutil

            if old_pid > 0 and psutil.pid_exists(old_pid):
                raise RuntimeError(
                    f"Une autre instance tourne déjà (PID={old_pid}, verrou={lock_path}). "
                    "Attendez sa fin ou arrêtez ce processus avant de relancer."
                )
            lock_path.unlink(missing_ok=True)
        except RuntimeError:
            raise
        except Exception:
            lock_path.unlink(missing_ok=True)

    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "started_at": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
        yield
    finally:
        lock_path.unlink(missing_ok=True)
