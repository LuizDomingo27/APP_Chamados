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


def save_upload(slot: str, file_name: str, data: bytes) -> bool:
    """
    Grava o arquivo no cache. Devolve False quando não foi possível gravar
    (pasta somente leitura, disco cheio, antivírus travando o arquivo).

    Falha de cache não pode impedir o uso do dashboard — os bytes já estão
    em st.session_state e a sessão atual funciona sem o disco. O retorno
    existe para a página AVISAR o usuário de que a conveniência de reabrir
    o arquivo depois de um F5 não estará disponível, em vez de o cache
    falhar em silêncio.
    """
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path_bytes, path_name = _paths(slot)
        path_bytes.write_bytes(data)
        path_name.write_text(file_name, encoding="utf-8")
        return True
    except OSError:
        return False


def load_upload(slot: str) -> tuple[bytes, str] | None:
    """
    Devolve (bytes, nome) do último arquivo daquela página, ou None.

    Cache ilegível (arquivo truncado por desligamento no meio da escrita,
    permissão negada) equivale a cache ausente: a página cai na tela de
    upload, que é o comportamento correto e já tratado por ela.
    """
    try:
        path_bytes, path_name = _paths(slot)
        if not path_bytes.exists():
            return None
        nome = (
            path_name.read_text(encoding="utf-8")
            if path_name.exists()
            else path_bytes.name
        )
        return path_bytes.read_bytes(), nome
    except (OSError, UnicodeDecodeError):
        return None


def clear_upload(slot: str) -> None:
    """Apaga o cache da página. Arquivo já inexistente ou sem permissão de
    remoção não interrompe o fluxo de "carregar outro arquivo"."""
    for path in _paths(slot):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue
