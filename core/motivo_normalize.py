"""
core/motivo_normalize.py

O campo "Motivo" das Reposições é digitado à mão pela oficina, então a
MESMA causa aparece escrita de dezenas de formas diferentes — variando
caixa, acento, abreviação (ORDEM/OP/OM), erro de digitação
("INSULFICIENTE", "insufiente") e sinônimo ("veio faltando" = "faltou" =
"quantidade insuficiente"). Sem padronização, o gráfico "Top Motivos"
fragmenta uma única causa em 40+ fatias e nenhuma delas reflete o volume
real.

Este módulo reduz o texto livre a um conjunto fechado de motivos
canônicos, testando regras ordenadas (da causa mais específica para a
mais genérica) sobre a chave normalizada (sem acento, maiúscula). O que
não casar com nenhuma regra é apenas higienizado (caixa e pontuação
padronizadas) em vez de descartado — assim nenhuma informação se perde,
só deixa de poluir o topo do ranking.
"""

from __future__ import annotations

import re

from core.text_normalize import normalize_text_key

MOTIVO_NAO_INFORMADO = "Não informado"

# Motivos canônicos — todo texto livre é reduzido a um destes rótulos.
# Todo material que não chegou à oficina — citando ou não a Guararapes —
# é a mesma causa de negócio, então usa um rótulo único.
MOTIVO_NAO_ENVIADO_GUARARAPES = "Material não enviado pela Guararapes"
MOTIVO_INSUFICIENTE = "Quantidade insuficiente para terminar a ordem"
MOTIVO_DEFEITO = "Material com defeito"
MOTIVO_DIVERGENTE = "Material diferente do especificado na ordem"
# Erro da oficina, erro operacional e erro no processo de fabricação são o
# mesmo caso na prática (a falha aconteceu dentro da oficina), então todos
# caem num rótulo único. O corte fica de fora: é setor próprio, e juntá-lo
# à oficina esconderia de quem responde pela falha.
MOTIVO_ERRO_OFICINA = "Erro operacional da oficina"
MOTIVO_ERRO_CORTE = "Erro no setor de corte"
MOTIVO_REPROCESSO = "Reprocesso de ordem"
MOTIVO_EXTRAVIADO = "Material extraviado"
MOTIVO_ERRO_CADASTRO = "Erro de cadastro"

