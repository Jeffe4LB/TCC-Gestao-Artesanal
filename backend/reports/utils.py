import csv
from decimal import Decimal
from io import StringIO

from django.http import HttpResponse


def parse_date_param(s: str | None):
    from django.utils.dateparse import parse_date

    if not s:
        return None
    return parse_date(s)


def decimal_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return format(v, "f")
    return str(v)


def csv_response(filename: str, header: list[str], rows: list[list]):
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


def csv_response_rows(filename: str, all_rows: list[list]):
    """CSV a partir de linhas já montadas (várias seções, etc.)."""
    buf = StringIO()
    buf.write("\ufeff")
    w = csv.writer(buf, delimiter=";")
    for row in all_rows:
        w.writerow(row)
    response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
