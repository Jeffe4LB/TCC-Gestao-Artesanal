"""Camada pura de exportação de relatórios em PDF e XLSX.

As funções aqui **não acessam o banco** — recebem dados já agregados pelas views
através das dataclasses ``SecaoTabela`` e ``DocumentoRelatorio``. Isso facilita
testes unitários e mantém as views responsáveis apenas por reunir os dados.

PDF: gerado com ``reportlab`` (pura Python, sem dependências de sistema).
XLSX: gerado com ``openpyxl``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Sequence

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Modelo comum de dados
# ---------------------------------------------------------------------------


Alinhamento = str  # "L" | "C" | "R"

CelulaValor = str | int | Decimal | None


@dataclass
class SecaoTabela:
    """Bloco tabular dentro de um relatório.

    Pode representar uma listagem principal (com cabeçalhos e linhas) ou um
    bloco de resumo (apenas pares chave-valor). Várias seções podem coexistir
    no mesmo relatório (ex.: financeiro em aberto tem pagar + receber).
    """

    cabecalhos: Sequence[str]
    linhas: Sequence[Sequence[CelulaValor]]
    titulo: str | None = None
    totais: Sequence[CelulaValor] | None = None
    alinhamentos: Sequence[Alinhamento] | None = None
    mensagem_vazio: str = "Sem dados para os filtros selecionados."


@dataclass
class DocumentoRelatorio:
    """Estrutura completa de um relatório exportável."""

    titulo: str
    secoes: list[SecaoTabela]
    subtitulo: str | None = None
    periodo: str | None = None
    resumo: list[tuple[str, str]] = field(default_factory=list)
    rodape: str | None = None
    orientacao_paisagem: bool = False


# ---------------------------------------------------------------------------
# Helpers de formatação
# ---------------------------------------------------------------------------


def _formatar_celula(v: CelulaValor) -> str:
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return format(v, "f")
    return str(v)


def _agora_local_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


# ---------------------------------------------------------------------------
# Exportador PDF (reportlab)
# ---------------------------------------------------------------------------


_COR_CABECALHO_TABELA = colors.HexColor("#1f3a5f")
_COR_FUNDO_CABECALHO = colors.HexColor("#eef2f7")
_COR_LINHA_ALTERNADA = colors.HexColor("#fafbfd")
_COR_TOTAL = colors.HexColor("#d9e2ec")


def _estilos_pdf():
    base = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloRelatorio",
        parent=base["Title"],
        fontSize=16,
        leading=20,
        spaceAfter=6,
        textColor=_COR_CABECALHO_TABELA,
        alignment=0,
    )
    subtitulo = ParagraphStyle(
        "SubtituloRelatorio",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.grey,
    )
    cabecalho_secao = ParagraphStyle(
        "CabecalhoSecao",
        parent=base["Heading4"],
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
        textColor=_COR_CABECALHO_TABELA,
    )
    par_normal = ParagraphStyle(
        "ParNormal",
        parent=base["Normal"],
        fontSize=9,
        leading=12,
    )
    return titulo, subtitulo, cabecalho_secao, par_normal


def _alinhamentos_to_reportlab(alinhamentos: Sequence[Alinhamento] | None, n_colunas: int):
    """Devolve lista de pares (col_index, 'LEFT|CENTER|RIGHT') para o TableStyle."""
    if not alinhamentos:
        return []
    mapa = {"L": "LEFT", "C": "CENTER", "R": "RIGHT"}
    cmds = []
    for i in range(min(n_colunas, len(alinhamentos))):
        align = mapa.get(alinhamentos[i].upper(), "LEFT")
        cmds.append(("ALIGN", (i, 1), (i, -1), align))
    return cmds


def _construir_tabela_pdf(secao: SecaoTabela) -> Table | Paragraph:
    if not secao.linhas:
        styles = getSampleStyleSheet()
        return Paragraph(
            f"<i>{secao.mensagem_vazio}</i>",
            ParagraphStyle("Vazio", parent=styles["Normal"], fontSize=9, textColor=colors.grey),
        )

    cabecalhos = [str(c) for c in secao.cabecalhos]
    linhas_formatadas = [
        [_formatar_celula(c) for c in linha] for linha in secao.linhas
    ]
    dados = [cabecalhos, *linhas_formatadas]
    if secao.totais:
        dados.append([_formatar_celula(c) for c in secao.totais])

    estilo: list = [
        ("BACKGROUND", (0, 0), (-1, 0), _COR_FUNDO_CABECALHO),
        ("TEXTCOLOR", (0, 0), (-1, 0), _COR_CABECALHO_TABELA),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dcdfe4")),
    ]
    estilo.extend(_alinhamentos_to_reportlab(secao.alinhamentos, len(cabecalhos)))

    n_linhas_dados = len(linhas_formatadas)
    for i in range(n_linhas_dados):
        if i % 2 == 1:
            estilo.append(("BACKGROUND", (0, i + 1), (-1, i + 1), _COR_LINHA_ALTERNADA))

    if secao.totais:
        estilo.append(("BACKGROUND", (0, -1), (-1, -1), _COR_TOTAL))
        estilo.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))

    tabela = Table(dados, repeatRows=1)
    tabela.setStyle(TableStyle(estilo))
    return tabela


def exportar_pdf(documento: DocumentoRelatorio, usuario: str = "") -> bytes:
    """Gera um PDF a partir de ``DocumentoRelatorio``.

    Cabeçalho fixo com título + período + data/hora de emissão.
    Rodapé com numeração de página (X de Y) e identificação do usuário.
    """

    buf = BytesIO()
    pagesize = landscape(A4) if documento.orientacao_paisagem else A4
    margem = 1.4 * cm

    pdf = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=margem,
        rightMargin=margem,
        topMargin=margem + 0.4 * cm,
        bottomMargin=margem,
        title=documento.titulo,
        author="Gestão Artesanal",
    )

    estilo_titulo, estilo_subtitulo, estilo_secao, _ = _estilos_pdf()

    flowables: list = [Paragraph(documento.titulo, estilo_titulo)]
    if documento.subtitulo:
        flowables.append(Paragraph(documento.subtitulo, estilo_subtitulo))
    info_linhas: list[str] = []
    if documento.periodo:
        info_linhas.append(f"<b>Período:</b> {documento.periodo}")
    info_linhas.append(f"<b>Emitido em:</b> {_agora_local_str()}")
    if usuario:
        info_linhas.append(f"<b>Por:</b> {usuario}")
    flowables.append(Paragraph(" &nbsp;|&nbsp; ".join(info_linhas), estilo_subtitulo))
    flowables.append(Spacer(1, 0.4 * cm))

    if documento.resumo:
        resumo_dados = [[k, v] for k, v in documento.resumo]
        resumo_tabela = Table(resumo_dados, colWidths=[6 * cm, None])
        resumo_tabela.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 0), (0, -1), _COR_FUNDO_CABECALHO),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#dcdfe4")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dcdfe4")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        flowables.append(Paragraph("Resumo", estilo_secao))
        flowables.append(resumo_tabela)
        flowables.append(Spacer(1, 0.3 * cm))

    for i, secao in enumerate(documento.secoes):
        if secao.titulo:
            flowables.append(Paragraph(secao.titulo, estilo_secao))
        flowables.append(_construir_tabela_pdf(secao))
        if i < len(documento.secoes) - 1:
            flowables.append(Spacer(1, 0.3 * cm))

    rodape_extra = documento.rodape or ""

    def _desenhar_rodape(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        pagina = canvas.getPageNumber()
        texto_pagina = f"Página {pagina}"
        if rodape_extra:
            texto_pagina = f"{rodape_extra}  ·  {texto_pagina}"
        canvas.drawString(margem, margem / 2, "Gestão Artesanal")
        canvas.drawRightString(pagesize[0] - margem, margem / 2, texto_pagina)
        canvas.restoreState()

    pdf.build(flowables, onFirstPage=_desenhar_rodape, onLaterPages=_desenhar_rodape)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Exportador XLSX (openpyxl)
# ---------------------------------------------------------------------------


_COR_AZUL = "FF1F3A5F"
_COR_FUNDO = "FFEEF2F7"
_COR_TOTAL_XLSX = "FFD9E2EC"


def _valor_xlsx(v: CelulaValor):
    """Converte para tipo nativo do openpyxl (mantém Decimal como número)."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        try:
            return float(v)
        except (TypeError, ValueError):
            return str(v)
    return v


