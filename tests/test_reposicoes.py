import unittest
import io

import pandas as pd

from core.config import *
from services.data_format_service import normalize_reposicao_formats, parse_quantidade
from services.data_loader import load_dados_consolidados
from services.filter_service import filter_by_numero_chamado
from services.parser_service import parse_nome_tarefa
from services.reposicao_parser_service import parse_reposicao_row
from services.reposicao_kpi_service import ranking_oficinas_ultimas_semanas, enrich_com_indicadores_temporais, oficinas_com_reposicao_pendente


class ReposicaoTests(unittest.TestCase):
    def test_brazilian_and_iso_dates_and_required_columns(self):
        file = io.BytesIO()
        pd.DataFrame({COL_NOME_TAREFA: ['A', 'B'], COL_STATUS: [' Concluída ', 'Não iniciado'], COL_CRIADO_EM: ['05/06/2026', '2026-09-30']}).to_excel(file, sheet_name=SHEET_DADOS, index=False)
        file.seek(0)
        df = load_dados_consolidados(file)
        self.assertEqual(df[COL_CRIADO_EM].iloc[0], pd.Timestamp('2026-06-05'))
        self.assertEqual(df[COL_CRIADO_EM].iloc[1], pd.Timestamp('2026-09-30'))
        self.assertEqual(df[COL_STATUS].iloc[0], STATUS_CONCLUIDA)
        self.assertTrue(df[COL_CONCLUIDO_EM].isna().all())
        invalid = io.BytesIO()
        pd.DataFrame({'Outro': [1]}).to_excel(invalid, sheet_name=SHEET_DADOS, index=False)
        invalid.seek(0)
        with self.assertRaisesRegex(ValueError, 'Colunas obrigatórias'):
            load_dados_consolidados(invalid)

    def test_empty_label_does_not_capture_next_line(self):
        result = parse_reposicao_row('1-300280446-ABC LTDA - Cós', 'Motivo:\r\nQuantidade: 7')
        self.assertEqual(result[COL_MOTIVO], 'Não informado')
        self.assertEqual(result[COL_QUANTIDADE_REPOSICAO], '7')

    def test_missing_notes_and_divergent_order(self):
        result = parse_reposicao_row('JEANS- 1677-300280446-ABC LTDA - Cós', pd.NA)
        self.assertEqual(result[COL_OFICINA], 'ABC LTDA')
        self.assertEqual(result[COL_PARTE_PECA], 'Cós')
        self.assertEqual(result[COL_ORDEM_PRODUCAO], '300280446')
        result = parse_reposicao_row('1-300298109-ABC LTDA - Gola', 'Ordem de Produção Mestre: 300288109\nParte da peça: Gola')
        self.assertEqual(result[COL_OFICINA], 'ABC LTDA')
        self.assertEqual(result[COL_ORDEM_PRODUCAO], '300288109')

    def test_single_line_chamado_and_literal_search(self):
        result = parse_nome_tarefa('CHAMADO Nº-25128-REF.-1-OFICINA-ABC LTDA-SOLICITAÇÃO- Nota fiscal')
        self.assertEqual(result[COL_OFICINA], 'ABC LTDA')
        df = pd.DataFrame({COL_NUM_CHAMADO: ['12', '[']})
        self.assertEqual(len(filter_by_numero_chamado(df, '[')), 1)

    def test_quantity_units_and_complex_text(self):
        self.assertEqual(parse_quantidade('1.200,5 metros'), (1200.5, 'metros'))
        self.assertEqual(parse_quantidade('10 CONES'), (10.0, 'cones'))
        self.assertEqual(parse_quantidade('1.000'), (1000.0, 'Não informada'))
        self.assertEqual(parse_quantidade('3 cones e 3 rolos'), (None, None))
        df = normalize_reposicao_formats(pd.DataFrame({COL_PARTE_PECA: ['Linha', 'LINHAS', 'Etiqueta de preço', 'Etiqueta de Preço'], COL_QUANTIDADE_REPOSICAO: ['1'] * 4}))
        self.assertEqual(df[COL_PARTE_PECA].nunique(), 2)
        self.assertEqual(df['Parte da Peça Original'].iloc[0], 'Linha')

    def test_four_consecutive_weeks_with_year_boundary_and_empty_week(self):
        df = pd.DataFrame({COL_CRIADO_EM: pd.to_datetime(['2025-12-01', '2025-12-15', '2025-12-22', '2025-12-29', '2026-01-05', '2026-01-05']), COL_OFICINA: ['A', 'A', 'A', 'A', 'A', 'B']})
        ranking, start, end = ranking_oficinas_ultimas_semanas(df)
        self.assertEqual(start, pd.Timestamp('2025-12-15'))
        self.assertEqual(end, pd.Timestamp('2026-01-05'))
        self.assertEqual(ranking['Total'].sum(), 4)
        self.assertEqual(ranking.iloc[0]['Semanas com Solicitação'], 4)
        self.assertTrue((ranking.iloc[:, 2:6] > 0).all().all())
        self.assertIn('/2026', ranking.columns[4])
        filtered, other_start, _ = ranking_oficinas_ultimas_semanas(df, ['B'])
        self.assertEqual(other_start, start)
        self.assertTrue(filtered.empty)

    def test_missing_week_excludes_all_workshops(self):
        df = pd.DataFrame({COL_CRIADO_EM: pd.to_datetime(['2026-09-07', '2026-09-21', '2026-09-30']), COL_OFICINA: ['A'] * 3})
        ranking, _, _ = ranking_oficinas_ultimas_semanas(df)
        self.assertTrue(ranking.empty)

    def test_same_day_and_missing_date_pending(self):
        today = pd.Timestamp.now().normalize()
        df = pd.DataFrame({COL_CRIADO_EM: [today + pd.Timedelta(hours=8), pd.NaT], COL_CONCLUIDO_EM: [pd.NaT, pd.NaT], COL_STATUS: [STATUS_NAO_INICIADO] * 2, COL_OFICINA: ['A'] * 2})
        self.assertEqual(enrich_com_indicadores_temporais(df)[COL_DIAS_ABERTO].iloc[0], 0)
        self.assertEqual(oficinas_com_reposicao_pendente(df)['Qtd. Pendente'].sum(), 2)


if __name__ == '__main__':
    unittest.main()
