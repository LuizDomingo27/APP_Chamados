"""
services/upload_cache.py

Guarda em disco o último arquivo enviado em cada página.

O st.session_state sobrevive à troca de página, mas morre junto com a
sessão do navegador: bastava um F5 (ou abrir o app no dia seguinte) para
a tela de upload voltar e o usuário ter que reenviar a mesma planilha.
Persistindo os bytes numa pasta local, cada página reabre sozinha com o
último arquivo usado, e o botão "Carregar outro arquivo" apaga o cache
para permitir a troca.

A pasta é local e não versionada (ver .gitignore) — é cache de
conveniência, não fonte de dados.
"""

from __future__ import annotations

from pathlib import Path

_CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache_uploads"


def _paths(slot: str) -> tuple[Path, Path]:
    """Arquivo de bytes e o sidecar com o nome original, por página."""
    return _CACHE_DIR / f"{slot}.xlsx", _CACHE_DIR / f"{slot}.name"


def save_upload(slot: str, file_name: str, data: bytes) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path_bytes, path_name = _paths(slot)
    path_bytes.write_bytes(data)
    path_name.write_text(file_name, encoding="utf-8")


def load_upload(slot: str) -> tuple[bytes, str] | None:
    """Devolve (bytes, nome) do último arquivo daquela página, ou None."""
    path_bytes, path_name = _paths(slot)
    if not path_bytes.exists():
        return None
    nome = path_name.read_text(encoding="utf-8") if path_name.exists() else path_bytes.name
    return path_bytes.read_bytes(), nome


def clear_upload(slot: str) -> None:
    for path in _paths(slot):
        path.unlink(missing_ok=True)
