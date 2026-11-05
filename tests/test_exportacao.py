import io
import unittest
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook

from core.config import (
    COL_CATEGORIA,
    COL_CRIADO_EM,
    COL_NOME_TAREFA,
    COL_STATUS,
    SHEET_DADOS,
    STATUS_CONCLUIDA,
    STATUS_NAO_INICIADO,
    STATUS_NEGADA,
)
from services.export_service import AbaRelatorio, gerar_relatorio_excel
from services.kpi_service import (
    abertos_e_negadas_por_dia,
    abertos_por_dia,
    contagem_por_status,
    indicadores_diarios,
    indicadores_mensais,
    resumo_atendimento,
    total_pendentes,
)
from services.planilhas import marcar_negadas
from ui.exportacao import _montar_abas

CABECALHO = 9
GERADO_EM = pd.Timestamp("2026-11-05 14:30")


def _base():
    """Dia 01/09: 2 criados, 1 concluído. Dia 03/09: 1 aberto. Dia 10/10: 1 concluído."""
    return pd.DataFrame(
        {
            COL_CRIADO_EM: pd.to_datetime(
                ["2026-09-01 08:00", "2026-09-01 09:00", "2026-09-03", "2026-10-10", None], format="mixed"
            ),
            COL_STATUS: [STATUS_NAO_INICIADO, STATUS_CONCLUIDA, STATUS_NAO_INICIADO, STATUS_CONCLUIDA, STATUS_NAO_INICIADO],
        }
    )


class IndicadoresTests(unittest.TestCase):
    def test_item_aberto_conta_so_no_dia_em_que_foi_criado(self):
        out = indicadores_diarios(_base())
        self.assertEqual(out["Data"].tolist(), list(pd.to_datetime(["2026-09-01", "2026-09-03", "2026-10-10"])))
        self.assertEqual(out["Total do dia"].tolist(), [2, 1, 1])
        self.assertEqual(out["Atendidos"].tolist(), [1, 0, 1])
        self.assertEqual(out["Acumulado em aberto"].tolist(), [1, 1, 0])
        self.assertEqual(out["% Atendimento"].tolist(), [0.5, 0.0, 1.0])
        self.assertEqual(out["% Em aberto"].tolist(), [0.5, 1.0, 0.0])

    def test_acumulado_diario_bate_com_a_tabela_da_tela(self):
        diario = indicadores_diarios(_base()).set_index("Data")["Acumulado em aberto"]
        tela = abertos_por_dia(_base()).set_index("Data")["Em Aberto"]
        self.assertEqual(diario[diario > 0].sort_index().to_dict(), tela.sort_index().to_dict())

    def test_por_mes_e_resumo(self):
        out = indicadores_mensais(_base())
        self.assertEqual(out["Mês"].tolist(), list(pd.to_datetime(["2026-09-01", "2026-10-01"])))
        self.assertEqual(out["Total do mês"].tolist(), [3, 1])
        resumo = resumo_atendimento(_base())
        self.assertEqual((resumo.total, resumo.atendidos, resumo.em_aberto), (4, 2, 2))
        self.assertEqual((resumo.pct_atendimento, resumo.pct_em_aberto), (0.5, 0.5))


class ExcelTests(unittest.TestCase):
    def setUp(self):
        conteudo = gerar_relatorio_excel(
            [AbaRelatorio("Chamados", df=_base(), arquivo="a.xlsx"), AbaRelatorio("Reposição", aviso="Sem planilha")],
            GERADO_EM,
        )
        self.wb = load_workbook(io.BytesIO(conteudo))
        self.ws = self.wb["Chamados"]

    def test_uma_aba_por_modulo_e_aviso_quando_falta_planilha(self):
        self.assertEqual(self.wb.sheetnames, ["Chamados", "Reposição"])
        self.assertEqual(self.wb["Reposição"]["B3"].value, "Sem planilha")

    def test_valores_nativos_com_formato_pt_br(self):
        data = self.ws.cell(CABECALHO + 1, 2)
        self.assertEqual(data.value, datetime(2026, 9, 1))
        self.assertEqual(data.number_format, "[$-416]dd/mm/yyyy")
        self.assertEqual(self.ws.cell(CABECALHO + 1, 3).number_format, "#,##0")
        pct = self.ws.cell(CABECALHO + 1, 7)
        self.assertEqual(pct.value, 0.5)
        self.assertEqual(pct.number_format, "0.0%")
        mes = self.ws.cell(CABECALHO + 1, 10)
        self.assertEqual(mes.value, datetime(2026, 9, 1))
        self.assertEqual(mes.number_format, "[$-416]mmmm/yyyy")

    def test_linha_de_total_fecha_com_o_resumo(self):
        linha_total = CABECALHO + 1 + 3
        self.assertEqual(self.ws.cell(linha_total, 2).value, "Total")
        self.assertEqual(self.ws.cell(linha_total, 3).value, 4)
        self.assertEqual(self.ws["B6"].value, 4)
        self.assertEqual(self.ws.cell(CABECALHO + 1 + 2, 11).value, 4)

    def test_textos_e_impressao(self):
        self.assertIn("05/11/2026 às 14:30", self.ws["B3"].value)
        self.assertIn("01/09/2026 a 10/10/2026", self.ws["B3"].value)
        self.assertFalse(self.ws.sheet_view.showGridLines)
        self.assertEqual(self.ws.page_setup.orientation, "landscape")
        self.assertEqual(self.ws.freeze_panes, f"A{CABECALHO + 1}")