# A ordem importa: a primeira regra que casar vence. As causas mais
# específicas vêm antes das genéricas, porque um mesmo texto costuma
# conter palavras de várias famílias ("VEIO FALTANDO E COM DEFEITO").
#
# Os padrões incluem de propósito os erros de digitação observados na
# planilha (INSULFICIENTE, ISUFUCIENTE, GUARARSPES, ACIMETRICO...) —
# corrigi-los na origem não é possível, e sem eles a linha cairia no
# fallback e voltaria a fragmentar o ranking.
_REGRAS: list[tuple[str, re.Pattern[str]]] = [
    # "Não enviado pela Guararapes" precisa vir antes de qualquer regra de
    # falta/insuficiência: o texto quase sempre traz as duas ideias, mas o
    # que o negócio quer medir aqui é a origem (envio da Guararapes).
    (
        MOTIVO_NAO_ENVIADO_GUARARAPES,
        re.compile(
            r"N[AÃ]O\s+(?:FOI\s+|FORAM\s+|VEIO\s+|VIERAM\s+)?"
            r"(?:ENVIAD|ENVIAND|ENVIA\b|RECEB)"
            r"[\s\S]*GUARAR|GUARAR[\s\S]*N[AÃ]O\s+(?:FOI\s+|FORAM\s+)?"
            r"(?:ENVIAD|ENVIAND)"
        ),
    ),
    (
        MOTIVO_REPROCESSO,
        re.compile(r"REPROCESSO|RETRABALHO|REPROVAD|REPROVACAO|CONSERTO|CONCERTO|DESMANCH|REJEITAD"),
    ),
    (MOTIVO_EXTRAVIADO, re.compile(r"EXTRAVIAD")),
    (MOTIVO_ERRO_CADASTRO, re.compile(r"CADASTRO")),
    # O corte vem antes da oficina: "erro no processo de corte" casaria com
    # "ERRO N[OA] PROC" da regra genérica se a ordem fosse invertida.
    (
        MOTIVO_ERRO_CORTE,
        re.compile(
            r"ERRO\s+N[OA]\s+CORTE|ERRO\s+DE\s+CORTE|DEFEITO\s+NO\s+CORTE"
            r"|PROBLEMAS?\s+(?:DE|NO|NAS|NOS)\s+CORTE|CORTE\s+DIVERGENTE"
            r"|(?:PROCESSO|SETOR)\s+DE\s+CORTE|CORTAD[OA]S?\s+ERRAD"
            r"|A[SC]SIMETRIC|ACIMETRIC|ENTRADA\s+DE\s+FACA|BOCADA\s+RASA"
        ),
    ),
    (
        MOTIVO_ERRO_OFICINA,
        re.compile(
            r"ERRO\s+D[AE]\s+OFICINA|ERRO\s+OPERACIONAL|FEITO\s+ERRADO|FEIRO\s+"
            r"|LINHA\s+ERRADA|COSTURAD[OA]\s+COM\s+LINHA|PERDA\s+NA\s+|PERCA\b"
            r"|DANIFICAD[AO]S?\s+(?:NA|NO)\s+(?:PROCESSO|PRODUCAO|COSTURA)"
            r"|ERRO\s+N[OA]\s+PROC|PROCSSO|PROCESSO\s+DE\s+FABRICAC"
            r"|FALHA\s+DE\s+TECIDO"
        ),
    ),
    (
        MOTIVO_DEFEITO,
        re.compile(
            r"DEFEIT|DANIFICAD|QUEBRA|QUEBROU|MANCHAD|MOLHAD|MOFAD|MORFAD|RASG"
            r"|FURAD|PICOTAD|DESFIAD|AMASSAD|ENRUGA|ESTOURAND|ESTA\s+ESTOURANDO"
            r"|COM\s+FALHAS?|TORAD|CORTAD[AO]S?\s+N[AO]\s+"
        ),
    ),
    (
        MOTIVO_DIVERGENTE,
        re.compile(
            r"DIVERG|TONALIDADE|TROCAD|ERRAD|INCORRET|MISTURAD|PELO\s+AVESSO"
            r"|LADO\s+ERRADO|DIFERENTE\s+DO\s+ESPECIFICADO|MATERIAL\s+DIFERENTE"
            r"|DE\s+OUTRA\s+ORDEM|OUTRA\s+ORDEM|VARIACAO\s+DE\s+MP|COR\s+E\s+TECIDO\s+DIFERENTE"
            r"|VIERAM\s+JEANS|VIERAM\s+CORTADOS"
        ),
    ),
    # Família "faltou / insuficiente": a maior de todas. Cobre insuficiência
    # de quantidade escrita de qualquer forma, inclusive as grafias erradas.
    (
        MOTIVO_INSUFICIENTE,
        re.compile(
            r"INSUFICIENT|INSUFIENT|INSUFIECIENT|INSULFICIENT|INSUFUCIENT|INSUFICENT"
            r"|ISUFUCIENT|ISUFICIENT|IMSUFIENT|INSUFICIENTT|INSUFICIENTA|INSUFICENT"
            r"|INSUFIC|ISUFIC|INSULFIC|INFUFICIENT|INSUFUC"
            r"|FALT|ACABOU|ACABANDO|ACABAND|SO\s+RESTAMOS|INCOMPLET|IMCOMPLET"
            r"|SOBRANDO|A\s+MAIS|A\s+MENOS|POUC[AO]S?\b|ESTAMOS\s+SEM|ESTAMOS\s+PRECISANDO"
            r"|PRECISANDO|PRECISAMOS|N[AÃ]O\s+(?:TEM|E|SERA|VOU\s+TE|DA|DEU|VAI\s+DA|DA\s+PRA)"
            r"[\s\S]*(?:SUFICIENTE|FINALIZ|TERMINAR|CONCLUI)"
            r"|QUANTIDADE\s+(?:QUE\s+VEIO|RECEBIDA)|MENOR\s+QUE"
        ),
    ),
    # Mesma causa da primeira regra, só que sem citar a Guararapes no texto.
    # Fica aqui no fim de propósito: quando a oficina escreve "faltou" junto
    # com "não veio", o que interessa medir é a insuficiência.
    (
        MOTIVO_NAO_ENVIADO_GUARARAPES,
        re.compile(
            r"N[AÃ]O\s+(?:FOI\s+|FORAM\s+)?ENVIAD|N[AÃ]O\s+ENVIAND|N[AÃ]O\s+VEIO"
            r"|N[AÃ]O\s+VIERAM|N[AÃ]O\s+VENHO|NAO\s+VEIO|N[AÃ]O\s+RECEB|N[AÃ]O\s+ENCONTRAM"
            r"|N[AÃ]O\s+TEM(?:OS)?\b|LOTE\s+N[AÃ]O\s+ENVIADO|MATERIAL\s+N[AÃ]O\s+VEIO"
            r"|N[AÃ]O\s+VIERAM|OFICINA\s+N[AÃ]O\s+RECEBEU|N[AÃ]O\s+FOI\s+ENVIAD"
            r"|EM\s+FALTA|N\s+TEMOS|ESTAMOS\s+SEM|SEM\s+O\s+"
        ),
    ),
]

# Textos que não identificam causa alguma ("-", "000000", "F", "VEIO").
_RE_SEM_CONTEUDO = re.compile(r"^[^A-Z0-9]*$|^[\W\d_]+$")
_PLACEHOLDERS = {"F", "VEIO", "OUTROS", "XXX", "NAO INFORMADO", "-"}


def _higienizar(texto: str) -> str:
    """Padroniza a grafia de um motivo que não casou com nenhuma regra:
    colapsa espaços, remove pontuação final e aplica caixa de frase — o
    suficiente para que "FALTOU LINHA", "faltou linha" e "Faltou linha."
    deixem de contar como três motivos distintos."""
    limpo = re.sub(r"\s+", " ", str(texto or "").strip())
    limpo = limpo.rstrip(" .;,:-")
    if not limpo:
        return MOTIVO_NAO_INFORMADO
    return limpo[0].upper() + limpo[1:].lower()


def canonicalize_motivo(texto: str) -> str:
    """Reduz o motivo digitado ao rótulo canônico correspondente."""
    key = normalize_text_key(texto)
    if not key or len(key) < 3 or _RE_SEM_CONTEUDO.match(key) or key in _PLACEHOLDERS:
        return MOTIVO_NAO_INFORMADO

    for canonico, padrao in _REGRAS:
        if padrao.search(key):
            return canonico

    return _higienizar(texto)
