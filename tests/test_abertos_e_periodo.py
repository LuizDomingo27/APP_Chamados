import unittest
from datetime import date

import pandas as pd

from core.config import COL_CRIADO_EM, COL_STATUS, STATUS_CONCLUIDA, STATUS_EM_ANDAMENTO, STATUS_NAO_INICIADO
from services.filter_service import ha_filtro_de_periodo, recorte_tendencia
from services.kpi_service import abertos_por_dia, card_nao_iniciado_do_dia, nao_iniciados_do_dia

HOJE = pd.Timestamp("2026-11-05")


def _df(*linhas):
    return pd.DataFrame(
        {
            COL_CRIADO_EM: pd.to_datetime([data for data, _ in linhas]),
            COL_STATUS: [status for _, status in linhas],
        }
    )


class AbertosPorDiaTests(unittest.TestCase):
    def test_soma_abertos_do_dia_e_omite_dias_sem_aberto(self):
        df = _df(
            ("2026-09-20 08:00", STATUS_NAO_INICIADO),
            ("2026-09-20 17:30", STATUS_EM_ANDAMENTO),
            ("2026-09-20 18:00", STATUS_CONCLUIDA),
            ("2026-09-21 09:00", STATUS_CONCLUIDA),
            ("2026-10-01 09:00", STATUS_NAO_INICIADO),
            (None, STATUS_NAO_INICIADO),
        )
        out = abertos_por_dia(df)
        self.assertEqual(list(out.columns), ["Data", "Em Aberto"])
        self.assertEqual(out["Data"].tolist(), [pd.Timestamp("2026-10-01"), pd.Timestamp("2026-09-20")])
        self.assertEqual(out["Em Aberto"].tolist(), [1, 2])

    def test_sem_abertos_devolve_tabela_vazia(self):
        out = abertos_por_dia(_df(("2026-09-20", STATUS_CONCLUIDA)))
        self.assertTrue(out.empty)
        self.assertEqual(out["Em Aberto"].sum(), 0)


class CardNaoIniciadoTests(unittest.TestCase):
    def test_conta_somente_nao_iniciados_criados_no_dia(self):
        df = _df(
            ("2026-11-05 08:00", STATUS_NAO_INICIADO),
            ("2026-11-05 23:59", STATUS_NAO_INICIADO),
            ("2026-11-05 10:00", STATUS_EM_ANDAMENTO),
            ("2026-11-05 11:00", STATUS_CONCLUIDA),
            ("2026-11-04 10:00", STATUS_NAO_INICIADO),
            (None, STATUS_NAO_INICIADO),
        )
        self.assertEqual(nao_iniciados_do_dia(df, HOJE), (2, 4))
        card = card_nao_iniciado_do_dia(df, HOJE)[STATUS_NAO_INICIADO]
        self.assertEqual(card["value"], 2)
        self.assertEqual(card["progress"], 50.0)
        self.assertIn("05/11/2026", card["subtitle"])

    def test_dia_sem_criacao_nao_divide_por_zero(self):
        card = card_nao_iniciado_do_dia(_df(("2026-11-04", STATUS_NAO_INICIADO)), HOJE)
        self.assertEqual(card[STATUS_NAO_INICIADO]["value"], 0)
        self.assertEqual(card[STATUS_NAO_INICIADO]["progress"], 0.0)


class PeriodoTests(unittest.TestCase):
    def setUp(self):
        self.df = _df(
            ("2026-09-15 10:00", STATUS_CONCLUIDA),
            ("2026-11-01 10:00", STATUS_CONCLUIDA),
            ("2026-11-05 10:00", STATUS_NAO_INICIADO),
        )

    def test_intervalo_completo_nao_conta_como_filtro(self):
        inicio, fim = date(2026, 9, 15), date(2026, 11, 5)
        self.assertFalse(ha_filtro_de_periodo(self.df, inicio, fim, [], []))
        self.assertTrue(ha_filtro_de_periodo(self.df, date(2026, 10, 1), fim, [], []))
        self.assertTrue(ha_filtro_de_periodo(self.df, inicio, date(2026, 11, 1), [], []))
        self.assertTrue(ha_filtro_de_periodo(self.df, inicio, fim, [], ["Setembro/2026"]))
        self.assertTrue(ha_filtro_de_periodo(self.df, inicio, fim, ["Semana 38/2026"], []))

    def test_sem_filtro_tendencia_mostra_so_mes_vigente(self):
        recorte = recorte_tendencia(self.df, False, HOJE)
        self.assertEqual(len(recorte.df), 2)
        self.assertIn("Novembro/2026", recorte.legenda)

    def test_com_filtro_tendencia_respeita_o_recorte(self):
        recorte = recorte_tendencia(self.df, True, HOJE)
        self.assertEqual(len(recorte.df), 3)
        self.assertEqual(recorte.legenda, "")

    def test_mes_vigente_sem_dados_nao_cai_para_outro_mes(self):
        recorte = recorte_tendencia(self.df, False, pd.Timestamp("2026-12-10"))
        self.assertTrue(recorte.df.empty)
        self.assertIn("Dezembro/2026", recorte.aviso_vazio)
        self.assertIn("05/11/2026", recorte.aviso_vazio)


if __name__ == "__main__":
    unittest.main()
