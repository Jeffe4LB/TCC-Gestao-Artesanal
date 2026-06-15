import csv
from decimal import Decimal
from io import StringIO

from django.http import HttpResponse


def parsear_parametro_data(s: str | None):
    from django.utils.dateparse import parse_date

    if not s:
        return None
    return parse_date(s)


def texto_decimal(v) -> str:
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return format(v, "f")
    return str(v)


def resposta_csv(filename: str, header: list[str], rows: list[list]):
    """CSV UTF-8 com BOM para abrir bem no Excel."""
    buf = StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf, delimiter=";")
    w.writerow(header)
    for row in rows:
        w.writerow(row)
    response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def resposta_csv_linhas(filename: str, all_rows: list[list]):
    """CSV a partir de linhas já montadas (várias seções, etc.)."""
    buf = StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf, delimiter=";")
    for row in all_rows:
        w.writerow(row)
    response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# Aliases legados
parse_date_param = parsear_parametro_data
decimal_str = texto_decimal
csv_response = resposta_csv
csv_response_rows = resposta_csv_linhas
