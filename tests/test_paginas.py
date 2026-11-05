"""Roda as duas páginas de verdade (sem navegador) com uma planilha sintética.

Os bytes entram pelo session_state, então o cache local de uploads não é lido.
"""

import io
import unittest
from datetime import date
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from core.config import (
    COL_CATEGORIA,
    COL_CRIADO_EM,
    COL_NOME_TAREFA,
    COL_STATUS,
    SHEET_DADOS,
    STATUS_CONCLUIDA,
    STATUS_NAO_INICIADO,
)
from core.utils import hoje_local

RAIZ = Path(__file__).resolve().parents[1]
PAGINAS = {
    "pages/chamados.py": ("ppc", "CHAMADO Nº-{i}-REF.-1-OFICINA-ABC LTDA-SOLICITAÇÃO- Nota fiscal"),
    "pages/reposicoes.py": ("rep", "{i}-300280446-SERRANA TEXTIL LTDA - Cós"),
}


def _planilha(modelo: str) -> tuple[bytes, date]:
    """Dois não iniciados + um concluído hoje e, 70 dias antes, três não iniciados."""
    hoje = hoje_local()
    antigo = hoje - pd.Timedelta(days=70)
    linhas = [
        (hoje, STATUS_NAO_INICIADO),
        (hoje, STATUS_NAO_INICIADO),
        (hoje, STATUS_CONCLUIDA),
        (antigo, STATUS_NAO_INICIADO),
        (antigo, STATUS_NAO_INICIADO),
        (antigo, STATUS_NAO_INICIADO),
    ]
    buffer = io.BytesIO()
    pd.DataFrame(
        {
            COL_NOME_TAREFA: [modelo.format(i=i) for i in range(len(linhas))],
            COL_STATUS: [status for _, status in linhas],
            COL_CRIADO_EM: [data for data, _ in linhas],
            COL_CATEGORIA: ["Reposição"] * len(linhas),
        }
    ).to_excel(buffer, sheet_name=SHEET_DADOS, index=False)
    return buffer.getvalue(), antigo.date()


def _textos(app: AppTest) -> str:
    return "\n".join(str(m.value) for m in [*app.markdown, *app.caption, *app.info, *app.warning])


class PaginasTests(unittest.TestCase):
    def _abrir(self, pagina: str) -> tuple[AppTest, str, date]:
        prefixo, modelo = PAGINAS[pagina]
        bytes_planilha, antigo = _planilha(modelo)
        app = AppTest.from_file(str(RAIZ / pagina), default_timeout=60)
        app.session_state[f"{prefixo}_file_bytes"] = bytes_planilha
        app.session_state[f"{prefixo}_file_name"] = "teste.xlsx"
        app.run()
        self.assertFalse(app.exception, app.exception)
        return app, prefixo, antigo

    def test_sem_filtro_card_olha_o_dia_e_grafico_o_mes_vigente(self):
        for pagina in PAGINAS:
            with self.subTest(pagina):
                app, _, _ = self._abrir(pagina)
                textos = _textos(app)
                self.assertIn(f"criados hoje ({hoje_local():%d/%m/%Y})", textos)
                self.assertIn("67% dos criados hoje", textos)
                self.assertIn("mês vigente", textos)
                self.assertIn("Em aberto por dia (5)", textos)

    def test_calendarios_filtram_card_e_tendencia(self):
        for pagina in PAGINAS:
            with self.subTest(pagina):
                app, prefixo, antigo = self._abrir(pagina)
                app.date_input(key=f"{prefixo}_data_fim").set_value(antigo).run()
                self.assertFalse(app.exception, app.exception)
                textos = _textos(app)
                self.assertNotIn("criados hoje", textos)
                self.assertNotIn("mês vigente", textos)
                self.assertIn("aguardando início", textos)
                self.assertIn("Em aberto por dia (3)", textos)

    def test_data_inicio_depois_da_data_fim_avisa(self):
        for pagina in PAGINAS:
            with self.subTest(pagina):
                app, prefixo, antigo = self._abrir(pagina)
                app.date_input(key=f"{prefixo}_data_fim").set_value(antigo).run()
                app.date_input(key=f"{prefixo}_data_inicio").set_value(hoje_local().date()).run()
                self.assertFalse(app.exception, app.exception)
                self.assertIn("data início está depois", _textos(app))


if __name__ == "__main__":
    unittest.main()