def _formatar_cabecalho(celula) -> None:
    celula.font = Font(bold=True, color="FFFFFFFF")
    celula.fill = PatternFill("solid", fgColor=_COR_AZUL)
    celula.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _formatar_total(celula) -> None:
    celula.font = Font(bold=True)
    celula.fill = PatternFill("solid", fgColor=_COR_TOTAL_XLSX)


def _ajustar_larguras(ws, n_colunas: int, linhas_dados: list[list]) -> None:
    """Define largura de cada coluna a partir do maior conteúdo (limite 50)."""
    for col_idx in range(1, n_colunas + 1):
        letra = get_column_letter(col_idx)
        max_len = 6
        for linha in linhas_dados:
            if col_idx - 1 < len(linha) and linha[col_idx - 1] is not None:
                texto = str(linha[col_idx - 1])
                if len(texto) > max_len:
                    max_len = len(texto)
        ws.column_dimensions[letra].width = min(max_len + 2, 50)


def _escrever_secao_xlsx(ws, secao: SecaoTabela, linha_inicial: int) -> int:
    """Escreve uma seção e devolve a linha logo após o fim dela."""
    linha = linha_inicial

    if secao.titulo:
        ws.cell(row=linha, column=1, value=secao.titulo).font = Font(
            bold=True, size=12, color=_COR_AZUL
        )
        linha += 1

    cabecalhos = list(secao.cabecalhos)
    for i, header in enumerate(cabecalhos, start=1):
        celula = ws.cell(row=linha, column=i, value=header)
        _formatar_cabecalho(celula)
    ws.row_dimensions[linha].height = 22
    ws.freeze_panes = ws.cell(row=linha + 1, column=1)
    linha += 1

    if not secao.linhas:
        ws.cell(row=linha, column=1, value=secao.mensagem_vazio).font = Font(italic=True, color="FF888888")
        return linha + 2

    todas_linhas_dados = []
    for linha_dados in secao.linhas:
        for i, valor in enumerate(linha_dados, start=1):
            ws.cell(row=linha, column=i, value=_valor_xlsx(valor))
        todas_linhas_dados.append([_formatar_celula(v) for v in linha_dados])
        linha += 1

    if secao.totais:
        for i, valor in enumerate(secao.totais, start=1):
            celula = ws.cell(row=linha, column=i, value=_valor_xlsx(valor))
            _formatar_total(celula)
        linha += 1

    _ajustar_larguras(
        ws,
        len(cabecalhos),
        [cabecalhos, *todas_linhas_dados, list(secao.totais or [])],
    )

    return linha + 1  # linha em branco entre seções


