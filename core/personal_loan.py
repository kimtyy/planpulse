"""개인 소상공인 정책자금 간이 사업계획서 (상환 계산 + DOCX 빌더).

소진공/신용보증재단 정책자금 신청 시 통상 요구되는 4개 영역
(사업개요, 자금소요내역, 사업타당성, 상환계획)에 맞춘 3~5P 간이 서식.
※ 공식 제출 양식이 별도로 지정된 경우 해당 양식을 우선 사용해야 한다.
"""
from typing import Any, Dict, List

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

NAVY = "1B365D"


def calc_repayment_schedule(principal: int, annual_rate_pct: float, term_months: int,
                            grace_months: int = 0) -> List[Dict[str, int]]:
    """원리금균등상환 월별 스케줄. 거치기간에는 이자만 납부."""
    term_months = max(int(term_months), 1)
    grace_months = min(max(int(grace_months), 0), term_months - 1)
    r = annual_rate_pct / 100 / 12
    amort = term_months - grace_months
    if r > 0:
        pay = principal * r / (1 - (1 + r) ** -amort)
    else:
        pay = principal / amort
    bal = float(principal)
    paid = 0
    rows = []
    for m in range(1, term_months + 1):
        interest = bal * r
        if m <= grace_months:
            prin = 0.0
        else:
            prin = pay - interest
            if m == term_months:
                prin = bal
        prin_i = principal - paid if m == term_months else round(prin)
        paid += prin_i
        bal = max(bal - prin, 0.0)
        rows.append({"month": m, "principal": prin_i, "interest": round(interest),
                     "payment": prin_i + round(interest), "balance": principal - paid})
    return rows


def summarize_by_year(schedule: List[Dict[str, int]]) -> List[Dict[str, int]]:
    out = []
    for y in range((len(schedule) + 11) // 12):
        part = schedule[y * 12:(y + 1) * 12]
        out.append({"year": y + 1, "principal": sum(r["principal"] for r in part),
                    "interest": sum(r["interest"] for r in part),
                    "payment": sum(r["payment"] for r in part), "balance": part[-1]["balance"]})
    return out


def project_revenue(base_revenue: int, growth_rates_pct: List[float]) -> List[int]:
    out, cur = [], float(base_revenue)
    for g in growth_rates_pct:
        cur *= 1 + g / 100
        out.append(round(cur))
    return out


# ------------------------------------------------------------------ DOCX
def _shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def _font(run, size=10, bold=False, color=None):
    run.font.name = "Malgun Gothic"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Malgun Gothic")
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def _h(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.keep_with_next = True
    _font(p.add_run(text), 13, True, NAVY)


def _para(doc, text):
    p = doc.add_paragraph()
    _font(p.add_run(text or "-"), 11)


def _table(doc, rows, header=None, widths=None, label_col=False):
    n = len(rows[0]) if rows else len(header)
    t = doc.add_table(rows=0, cols=n)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    if header:
        cells = t.add_row().cells
        for c, h in zip(cells, header):
            c.text = ""
            _font(c.paragraphs[0].add_run(h), 10, True, "FFFFFF")
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            _shade(c, NAVY)
        trPr = t.rows[0]._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:tblHeader"))
    for r in rows:
        cells = t.add_row().cells
        for i, (c, v) in enumerate(zip(cells, r)):
            c.text = ""
            _font(c.paragraphs[0].add_run(str(v)), 10, label_col and i % 2 == 0)
            if label_col and i % 2 == 0:
                _shade(c, "EEF2F7")
        cantsplit = OxmlElement("w:cantSplit")
        t.rows[-1]._tr.get_or_add_trPr().append(cantsplit)
    return t


def won(v: int) -> str:
    return f"{int(v):,}원"


def build_personal_loan_docx(d: Dict[str, Any], output_path: str) -> str:
    """d: 앱에서 수집한 입력 딕셔너리. 필수 키는 app.py 의 개인 모드 폼 참고."""
    doc = docx.Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Pt(64)
        s.top_margin = s.bottom_margin = Pt(60)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _font(title.add_run("소상공인 정책자금 사업계획서 (간이)"), 20, True, NAVY)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _font(sub.add_run(f"{d['business_name']}  |  신청금액 {won(d['amount'])}"), 11)

    _h(doc, "1. 사업개요")
    _table(doc, [
        ["상호명", d["business_name"], "사업자등록번호", d["biz_no"] or "-"],
        ["업종", d["industry"], "창업연도", f"{d['start_year']}년"],
        ["대표자", d["owner_name"] or "-", "연간 매출액", won(d["annual_revenue"])],
        ["청년기업(만 39세 이하)", "해당" if d["is_youth"] else "비해당",
         "여성기업", "해당" if d["is_female"] else "비해당"],
        ["관련 업종 경력", f"{d['career_years']}년", "대표 상품/메뉴", d["signature"] or "-"],
    ], label_col=True)

    _h(doc, "2. 자금소요내역")
    f, w = d["facility_amount"], d["working_amount"]
    _table(doc, [["시설자금", won(f), d["facility_use"] or "-"],
                 ["운전자금", won(w), d["working_use"] or "-"],
                 ["합계", won(f + w), ""]],
           header=["구분", "금액", "세부 용도"])
    doc.add_paragraph()
    _para(doc, "[당면 경영애로 및 자금 필요성]")
    _para(doc, d["difficulty"])

    _h(doc, "3. 사업타당성")
    _para(doc, "[대표 상품 및 경쟁력]")
    _para(doc, d["signature"])
    _para(doc, "[주요 타깃 고객층]")
    _para(doc, d["target"])
    _para(doc, "[온·오프라인 마케팅 방안]")
    _para(doc, d["marketing"])
    _para(doc, "[대표자 역량]")
    _para(doc, d["owner_career_text"] or f"관련 업종 경력 {d['career_years']}년")

    _h(doc, "4. 매출 및 상환계획")
    rev = d["revenue_forecast"]
    _table(doc, [[f"{i+1}차년도", won(v)] for i, v in enumerate(rev)],
           header=["구분", "추정 매출액"])
    doc.add_paragraph()
    _para(doc, (f"상환조건: 원리금균등상환, 연 {d['rate']:.2f}%, 총 {d['term_months']}개월 "
                f"(거치 {d['grace_months']}개월)"))
    sched = d["schedule"]
    years = summarize_by_year(sched)
    _table(doc, [[f"{y['year']}년차", won(y["principal"]), won(y["interest"]),
                  won(y["payment"]), won(y["balance"])] for y in years],
           header=["구분", "원금", "이자", "상환액 합계", "연말 잔액"])
    doc.add_paragraph()
    _para(doc, "[월별 상환 로드맵 - 최초 12개월]")
    _table(doc, [[f"{r['month']}개월", won(r["principal"]), won(r["interest"]),
                  won(r["payment"]), won(r["balance"])] for r in sched[:12]],
           header=["회차", "원금", "이자", "납부액", "잔액"])
    if len(sched) > 12:
        _para(doc, f"※ 이후 회차는 동일 산식으로 {len(sched)}개월까지 산출됨.")

    doc.add_paragraph()
    _para(doc, "위 내용은 사실과 다름이 없음을 확인합니다.")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _font(p.add_run(f"신청인(대표자): {d['owner_name'] or d['business_name']}  (인)"), 11)

    import os
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc.save(output_path)
    return output_path
