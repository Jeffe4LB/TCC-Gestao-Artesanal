"""
Unidades de medida (Fase 1).

Categorias: PESO, VOLUME, UNIDADE.
Cada código tem fator multiplicativo para converter quantidade → unidade base da categoria:
  - PESO  → base KG
  - VOLUME → base L
  - UNIDADE → base UN

Conversão entre categorias diferentes é proibida (ex.: KG ↔ L).
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Final

from django.core.exceptions import ValidationError

# Precisão interna para quantidades (estoque / movimentos futuros)
QUANTITY_DECIMAL_PLACES: Final[int] = 6
_QUANTIZE_TEMPLATE: Final[Decimal] = Decimal("1e-" + str(QUANTITY_DECIMAL_PLACES))


class UnitCategory:
    PESO = "PESO"
    VOLUME = "VOLUME"
    UNIDADE = "UNIDADE"


class UnitCode:
    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"
    UN = "UN"


# Quantidade na unidade `code` × fator = quantidade na unidade base da mesma categoria
FACTOR_TO_BASE: Final[dict[str, Decimal]] = {
    UnitCode.KG: Decimal("1"),
    UnitCode.G: Decimal("0.001"),
    UnitCode.L: Decimal("1"),
    UnitCode.ML: Decimal("0.001"),
    UnitCode.UN: Decimal("1"),
}

CATEGORY_BY_UNIT: Final[dict[str, str]] = {
    UnitCode.KG: UnitCategory.PESO,
    UnitCode.G: UnitCategory.PESO,
    UnitCode.L: UnitCategory.VOLUME,
    UnitCode.ML: UnitCategory.VOLUME,
    UnitCode.UN: UnitCategory.UNIDADE,
}

BASE_UNIT_BY_CATEGORY: Final[dict[str, str]] = {
    UnitCategory.PESO: UnitCode.KG,
    UnitCategory.VOLUME: UnitCode.L,
    UnitCategory.UNIDADE: UnitCode.UN,
}

# Rótulos para admin / serializers (PT-BR)
UNIT_CODE_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    (UnitCode.KG, "Quilo (KG)"),
    (UnitCode.G, "Grama (G)"),
    (UnitCode.L, "Litro (L)"),
    (UnitCode.ML, "Mililitro (ML)"),
    (UnitCode.UN, "Unidade (UN)"),
)

_VALID_CODES: Final[frozenset[str]] = frozenset(FACTOR_TO_BASE.keys())

# Aliases legados (minúsculas / sinônimos) → código canônico
_LEGACY_ALIASES: Final[dict[str, str]] = {
    "un": UnitCode.UN,
    "unidade": UnitCode.UN,
    "und": UnitCode.UN,
    "pc": UnitCode.UN,
    "kg": UnitCode.KG,
    "quilo": UnitCode.KG,
    "g": UnitCode.G,
    "gr": UnitCode.G,
    "grama": UnitCode.G,
    "l": UnitCode.L,
    "lt": UnitCode.L,
    "litro": UnitCode.L,
    "ml": UnitCode.ML,
    "mililitro": UnitCode.ML,
}


def normalize_unit_code(value: str | None) -> str:
    """
    Retorna código canônico (KG, G, L, ML, UN) ou levanta ValidationError.
    """
    raw = (value or "").strip()
    if not raw:
        raise ValidationError("Informe a unidade de medida.", code="unit_required")
    upper = raw.upper()
    if upper in _VALID_CODES:
        return upper
    lower = raw.lower()
    if lower in _LEGACY_ALIASES:
        return _LEGACY_ALIASES[lower]
    raise ValidationError(
        f"Unidade inválida: {value!r}. Use uma de: {', '.join(sorted(_VALID_CODES))}.",
        code="unit_invalid",
    )


def unit_category(unit_code: str) -> str:
    code = normalize_unit_code(unit_code)
    return CATEGORY_BY_UNIT[code]


def base_unit_for_product_unit(unit_code: str) -> str:
    """Unidade base da mesma categoria (KG, L ou UN)."""
    cat = unit_category(unit_code)
    return BASE_UNIT_BY_CATEGORY[cat]


def quantity_to_base(quantity: Decimal | str | float | int, unit_code: str) -> Decimal:
    """Converte quantidade na unidade informada para a unidade base da categoria."""
    q = Decimal(str(quantity))
    code = normalize_unit_code(unit_code)
    result = q * FACTOR_TO_BASE[code]
    return result.quantize(_QUANTIZE_TEMPLATE, rounding=ROUND_HALF_UP)


def signed_quantity_to_base(signed_quantity: Decimal | str | float | int, unit_code: str) -> Decimal:
    """Converte quantidade com sinal (ex.: ajuste -50 G) para a base mantendo o sinal."""
    q = Decimal(str(signed_quantity))
    if q == 0:
        return q.quantize(_QUANTIZE_TEMPLATE, rounding=ROUND_HALF_UP)
    sign = Decimal("1") if q > 0 else Decimal("-1")
    mag = quantity_to_base(abs(q), unit_code)
    return (sign * mag).quantize(_QUANTIZE_TEMPLATE, rounding=ROUND_HALF_UP)


def assert_same_unit_category(unit_a: str, unit_b: str) -> None:
    """Garante que duas unidades são da mesma categoria (ex.: estoque do produto vs unidade informada)."""
    if unit_category(unit_a) != unit_category(unit_b):
        raise ValidationError(
            "A unidade informada não é compatível com a categoria de medida do produto "
            f"(informada: {unit_category(unit_a)}; produto: {unit_category(unit_b)}).",
            code="unit_category_mismatch",
        )


def convert_quantity(
    quantity: Decimal | str | float | int,
    from_unit: str,
    to_unit: str,
) -> Decimal:
    """
    Converte quantidade entre duas unidades da mesma categoria.
    Ex.: 50 G → KG = 0.05
    """
    from_c = unit_category(from_unit)
    to_c = unit_category(to_unit)
    if from_c != to_c:
        raise ValidationError(
            f"Não é permitido converter entre categorias diferentes ({from_c} e {to_c}).",
            code="unit_category_mismatch",
        )
    base = quantity_to_base(quantity, from_unit)
    to = normalize_unit_code(to_unit)
    factor = FACTOR_TO_BASE[to]
    if factor == 0:
        raise ValidationError("Fator de conversão inválido.", code="unit_factor")
    out = base / factor
    return out.quantize(_QUANTIZE_TEMPLATE, rounding=ROUND_HALF_UP)
