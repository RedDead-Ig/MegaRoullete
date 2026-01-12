# Contagens: pares/ímpares/zero, cores, altos/baixos, dúzia, coluna
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


# Números vermelhos (roleta padrão europeia/americana em cores)
RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16, 18,
    19, 21, 23, 25, 27, 30, 32, 34, 36
}


def _to_int(value: Any) -> Optional[int]:
    """Converte pra int com segurança. Retorna None se der ruim."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_coluna(numero: int) -> str:
    if numero == 0:
        return "N/A"
    r = numero % 3
    if r == 1:
        return "1ª"
    if r == 2:
        return "2ª"
    return "3ª"


def get_duzia(numero: int) -> str:
    if numero == 0:
        return "N/A"
    if 1 <= numero <= 12:
        return "1ª"
    if 13 <= numero <= 24:
        return "2ª"
    if 25 <= numero <= 36:
        return "3ª"
    return "N/A"


def get_cor(numero: int) -> str:
    if numero == 0:
        return "Verde"
    if numero in RED_NUMBERS:
        return "Vermelho"
    return "Preto"


def is_baixo(numero: int) -> bool:
    return 1 <= numero <= 18


def is_alto(numero: int) -> bool:
    return 19 <= numero <= 36


@dataclass(frozen=True)
class AnalyticsResult:
    window: int

    pares: int
    impares: int
    zeros: int

    vermelhos: int
    pretos: int
    verdes: int

    baixos: int
    altos: int

    # dominância (labels curtos: "1ª", "2ª", "3ª" ou "—")
    duzia_predominante: str
    coluna_predominante: str


def _pick_dominant(counts: Dict[str, int]) -> str:
    """
    Escolhe o dominante com desempate fixo (1ª > 2ª > 3ª).
    Se tudo 0, retorna "—".
    """
    order = ["1ª", "2ª", "3ª"]
    best_label = "—"
    best_val = 0
    for label in order:
        val = counts.get(label, 0)
        if val > best_val:
            best_val = val
            best_label = label
    return best_label if best_val > 0 else "—"


def compute_analytics(results: Iterable[Dict[str, Any]], window: int) -> AnalyticsResult:
    """
    Recebe uma lista/iterável de resultados (dict com 'result' ou 'number')
    e calcula contagens na janela atual.
    """
    pares = impares = zeros = 0
    vermelhos = pretos = verdes = 0
    baixos = altos = 0

    duzia_counts = {"1ª": 0, "2ª": 0, "3ª": 0}
    coluna_counts = {"1ª": 0, "2ª": 0, "3ª": 0}

    for r in results:
        # teu WS usa 'result' como string do número
        n = _to_int(r.get("result", r.get("number")))
        if n is None:
            continue

        # zero
        if n == 0:
            zeros += 1
            verdes += 1
            continue

        # paridade
        if n % 2 == 0:
            pares += 1
        else:
            impares += 1

        # cor
        cor = get_cor(n)
        if cor == "Vermelho":
            vermelhos += 1
        elif cor == "Preto":
            pretos += 1
        else:
            verdes += 1  # não deve cair aqui exceto 0, mas deixo safe

        # altos/baixos
        if is_baixo(n):
            baixos += 1
        elif is_alto(n):
            altos += 1

        # dúzia/coluna (não contam 0)
        d = get_duzia(n)
        c = get_coluna(n)
        if d in duzia_counts:
            duzia_counts[d] += 1
        if c in coluna_counts:
            coluna_counts[c] += 1

    duzia_pred = _pick_dominant(duzia_counts)
    coluna_pred = _pick_dominant(coluna_counts)

    return AnalyticsResult(
        window=window,
        pares=pares,
        impares=impares,
        zeros=zeros,
        vermelhos=vermelhos,
        pretos=pretos,
        verdes=verdes,
        baixos=baixos,
        altos=altos,
        duzia_predominante=duzia_pred,
        coluna_predominante=coluna_pred,
    )
