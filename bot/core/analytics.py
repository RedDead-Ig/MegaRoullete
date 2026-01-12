from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


# =========================
# CORES
# =========================
RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16, 18,
    19, 21, 23, 25, 27, 30, 32, 34, 36
}


def get_cor(numero: int) -> str:
    if numero == 0:
        return "Verde"
    if numero in RED_NUMBERS:
        return "Vermelho"
    return "Preto"


# =========================
# DÚZIA / COLUNA
# =========================
def get_duzia_key(numero: int) -> Optional[str]:
    if numero == 0:
        return None
    if 1 <= numero <= 12:
        return "1ª"
    if 13 <= numero <= 24:
        return "2ª"
    if 25 <= numero <= 36:
        return "3ª"
    return None


def get_coluna_key(numero: int) -> Optional[str]:
    if numero == 0:
        return None
    r = numero % 3
    if r == 1:
        return "1ª"
    if r == 2:
        return "2ª"
    return "3ª"


# =========================
# REGIÕES (Call bets)
# Observação importante:
# - No cassino, "Jeu Zéro" é uma aposta que SOBREPOE Voisins.
# - Pro nosso relatório, a gente quer % LIMPO (sem duplicar número),
#   então usamos um "bucket" exclusivo:
#   1) Jeu Zéro
#   2) Voisins (sem Jeu Zéro)
#   3) Orphelins
#   4) Tiers
# Assim a soma dá 100% (em cima da janela).
# =========================
JEU_ZERO = {0, 3, 12, 15, 26, 32, 35}

VOISINS_DU_ZERO_FULL = {22, 18, 29, 7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 2, 25}
ORPHELINS = {1, 20, 14, 31, 9, 6, 34, 17}
TIERS_DU_CYLINDRE = {27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33}

# Voisins "exclusivo" (tirando os números que já caem em Jeu Zéro)
VOISINS_EXCLUSIVE = VOISINS_DU_ZERO_FULL - JEU_ZERO


def get_region_bucket(numero: int) -> str:
    """
    Retorna UM bucket exclusivo pra não duplicar contagem:
      - Jeu Zéro
      - Voisins du Zéro
      - Orphelins
      - Tiers
    """
    if numero in JEU_ZERO:
        return "Jeu Zéro"
    if numero in VOISINS_EXCLUSIVE:
        return "Voisins du Zéro"
    if numero in ORPHELINS:
        return "Orphelins"
    # o resto cai em Tiers (cobre os números restantes do cilindro)
    return "Tiers"


# =========================
# HELPERS
# =========================
def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pct(part: int, denom: int) -> int:
    if denom <= 0:
        return 0
    return int(round((part / denom) * 100))


@dataclass(frozen=True)
class RankItem:
    key: str
    pct: int


@dataclass(frozen=True)
class AnalyticsResult:
    window: int
    total_spins: int

    zeros: int
    pares: int
    impares: int

    vermelhos: int
    pretos: int

    baixos: int
    altos: int

    pct_zeros: int
    pct_pares: int
    pct_impares: int
    pct_vermelhos: int
    pct_pretos: int
    pct_baixos: int
    pct_altos: int

    duzias_rank: List[RankItem]
    colunas_rank: List[RankItem]
    regioes_rank: List[RankItem]  # agora vem 4 itens: Voisins, Tiers, Orphelins, Jeu Zéro (ordenados)


def compute_analytics(results: Iterable[Dict[str, Any]], window_label: int) -> AnalyticsResult:
    nums: List[int] = []
    for r in results:
        n = _to_int(r.get("result", r.get("number")))
        if n is None:
            continue
        if 0 <= n <= 36:
            nums.append(n)

    total_spins = len(nums)
    zeros = sum(1 for n in nums if n == 0)
    nonzero = total_spins - zeros

    # pares/ímpares: zero NÃO entra
    pares = sum(1 for n in nums if n != 0 and n % 2 == 0)
    impares = sum(1 for n in nums if n != 0 and n % 2 == 1)

    # cores: zero NÃO entra
    vermelhos = sum(1 for n in nums if n != 0 and get_cor(n) == "Vermelho")
    pretos = sum(1 for n in nums if n != 0 and get_cor(n) == "Preto")

    # baixos/altos: zero NÃO entra
    baixos = sum(1 for n in nums if 1 <= n <= 18)
    altos = sum(1 for n in nums if 19 <= n <= 36)

    # %: zeros em cima do total, resto em cima do nonzero
    pct_zeros = _pct(zeros, total_spins)
    pct_pares = _pct(pares, nonzero)
    pct_impares = _pct(impares, nonzero)
    pct_vermelhos = _pct(vermelhos, nonzero)
    pct_pretos = _pct(pretos, nonzero)
    pct_baixos = _pct(baixos, nonzero)
    pct_altos = _pct(altos, nonzero)

    # dominância (dúzias/colunas) em cima do nonzero
    duzia_counts = {"1ª": 0, "2ª": 0, "3ª": 0}
    coluna_counts = {"1ª": 0, "2ª": 0, "3ª": 0}

    for n in nums:
        if n == 0:
            continue
        d = get_duzia_key(n)
        c = get_coluna_key(n)
        if d:
            duzia_counts[d] += 1
        if c:
            coluna_counts[c] += 1

    duzias_rank = [RankItem(k, _pct(v, nonzero)) for k, v in duzia_counts.items()]
    colunas_rank = [RankItem(k, _pct(v, nonzero)) for k, v in coluna_counts.items()]

    order = {"1ª": 1, "2ª": 2, "3ª": 3}
    duzias_rank.sort(key=lambda x: (-x.pct, order.get(x.key, 99)))
    colunas_rank.sort(key=lambda x: (-x.pct, order.get(x.key, 99)))

    # regiões (4 buckets exclusivos) em cima do total_spins
    region_counts = {
        "Voisins du Zéro": 0,
        "Tiers": 0,
        "Orphelins": 0,
        "Jeu Zéro": 0,
    }

    for n in nums:
        bucket = get_region_bucket(n)
        region_counts[bucket] += 1

    regioes_rank = [RankItem(k, _pct(v, total_spins)) for k, v in region_counts.items()]

    # ranking por % desc, com ordem fixa de desempate
    region_order = {"Voisins du Zéro": 1, "Tiers": 2, "Orphelins": 3, "Jeu Zéro": 4}
    regioes_rank.sort(key=lambda x: (-x.pct, region_order.get(x.key, 99)))

    return AnalyticsResult(
        window=window_label,
        total_spins=total_spins,
        zeros=zeros,
        pares=pares,
        impares=impares,
        vermelhos=vermelhos,
        pretos=pretos,
        baixos=baixos,
        altos=altos,
        pct_zeros=pct_zeros,
        pct_pares=pct_pares,
        pct_impares=pct_impares,
        pct_vermelhos=pct_vermelhos,
        pct_pretos=pct_pretos,
        pct_baixos=pct_baixos,
        pct_altos=pct_altos,
        duzias_rank=duzias_rank,
        colunas_rank=colunas_rank,
        regioes_rank=regioes_rank,
    )