def exportar_xlsx(documento: DocumentoRelatorio) -> bytes:
    """Gera um XLSX a partir de ``DocumentoRelatorio``.

    - Aba "Resumo" com cabeçalho, período, totais agregados.
    - Aba "Detalhes" com todas as seções concatenadas.
    """

    wb = Workbook()

    aba_resumo = wb.active
    aba_resumo.title = "Resumo"
    aba_resumo["A1"] = documento.titulo
    aba_resumo["A1"].font = Font(bold=True, size=14, color=_COR_AZUL)
    aba_resumo.merge_cells("A1:B1")

    linha = 2
    if documento.subtitulo:
        aba_resumo.cell(row=linha, column=1, value=documento.subtitulo).font = Font(italic=True, color="FF555555")
        aba_resumo.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=2)
        linha += 1
    if documento.periodo:
        aba_resumo.cell(row=linha, column=1, value="Período").font = Font(bold=True)
        aba_resumo.cell(row=linha, column=2, value=documento.periodo)
        linha += 1
    aba_resumo.cell(row=linha, column=1, value="Emitido em").font = Font(bold=True)
    aba_resumo.cell(row=linha, column=2, value=_agora_local_str())
    linha += 2

    if documento.resumo:
        aba_resumo.cell(row=linha, column=1, value="Indicador").font = Font(bold=True, color="FFFFFFFF")
        aba_resumo.cell(row=linha, column=1).fill = PatternFill("solid", fgColor=_COR_AZUL)
        aba_resumo.cell(row=linha, column=2, value="Valor").font = Font(bold=True, color="FFFFFFFF")
        aba_resumo.cell(row=linha, column=2).fill = PatternFill("solid", fgColor=_COR_AZUL)
        linha += 1
        for chave, valor in documento.resumo:
            aba_resumo.cell(row=linha, column=1, value=chave).font = Font(bold=True)
            aba_resumo.cell(row=linha, column=2, value=valor)
            linha += 1

    aba_resumo.column_dimensions["A"].width = 32
    aba_resumo.column_dimensions["B"].width = 32

    aba_detalhe = wb.create_sheet("Detalhes")
    linha_detalhe = 1
    for secao in documento.secoes:
        linha_detalhe = _escrever_secao_xlsx(aba_detalhe, secao, linha_detalhe)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Wrappers de resposta HTTP
# ---------------------------------------------------------------------------


_CONTENT_TYPE_PDF = "application/pdf"
_CONTENT_TYPE_XLSX = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def _filename_seguro(nome_base: str, extensao: str) -> str:
    base = nome_base.strip() or "relatorio"
    if not base.lower().endswith(f".{extensao}"):
        base = f"{base}.{extensao}"
    return base


def resposta_pdf(filename: str, documento: DocumentoRelatorio, usuario: str = "") -> HttpResponse:
    conteudo = exportar_pdf(documento, usuario=usuario)
    response = HttpResponse(conteudo, content_type=_CONTENT_TYPE_PDF)
    response["Content-Disposition"] = (
        f'attachment; filename="{_filename_seguro(filename, "pdf")}"'
    )
    return response


def resposta_xlsx(filename: str, documento: DocumentoRelatorio) -> HttpResponse:
    conteudo = exportar_xlsx(documento)
    response = HttpResponse(conteudo, content_type=_CONTENT_TYPE_XLSX)
    response["Content-Disposition"] = (
        f'attachment; filename="{_filename_seguro(filename, "xlsx")}"'
    )
    return response


# ---------------------------------------------------------------------------
# Helpers para uso nas views
# ---------------------------------------------------------------------------


FORMATOS_EXPORTACAO = ("csv", "pdf", "xlsx")


def formato_solicitado(request) -> str:
    """Devolve "csv"/"pdf"/"xlsx" se solicitado via ?export=, senão "" para JSON."""
    valor = (request.query_params.get("export") or "").strip().lower()
    return valor if valor in FORMATOS_EXPORTACAO else ""


def formatar_intervalo(de: date | None, ate: date | None) -> str | None:
    if not de or not ate:
        return None
    return f"{de.strftime('%d/%m/%Y')} a {ate.strftime('%d/%m/%Y')}"


def nome_usuario(request) -> str:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return ""
    nome = (user.get_full_name() or "").strip()
    return nome or user.get_username()
