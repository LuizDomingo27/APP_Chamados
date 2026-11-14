import unittest

import pandas as pd

from core.config import COL_ITEM_SECUNDARIO
from core.item_secundario import (
    ARTOK_VAZIO,
    CAPAS_ARTOK,
    FILME_PLASTICO,
    LACRE,
    PAPEL_FILME,
    PAPELAO_GABARITO,
    PISTOLA,
    SACOS_ARTOK,
    classificar_item_secundario as classificar,
)
from services.material_service import resumo_itens_secundarios
from services.reposicao_parser_service import parse_reposicao_row


class ClassificacaoTests(unittest.TestCase):
    def assertItem(self, esperado, *textos):
        for texto in textos:
            with self.subTest(texto=texto):
                self.assertEqual(classificar(texto), esperado)

    def test_grafias_da_planilha(self):
        self.assertItem(FILME_PLASTICO, "Filme Plástico", "PLASTICO FILME", "Filme",
                        "Filme plástico - passante", "Plástico para fusionar passante",
                        "filme de fusionar passante")
        self.assertItem(PAPEL_FILME, "Papel filme para fusionar passantes", "Papel Filme")
        self.assertItem(LACRE, "Lacre", "LACRES", "Lacres para as OPs", "lacre para embalar OP")
        self.assertItem(PAPELAO_GABARITO, "Papelão para Gabarito", "PAPELAO", "Gabarito")
        self.assertItem(PISTOLA, "Pistola", "pistola de tag")
        self.assertItem(SACOS_ARTOK, "Sacos para Artoks", "Sacos para embalar ordens")
        self.assertItem(ARTOK_VAZIO, "Artok Vazio", "artoks")
        self.assertItem(CAPAS_ARTOK, "Capas de Artok", "Pano para artoks")

    def test_erros_de_digitacao_e_palavras_coladas(self):
        self.assertItem(PISTOLA, "Pistoa", "PISTOLLA")
        self.assertItem(FILME_PLASTICO, "Fime plastico", "FILMEPLASTICO", "plastico filmi")
        self.assertItem(LACRE, "lacrre", "LACRI")
        self.assertItem(PAPELAO_GABARITO, "papelao p/ gabarto", "PAPELAOPARAGABARITO")
        self.assertItem(ARTOK_VAZIO, "Artoc vazio", "ARTOQUE VASIO")
        self.assertItem(SACOS_ARTOK, "saco p artoc")
        self.assertItem(CAPAS_ARTOK, "capa artok")

    def test_itens_parecidos_que_nao_sao_secundarios(self):
        self.assertItem(None, "Elástico", "Laço", "LACO", "Agulha da pistola",
                        "Agulha pra pistola", "Pino", "Pente", "Tag de preço",
                        "Etiqueta de composição", "Frente", "Papel", "", None, "0000")

    def test_observacoes_so_quando_parte_sem_texto(self):
        self.assertEqual(classificar("0000", "faltou lacre"), LACRE)
        self.assertIsNone(classificar("Agulha", "agulha da pistola de tag"))


class IntegracaoTests(unittest.TestCase):
    def test_parser_preenche_coluna(self):
        notas = "Ordem de Produção Mestre: 300260622\nParte da peça: Filme Plastico\nMotivo: ACABOU"
        linha = parse_reposicao_row("26-300260622-ABC LTDA-Filme Plastico", notas)
        self.assertEqual(linha[COL_ITEM_SECUNDARIO], FILME_PLASTICO)
        linha = parse_reposicao_row("26-300260622-ABC LTDA-Frente", "Parte da peça: Frente")
        self.assertEqual(linha[COL_ITEM_SECUNDARIO], "")

    def test_resumo(self):
        df = pd.DataFrame({COL_ITEM_SECUNDARIO: [LACRE, LACRE, PISTOLA, "", ""]})
        resumo = resumo_itens_secundarios(df)
        self.assertEqual(resumo.total, 3)
        self.assertEqual(resumo.percentual, 60.0)
        self.assertEqual([(i.rotulo, i.quantidade) for i in resumo.itens], [(LACRE, 2), (PISTOLA, 1)])
        self.assertEqual(resumo_itens_secundarios(pd.DataFrame()).total, 0)


if __name__ == "__main__":
    unittest.main()