class FontesTests(unittest.TestCase):
    def test_planilha_ausente_ou_invalida_nao_derruba_a_outra_aba(self):
        buffer = io.BytesIO()
        pd.DataFrame(
            {
                COL_NOME_TAREFA: ["CHAMADO Nº-1-REF.-1-OFICINA-ABC LTDA-SOLICITAÇÃO- Nota fiscal"],
                COL_STATUS: [STATUS_NAO_INICIADO],
                COL_CRIADO_EM: ["2026-09-01"],
            }
        ).to_excel(buffer, sheet_name=SHEET_DADOS, index=False)

        abas = _montar_abas({"Chamados": (buffer.getvalue(), "a.xlsx"), "Reposição": None})
        self.assertEqual(len(abas[0].df), 1)
        self.assertIsNone(abas[1].df)
        self.assertIn("não foi carregada", abas[1].aviso)

        abas = _montar_abas({"Chamados": (b"isto nao e excel", "a.xlsx"), "Reposição": None})
        self.assertIsNone(abas[0].df)
        self.assertIn("Não foi possível processar", abas[0].aviso)


class NegadasTests(unittest.TestCase):
    def setUp(self):
        self.df = marcar_negadas(
            pd.DataFrame(
                {
                    COL_CRIADO_EM: pd.to_datetime(["2026-09-01", "2026-09-01", "2026-09-01", "2026-09-02", "2026-09-02"]),
                    COL_STATUS: [
                        STATUS_NAO_INICIADO,
                        STATUS_NAO_INICIADO,
                        STATUS_CONCLUIDA,
                        STATUS_NAO_INICIADO,
                        STATUS_CONCLUIDA,
                    ],
                    COL_CATEGORIA: ["REPOSIÇÃO NEGADA", " reposicao  negada ", "REPOSIÇÃO NEGADA", None, "TRIAGEM"],
                }
            )
        )

    def test_toda_negada_muda_de_situacao_e_as_demais_nao(self):
        self.assertEqual(
            self.df[COL_STATUS].tolist(),
            [STATUS_NEGADA, STATUS_NEGADA, STATUS_NEGADA, STATUS_NAO_INICIADO, STATUS_CONCLUIDA],
        )

    def test_negada_sai_do_em_aberto_e_fica_no_total(self):
        self.assertEqual(total_pendentes(self.df), 1)
        self.assertEqual(abertos_por_dia(self.df)["Em Aberto"].tolist(), [1])
        resumo = resumo_atendimento(self.df)
        self.assertEqual((resumo.total, resumo.atendidos, resumo.em_aberto, resumo.negadas), (5, 1, 1, 3))
        dia = indicadores_diarios(self.df).iloc[0]
        self.assertEqual(
            (dia["Total do dia"], dia["Atendidos"], dia["Negadas"], dia["Acumulado em aberto"]), (3, 0, 3, 0)
        )
        self.assertEqual(indicadores_mensais(self.df)["Negadas"].tolist(), [3])

    def test_tabela_da_tela_mostra_abertos_e_negadas_por_dia(self):
        tabela = abertos_e_negadas_por_dia(self.df)
        self.assertEqual(tabela["Data"].tolist(), list(pd.to_datetime(["2026-09-02", "2026-09-01"])))
        self.assertEqual(tabela["Em Aberto"].tolist(), [1, 0])
        self.assertEqual(tabela["Negadas"].tolist(), [0, 3])
        self.assertTrue(abertos_e_negadas_por_dia(self.df.iloc[0:0]).empty)

    def test_card_de_negada_so_existe_quando_ha_negada(self):
        self.assertEqual(sum(contagem_por_status(self.df).values()), 5)
        self.assertNotIn(STATUS_NEGADA, contagem_por_status(_base()))

    def test_planilha_sem_categoria_fica_como_esta(self):
        self.assertEqual(marcar_negadas(_base())[COL_STATUS].tolist(), _base()[COL_STATUS].tolist())

    def test_excel_tem_coluna_de_negadas_so_na_aba_que_tem_negadas(self):
        conteudo = gerar_relatorio_excel(
            [AbaRelatorio("Reposição", df=self.df, arquivo="r.xlsx"), AbaRelatorio("Chamados", df=_base(), arquivo="c.xlsx")],
            GERADO_EM,
        )
        wb = load_workbook(io.BytesIO(conteudo))
        ws = wb["Reposição"]
        self.assertEqual(ws.cell(CABECALHO, 5).value, "Negadas")
        self.assertEqual(ws.cell(CABECALHO, 13).value, "Negadas")
        self.assertEqual(ws.cell(CABECALHO + 1, 5).value, 3)
        self.assertEqual(ws["J5"].value, "NEGADAS")
        self.assertEqual(ws["J6"].value, 3)
        self.assertFalse(ws.column_dimensions["E"].hidden)
        self.assertTrue(wb["Chamados"].column_dimensions["E"].hidden)
        self.assertTrue(wb["Chamados"].column_dimensions["M"].hidden)


if __name__ == "__main__":
    unittest.main()
