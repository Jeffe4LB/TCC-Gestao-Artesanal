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

from decimal import ROUND_HALF_UP, Decimal
from typing import Final

from django.core.exceptions import ValidationError

# Precisão interna para quantidades (estoque / movimentos futuros)
QUANTITY_DECIMAL_PLACES: Final[int] = 6
_QUANTIZE_TEMPLATE: Final[Decimal] = Decimal("1e-" + str(QUANTITY_DECIMAL_PLACES))


class CategoriaUnidade:
    PESO = "PESO"
    VOLUME = "VOLUME"
    UNIDADE = "UNIDADE"


class CodigoUnidade:
    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"
    UN = "UN"


# Quantidade na unidade `code` × fator = quantidade na unidade base da mesma categoria
FACTOR_TO_BASE: Final[dict[str, Decimal]] = {
    CodigoUnidade.KG: Decimal("1"),
    CodigoUnidade.G: Decimal("0.001"),
    CodigoUnidade.L: Decimal("1"),
    CodigoUnidade.ML: Decimal("0.001"),
    CodigoUnidade.UN: Decimal("1"),
}

CATEGORY_BY_UNIT: Final[dict[str, str]] = {
    CodigoUnidade.KG: CategoriaUnidade.PESO,
    CodigoUnidade.G: CategoriaUnidade.PESO,
    CodigoUnidade.L: CategoriaUnidade.VOLUME,
    CodigoUnidade.ML: CategoriaUnidade.VOLUME,
    CodigoUnidade.UN: CategoriaUnidade.UNIDADE,
}

BASE_UNIT_BY_CATEGORY: Final[dict[str, str]] = {
    CategoriaUnidade.PESO: CodigoUnidade.KG,
    CategoriaUnidade.VOLUME: CodigoUnidade.L,
    CategoriaUnidade.UNIDADE: CodigoUnidade.UN,
}

# Rótulos para admin / serializers (PT-BR)
UNIT_CODE_CHOICES: Final[tuple[tuple[str, str], ...]] = (
    (CodigoUnidade.KG, "Quilo (KG)"),
    (CodigoUnidade.G, "Grama (G)"),
    (CodigoUnidade.L, "Litro (L)"),
    (CodigoUnidade.ML, "Mililitro (ML)"),
    (CodigoUnidade.UN, "Unidade (UN)"),
)

_VALID_CODES: Final[frozenset[str]] = frozenset(FACTOR_TO_BASE.keys())

# Aliases legados (minúsculas / sinônimos) → código canônico
_LEGACY_ALIASES: Final[dict[str, str]] = {
    "un": CodigoUnidade.UN,
    "unidade": CodigoUnidade.UN,
    "und": CodigoUnidade.UN,
    "pc": CodigoUnidade.UN,
    "kg": CodigoUnidade.KG,
    "quilo": CodigoUnidade.KG,
    "g": CodigoUnidade.G,
    "gr": CodigoUnidade.G,
    "grama": CodigoUnidade.G,
    "l": CodigoUnidade.L,
    "lt": CodigoUnidade.L,
    "litro": CodigoUnidade.L,
    "ml": CodigoUnidade.ML,
    "mililitro": CodigoUnidade.ML,
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


# Aliases legados
UnitCategory = CategoriaUnidade
UnitCode = CodigoUnidade
