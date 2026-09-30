"""
ui/icons.py

Conjunto fechado de ícones de TRAÇO em SVG inline.

Por que SVG e não emoji: o emoji é renderizado pela fonte do sistema —
muda de desenho e de cor entre Windows/macOS/Android, ignora a cor do
acento do card e destoa do resto da interface. Os ícones aqui herdam
`currentColor`, então acompanham a cor do acento do componente, e o
desenho é idêntico em qualquer máquina.

Por que inline e não arquivo: zero requisição de rede, nada a versionar
em assets e nada que quebre se a pasta for movida.

Os traçados usam viewBox 24x24, `fill="none"` e stroke de 1.8 — o mesmo
peso visual em todos os ícones, que é o que faz o conjunto parecer uma
família e não uma colagem.
"""

from __future__ import annotations

from urllib.parse import quote

# Só o conteúdo interno do <svg>: o invólucro é montado por _svg(), para
# que largura/cor/stroke fiquem definidos num único lugar.
_PATHS: dict[str, str] = {
    # Documento / registro
    "clipboard": (
        '<path d="M9 4.5h6v2H9z"/>'
        '<path d="M9 5.5H6.5A1 1 0 0 0 5.5 6.5v13a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-13'
        'a1 1 0 0 0-1-1H15"/>'
        '<path d="M9 11.5h6M9 15h4"/>'
    ),
    # Tempo
    "calendar": (
        '<path d="M5.5 7.5h13a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1h-13a1 1 0 0 1-1-1v-11'
        'a1 1 0 0 1 1-1z"/>'
        '<path d="M8.5 4.5v4M15.5 4.5v4M4.5 11.5h15"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="8.2"/>'
        '<path d="M12 7.4V12l3.4 2"/>'
    ),
    "hourglass": (
        '<path d="M7 4.2h10M7 19.8h10"/>'
        '<path d="M8 4.2c0 4 4 4.3 4 7.8s-4 3.8-4 7.8"/>'
        '<path d="M16 4.2c0 4-4 4.3-4 7.8s4 3.8 4 7.8"/>'
    ),
    "refresh": (
        '<path d="M19.8 12a7.8 7.8 0 1 1-2.3-5.5"/>'
        '<path d="M19.8 4.4v4.2h-4.2"/>'
    ),
    # Estado
    "check": (
        '<circle cx="12" cy="12" r="8.2"/>'
        '<path d="m8.4 12.2 2.5 2.5 4.7-5.2"/>'
    ),
    # Domínio
    "factory": (
        '<path d="M4.4 19.8V10.6l4.6 2.8v-2.8l4.6 2.8v-2.8l6 3.6v5.6z"/>'
        '<path d="M3.4 19.8h17.2M9 16.4h.01M13.6 16.4h.01"/>'
    ),
    "tag": (
        '<path d="M4.4 4.4h7.2l8 8-7.2 7.2-8-8z"/>'
        '<circle cx="8" cy="8" r="1.3"/>'
    ),
    "spool": (
        '<path d="m12 3.4 8.4 4.6-8.4 4.6L3.6 8z"/>'
        '<path d="m3.6 12.4 8.4 4.6 8.4-4.6"/>'
        '<path d="m3.6 16.4 8.4 4.6 8.4-4.6"/>'
    ),
    "scales": (
        '<path d="M12 5v14M6.6 19h10.8M4.4 9.4h15.2"/>'
        '<path d="M7 9.4 4.4 14.6h5.2zM17 9.4l-2.6 5.2h5.2z"/>'
    ),
    "chart": (
        '<path d="M5 20v-8M11 20V8M17 20v-5M23 20V4" transform="translate(-2)"/>'
        '<path d="M4 11 10 6l6 4 6-5" transform="translate(-1)" opacity=".6"/>'
    ),
    # Marcador neutro — usado quando o chamador não informa ícone.
    "dot": '<circle cx="12" cy="12" r="3.4" fill="currentColor" stroke="none"/>',
}

# Ícone usado quando o nome pedido não existe. Nome errado não levanta
# exceção nem deixa um buraco no card: sai o marcador neutro, e a ausência
# do desenho esperado é visível na tela.
_FALLBACK = "dot"


def _svg(inner: str, size: str = "24") -> str:
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true" focusable="false">'
        f"{inner}</svg>"
    )


def icon(name: str, size: str = "24") -> str:
    """
    Devolve o markup SVG do ícone `name`, herdando cor de `currentColor`.

    Nome desconhecido (ou vazio/None) cai no marcador neutro em vez de
    levantar KeyError: um ícone é decoração e não deve derrubar a página.
    """
    chave = name if isinstance(name, str) and name in _PATHS else _FALLBACK
    return _svg(_PATHS[chave], size=size)


def icon_data_uri(name: str, color: str = "currentColor") -> str:
    """
    Mesmo ícone como data URI, para uso em `mask-image` no CSS.

    Existe para os itens do rail de navegação: o rótulo do st.button é
    texto puro e não aceita markup, então o ícone entra como máscara no
    ::before da regra CSS daquele botão.
    """
    chave = name if isinstance(name, str) and name in _PATHS else _FALLBACK
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{_PATHS[chave]}</svg>'
    )
    return f"url(\"data:image/svg+xml,{quote(svg, safe='')}\")"
