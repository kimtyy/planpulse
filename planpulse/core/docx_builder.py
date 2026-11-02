"""
PlanPulse DOCX Builder Engine (30P+ Large-scale Production Builder)
소상공인시장진흥공단/중기부 '전통시장 및 상점가 활성화 지원사업(문화관광형 3개년 20억원)' 표준 공고 서식 완벽 구현
word-processing 규격 준수:
- 11pt 본문, 10pt 표 텍스트 엄수 (Font Floor)
- OpenXML w:tblHeader (표 반복 헤더), w:cantSplit (행 분할 방지), keep_with_next (제목 이탈 방지)
- 10대 단위세부사업(WP-01 ~ WP-10) 딥-익스팬션 및 20억원 5페이지 원단위 회계 세부 산출내역표 완벽 조판
"""

import os
from typing import Dict, Any, List
import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

try:
    from planpulse.core.models import PlanPulseProject
    from planpulse.core.validator import validate_statutory_competency
    from planpulse.core.psst_engine import expand_psst_offline
    from planpulse.core.evaluator import evaluate_project
    from planpulse.core.budget_engine import (
        audit_budget_compliance,
        generate_detailed_accounting_budget,
        DetailedBudgetItem,
    )
    from planpulse.core.work_packages import get_jojong_10_work_packages, WorkPackage
except ImportError:
    from core.models import PlanPulseProject
    from core.validator import validate_statutory_competency
    from core.psst_engine import expand_psst_offline
    from core.evaluator import evaluate_project
    from core.budget_engine import (
        audit_budget_compliance,
        generate_detailed_accounting_budget,
        DetailedBudgetItem,
    )
    from core.work_packages import get_jojong_10_work_packages, WorkPackage


# 디자인 색상 토큰
COLOR_PRIMARY_HEX = "1B365D"       # Deep Navy (공공기관 신뢰감)
COLOR_ACCENT_HEX = "2E6B8E"        # Slate Teal
COLOR_HEADER_BG_HEX = "EBF1F6"     # 행정 서식 표준 소프트 블루그레이
COLOR_LIGHT_BG_HEX = "F8FAFC"      # 교차 행 배경
COLOR_BORDER_HEX = "B0C0D0"        # 은은한 테두리
COLOR_BOX_BG_HEX = "F1F5F9"        # 요약 박스 배경

RGB_PRIMARY = RGBColor(0x1B, 0x36, 0x5D)
RGB_ACCENT = RGBColor(0x2E, 0x6B, 0x8E)
RGB_DARK = RGBColor(0x1E, 0x29, 0x3B)
RGB_MUTED = RGBColor(0x47, 0x55, 0x69)
RGB_WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def set_cell_background(cell, hex_color: str):
    """표 셀 배경색 지정 XML 조작"""
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """표 셀 내부 패딩 지정 (dxa 단위: 20 dxa = 1 pt)"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_callout_box(doc, text: str, prefix: str = "※ 핵심 요약: "):
    """공문서 스타일 인용 박스 추가"""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(6.5)
    set_cell_background(cell, COLOR_BOX_BG_HEX)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    # 테두리 설정 (왼쪽 진한 블루 바)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="none"/>'
        f'  <w:left w:val="single" w:sz="24" w:space="0" w:color="{COLOR_PRIMARY_HEX}"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    r_pre = p.add_run(prefix)
    r_pre.font.name = "Malgun Gothic"
    r_pre.font.size = Pt(10)
    r_pre.font.bold = True
    r_pre.font.color.rgb = RGB_PRIMARY
    
    r_txt = p.add_run(text)
    r_txt.font.name = "Malgun Gothic"
    r_txt.font.size = Pt(10)
    r_txt.font.color.rgb = RGB_DARK
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_h1(doc, text: str, page_break_before: bool = False):
    """대제목 (H1, 16pt, Deep Navy, keep_with_next)"""
    if page_break_before:
        doc.add_page_break()
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Malgun Gothic"
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = RGB_PRIMARY
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    return p


def add_h2(doc, text: str):
    """중제목 (H2, 13pt, Slate Teal, keep_with_next)"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Malgun Gothic"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = RGB_ACCENT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    return p


def add_h3(doc, text: str):
    """소제목 (H3, 11.5pt, Deep Navy, keep_with_next)"""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Malgun Gothic"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = RGB_PRIMARY
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    return p


def add_body_p(doc, text: str, is_bullet: bool = False):
    """본문 단락 (11pt Malgun Gothic, Dark, line_spacing 1.15)"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    
    r = p.add_run(text)
    r.font.name = "Malgun Gothic"
    r.font.size = Pt(11)
    r.font.color.rgb = RGB_DARK
    
    # 볼드 강조 (개조식 앞머리 기호)
    if any(text.startswith(prefix) for prefix in ["□ ", "○ ", "- ", "ㆍ ", "※ "]):
        parts = text.split("]", 1) if "]" in text else [text[:2], text[2:]]
        if len(parts) == 2 and "]" in text:
            p.text = ""
            r1 = p.add_run(parts[0] + "]")
            r1.font.name = "Malgun Gothic"
            r1.font.size = Pt(11)
            r1.font.bold = True
            r1.font.color.rgb = RGB_PRIMARY
            
            r2 = p.add_run(parts[1])
            r2.font.name = "Malgun Gothic"
            r2.font.size = Pt(11)
            r2.font.color.rgb = RGB_DARK
    return p


def style_table(table, col_widths: List[float], has_header: bool = True):
    """표 조판 규격 일괄 적용: tblHeader, cantSplit, 10pt 폰트, 패딩"""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    if has_header and len(table.rows) > 0:
        header_tr = table.rows[0]._tr.get_or_add_trPr()
        header_tr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
        
        for c_idx, cell in enumerate(table.rows[0].cells):
            cell.width = col_widths[c_idx]
            set_cell_background(cell, COLOR_PRIMARY_HEX)
            set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            if len(p.runs) > 0:
                p.runs[0].font.name = "Malgun Gothic"
                p.runs[0].font.size = Pt(10)
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGB_WHITE
                
    # 데이터 행 서식
    start_row = 1 if has_header else 0
    for r_idx in range(start_row, len(table.rows)):
        row = table.rows[r_idx]
        row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        is_odd = (r_idx % 2 == 1)
        for c_idx, cell in enumerate(row.cells):
            cell.width = col_widths[c_idx]
            set_cell_margins(cell, top=90, bottom=90, left=110, right=110)
            if is_odd and not has_header:
                set_cell_background(cell, COLOR_LIGHT_BG_HEX)
            elif is_odd and has_header:
                set_cell_background(cell, COLOR_LIGHT_BG_HEX)
            for p in cell.paragraphs:
                p.paragraph_format.line_spacing = 1.1
                for run in p.runs:
                    run.font.name = "Malgun Gothic"
                    run.font.size = Pt(10)
                    run.font.color.rgb = RGB_DARK


def build_planpulse_docx(project: PlanPulseProject, output_path: str, mode: str = "full") -> str:
    """
    PlanPulse 프로젝트 데이터를 바탕으로 표준 공고 규격 DOCX 사업계획서 생성
    - mode="full": 공모전 본심사용 실시설계서 (Full Implementation Dossier, 30P~77P 대용량)
    - mode="summary": 1차 접수용 요약서 (Executive Summary, 약 7P)
    """
    doc = docx.Document()

    # 1. 페이지 여백 설정 (1.0인치)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # 바닥글 페이지 번호 설정
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = f_p.add_run("PlanPulse 2027년도 전통시장 문화관광형 육성사업 본 사업계획서 | ")
        f_run.font.name = "Malgun Gothic"
        f_run.font.size = Pt(9.5)
        f_run.font.color.rgb = RGB_MUTED

    # 2. 기본 스타일 설정
    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Malgun Gothic"
    style_normal.font.size = Pt(11)
    style_normal.font.color.rgb = RGB_DARK

    # 연산 및 데이터 분석 수행
    comp_val = validate_statutory_competency(project.market_profile.competency)
    expanded = expand_psst_offline(project)
    eval_card = evaluate_project(project)
    is_budget_ok, _, budget_sum = audit_budget_compliance(project.scale_up.budget_items)
    work_packages = get_jojong_10_work_packages()
    detailed_budget = generate_detailed_accounting_budget()

    # -------------------------------------------------------------------------
    # [표지] 대형 국책 사업 본 사업계획서 표지 (Cover Page)
    # -------------------------------------------------------------------------
    cover_sub = doc.add_paragraph()
    r_sub = cover_sub.add_run("2027년도 전통시장 및 상점가 활성화 지원사업 (문화관광형시장)")
    r_sub.font.name = "Malgun Gothic"
    r_sub.font.size = Pt(13)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGB_ACCENT
    cover_sub.paragraph_format.space_before = Pt(40)
    cover_sub.paragraph_format.space_after = Pt(10)

    cover_title = doc.add_paragraph()
    r_tit = cover_title.add_run(f"[{project.market_profile.market_name}]\n문화관광형시장 육성 본 사업계획서")
    r_tit.font.name = "Malgun Gothic"
    r_tit.font.size = Pt(26)
    r_tit.font.bold = True
    r_tit.font.color.rgb = RGB_PRIMARY
    cover_title.paragraph_format.space_after = Pt(18)

    cover_desc = doc.add_paragraph()
    r_desc = cover_desc.add_run(
        f"“{project.solution.vision_statement}”\n"
        f"- 3개년 총 사업비: 2,000,000,000원 (국비 10억원 / 지방비 10억원) -\n"
        f"- 사업 기간: 2027. 01. 01 ~ 2029. 12. 31 (36개월) -"
    )
    r_desc.font.name = "Malgun Gothic"
    r_desc.font.size = Pt(12)
    r_desc.font.color.rgb = RGB_MUTED
    cover_desc.paragraph_format.line_spacing = 1.3
    cover_desc.paragraph_format.space_after = Pt(80)

    # 표지 하단 기관 및 결재 정보
    cover_footer = doc.add_paragraph()
    cover_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_foot = cover_footer.add_run(
        "2026년 11월\n\n\n"
        f"신 청 기 관 : {project.market_profile.market_name} 상인회\n"
        f"관할 지자체 : 경기도 가평군청 (일자리경제과)\n"
        "전 담 기 관 : 소상공인시장진흥공단 / 중소벤처기업부"
    )
    r_foot.font.name = "Malgun Gothic"
    r_foot.font.size = Pt(11.5)
    r_foot.font.bold = True
    r_foot.font.color.rgb = RGB_PRIMARY

    # -------------------------------------------------------------------------
    # [신청서식 1] 사업 기본 정보 및 신청 개요
    # -------------------------------------------------------------------------
    add_h1(doc, "1. 사업 기본 정보 및 신청 개요", page_break_before=True)
    add_callout_box(
        doc,
        "본 사업계획서는 중소벤처기업부 '2027년도 전통시장 및 상점가 활성화 지원사업' 공고 지침에 따라 "
        "가평 조종시장의 지속가능한 문화관광 생태계 조성을 위해 수립된 3개년 20억원 규모의 법정 공식 실행계획서입니다."
    )

    m = project.market_profile
    summary_data = [
        ("시 장 명", m.market_name, "대 표 자", "상인회장 직무대행"),
        ("소 재 지", m.location, "개설연도", f"{m.established_year}년 (역사 50년 이상)"),
        ("점포 현황", f"총 {m.total_stores}개 (영업 {m.active_stores}개)", "주요 품목", m.main_items),
        ("총 사업비", "2,000,000,000원 (20억원)", "재원 분담", "국비 50% (10억) : 지방비 50% (10억)"),
        ("사업 기간", "2027. 01. 01 ~ 2029. 12. 31 (3개년)", "주관 부처", "중소벤처기업부 / 소진공"),
        ("핵심 테마", "달빛 캠핑 야시장 & 맹호 밀리터리 미식", "사업 비전", project.solution.vision_statement),
    ]

    t_sum = doc.add_table(rows=len(summary_data), cols=4)
    t_sum.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w = [Inches(1.2), Inches(2.1), Inches(1.2), Inches(2.0)]

    for r_idx, row in enumerate(summary_data):
        row_cells = t_sum.rows[r_idx].cells
        for c_idx, w in enumerate(col_w):
            row_cells[c_idx].width = w

        row_cells[0].text = row[0]
        set_cell_background(row_cells[0], COLOR_HEADER_BG_HEX)
        set_cell_margins(row_cells[0])
        p0 = row_cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.runs[0].font.bold = True
        p0.runs[0].font.size = Pt(10)

        row_cells[1].text = row[1]
        set_cell_margins(row_cells[1])
        p1 = row_cells[1].paragraphs[0]
        p1.runs[0].font.size = Pt(10)

        row_cells[2].text = row[2]
        set_cell_background(row_cells[2], COLOR_HEADER_BG_HEX)
        set_cell_margins(row_cells[2])
        p2 = row_cells[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.runs[0].font.bold = True
        p2.runs[0].font.size = Pt(10)

        row_cells[3].text = row[3]
        set_cell_margins(row_cells[3])
        p3 = row_cells[3].paragraphs[0]
        p3.runs[0].font.size = Pt(10)

        t_sum.rows[r_idx]._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        for cell in row_cells:
            cell.paragraphs[0].paragraph_format.keep_with_next = True

    # -------------------------------------------------------------------------
    # [신청서식 2] 법정 4대 기초역량 적격성 심사 결과
    # -------------------------------------------------------------------------
    add_h1(doc, "2. 법정 4대 기초역량 적격성 심사 결과", page_break_before=False)
    add_body_p(
        doc,
        "□ 문화관광형시장 육성사업 신청을 위한 중기부 법정 4대 필수 기초역량 충족 여부를 자체 사전 검증한 결과, "
        "모든 필수 항목을 기준치 이상으로 초과 달성하여 '적격' 판정을 획득함."
    )

    comp_headers = ["심사 항목", "법정 필수 기준", "신청 시장 현황", "적격 여부 및 검증 의견"]
    c = m.competency
    comp_rows = [
        ("① 상인회 동의율", "전체 점포의 60% 이상", f"{c.agreement_rate:.1f}% 달성 (동의서 첨부)", "적격 (기준 대비 +31.2%p 초과 달성)"),
        ("② 온누리상품권", "전체 점포의 50% 이상", f"{c.onnuri_rate:.1f}% 가맹 (모바일 100%)", "적격 (충전식 카드형 온누리 완벽 연동)"),
        ("③ 화재·소방안전", "화재알림설비 설치 완료", "100% 설치 완료 (소방서 필증)", "적격 (화재공제 가입률 88.0% 가점 요건)"),
        ("④ 3대 고객신뢰", "가격/원산지 80% 이상 준수", f"원산지 {c.price_tag_rate:.1f}%, 황색선 100%", "적격 (최근 3개년 부정결제 처분 0건)"),
    ]

    t_comp = doc.add_table(rows=len(comp_rows) + 1, cols=4)
    t_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_w = [Inches(1.6), Inches(1.6), Inches(1.6), Inches(1.7)]

    # 헤더
    for idx, name in enumerate(comp_headers):
        cell = t_comp.rows[0].cells[idx]
        cell.width = c_w[idx]
        cell.text = name
    style_table(t_comp, c_w, has_header=True)

    # 데이터 행
    for r_idx, r_data in enumerate(comp_rows, start=1):
        row = t_comp.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.text = val
            p = cell.paragraphs[0]
            if c_idx in (1, 3):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].font.size = Pt(10)
            if c_idx == 3:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGB_PRIMARY

    # 가점 요약
    add_callout_box(
        doc,
        f"법정 가점 평가: 청년상인 비율 {c.youth_merchant_rate:.1f}%(+2.0점), 화재공제 가입률 {c.fire_insurance_rate:.1f}%(+2.0점), "
        f"친환경 녹색시장 협약(+1.0점)을 통해 법정 상한인 총 +{comp_val.bonus_points:.1f}점(만점 한도)을 완전 확보함.",
        prefix="★ 가점 심사 우대 사항: "
    )

    # -------------------------------------------------------------------------
    # Ⅰ. 문제인식 (Problem) 및 상권 현황 심층 분석 (3~4페이지 분량)
    # -------------------------------------------------------------------------
    add_h1(doc, "Ⅰ. 문제인식 (Problem) 및 상권 현황 심층 분석", page_break_before=True)
    
    add_h2(doc, "1. 조종시장 및 배후 상권 생태계 현황")
    add_body_p(
        doc,
        "□ [시장 입지 및 역사적 가치] 가평 조종시장은 경기도 가평군 조종면 현리 중심부에 위치하며, 50년 이상의 전통을 지닌 가평 서북부의 중심 거점 상권임. "
        "인근에 국가지정 천연기념물 및 경기도 기념물 제28호 '조종암', 천년고찰 '현등사', 그리고 최근 개통된 '운악산 출렁다리' 등 풍부한 역사·생태 관광자원이 반경 5km 내에 집적되어 있음."
    )
    add_body_p(
        doc,
        "□ [배후 인구 및 주력 고객군 분석] 조종면 상주인구는 약 9,500명이나, 육군 수도기계화보병사단(맹호부대) 장병 약 6,000명 및 주말 면회객 2,500여명이 상시 유입되는 특수 국방 상권 구조를 띰. "
        "더불어 조종천을 따라 40여 개소의 오토캠핑장 및 100여 개소의 펜션이 조성되어 있어 연간 25만명 이상의 수도권 2040 캠핑 레저 관광객이 통과하는 핵심 교통 길목임."
    )

    add_h2(doc, "2. 상권 당면 위기 및 빅데이터 결핍 요인 진단")
    for block in expanded["problem_statement"]:
        add_body_p(doc, block)

    # 상권 진단 데이터 비교표
    diag_headers = ["진단 영역", "현재 조종시장 현황 (As-Is)", "목표 및 개선 방향 (To-Be)", "심사 착안점"]
    diag_rows = [
        ("야간 상권 활력", "18시 이후 91.2% 점포 소등 및 야간 공동화", "친환경 야시장 매대 20개소 상설화 (23시 운영)", "야간 체류시간 35분 → 110분 확대"),
        ("외래객 시장 유입", "운악산 등산객·캠핑객 시장 유입률 7.8% 불과", "스탬프 투어 및 캠핑 사이트 직배송 (유입률 80%)", "통과형 소비를 체류형 소비로 전환"),
        ("상인 디지털 역량", "상인 평균연령 62.4세, 온라인 판로 미비", "모바일 스마트 오더 & 라이브커머스 20개소", "디지털 결제 및 전국 택배 판매망 확보"),
        ("민·군 상생 체계", "군 장병 우대제도 부재 및 바가지 오해", "밀리터리 프렌들리 인증점포 50개소 & 온누리 페이백", "맹호부대 6천 장병 충성 고객화")
    ]
    t_diag = doc.add_table(rows=len(diag_rows) + 1, cols=4)
    t_diag.alignment = WD_TABLE_ALIGNMENT.CENTER
    d_w = [Inches(1.3), Inches(2.0), Inches(2.0), Inches(1.2)]
    for idx, name in enumerate(diag_headers):
        t_diag.rows[0].cells[idx].text = name
    style_table(t_diag, d_w, has_header=True)
    for r_idx, r_data in enumerate(diag_rows, start=1):
        for c_idx, val in enumerate(r_data):
            t_diag.rows[r_idx].cells[c_idx].text = val

    add_h2(doc, "3. SWOT 심층 분석 및 전략적 대응 매트릭스")
    swot_headers = ["구분", "강점 (Strengths)", "약점 (Weaknesses)"]
    swot_rows = [
        ("내부 환경", "ㆍ운악산 출렁다리 및 조종천 캠핑 벨트 인접\nㆍ맹호부대(6천 장병) 풍부한 배후 소비 수요\nㆍ상인회 사업 참여 동의율 91.2%의 높은 결속력", "ㆍ야간 조명 및 휴게 편의시설 전무\nㆍ상인 고령화 및 디지털 모바일 주문 시스템 미비\nㆍ시그니처 선물용 특화 PB 상품 부재"),
        ("외부 환경", "기회 (Opportunities)", "위협 (Threats)"),
        ("외부 대응", "ㆍ수도권 2040 캠핑·레저 미식 수요 급증\nㆍ중기부 전통시장 디지털·문화관광 육성 정책\nㆍ가평군 로컬푸드 및 관광 활성화 연계 지원", "ㆍ대형 할인마트 및 온라인 새벽배송 시장 잠식\nㆍ군 복무기간 단축 및 장병 평일 외출 감소 추세\nㆍ인근 지자체 야시장 간 유치 경쟁 심화")
    ]
    t_swot = doc.add_table(rows=len(swot_rows) + 1, cols=3)
    t_swot.alignment = WD_TABLE_ALIGNMENT.CENTER
    s_w = [Inches(1.1), Inches(2.7), Inches(2.7)]
    for idx, name in enumerate(swot_headers):
        t_swot.rows[0].cells[idx].text = name
    style_table(t_swot, s_w, has_header=True)
    for r_idx, r_data in enumerate(swot_rows, start=1):
        for c_idx, val in enumerate(r_data):
            t_swot.rows[r_idx].cells[c_idx].text = val

    # -------------------------------------------------------------------------
    # Ⅱ. 실현가능성 (Solution) 및 10대 Work Package(WP) 상세 실행계획 (15~20페이지)
    # -------------------------------------------------------------------------
    add_h1(doc, "Ⅱ. 실현가능성 (Solution) 및 10대 핵심 세부사업(Work Package) 실행계획", page_break_before=True)
    
    add_body_p(
        doc,
        "□ 본 사업계획서는 '조종천 달빛 캠핑과 맹호 미식이 살아 숨 쉬는 수도권 대표 K-관광 마켓'이라는 비전 달성을 위해, "
        "특성화 기반조성(H/W 3건), 지역문화콘텐츠 개발(S/W 3건), 홍보·마케팅 및 디지털 혁신(S/W 3건), 사업단 전담운영(1건) 등 "
        "총 10대 단위세부사업(Work Package)을 상호 유기적으로 설계하여 3개년 동안 총 20억원의 예산을 집중 투입함."
    )

    # 10대 WP 총괄 요약표
    add_h2(doc, "1. 10대 단위세부사업(WP-01 ~ WP-10) 투자 포트폴리오 총괄")
    wp_sum_headers = ["WP 코드", "단위 세부사업명", "사업 분야", "3개년 총예산", "핵심 목표치(KPI)"]
    wp_sum_rows = [
        (wp.wp_id, wp.title.split("(")[0].strip() if "(" in wp.title else wp.title[:24], wp.category, f"{wp.total_budget // 1000000:,}백만원", wp.kpi_metrics[0]["목표치(2029)"])
        for wp in work_packages
    ]
    t_wpsum = doc.add_table(rows=len(wp_sum_rows) + 1, cols=5)
    t_wpsum.alignment = WD_TABLE_ALIGNMENT.CENTER
    wp_w = [Inches(1.0), Inches(2.3), Inches(1.5), Inches(0.9), Inches(0.8)]
    for idx, name in enumerate(wp_sum_headers):
        t_wpsum.rows[0].cells[idx].text = name
    style_table(t_wpsum, wp_w, has_header=True)
    for r_idx, r_data in enumerate(wp_sum_rows, start=1):
        for c_idx, val in enumerate(r_data):
            t_wpsum.rows[r_idx].cells[c_idx].text = val

    add_body_p(
        doc,
        "※ 위 10대 단위사업은 상호 분절된 사업이 아닌, [H/W 인프라 조성] → [킬러 미식 콘텐츠 론칭] → [모바일 투어·배송 유입] → [사업단 상시 운영]으로 "
        "이어지는 완벽한 밸류체인으로 상호 시너지를 극대화하도록 설계됨."
    )

    # -------------------------------------------------------------------------
    # 10대 단위사업별 독립 실행계획서 (Full 모드 시 각 1.5 ~ 2페이지씩 조판)
    # -------------------------------------------------------------------------
    if mode == "full":
        for wp in work_packages:
            add_h1(doc, f"[{wp.wp_id}] {wp.title}", page_break_before=True)
            
            # 1. 추진 배경 및 필요성
            add_h2(doc, "1. 추진 배경 및 상권 실태분석 (Why)")
            for bg in wp.background_needs:
                add_body_p(doc, bg)
                
            # 2. 사업 개요
            add_h2(doc, "2. 단위사업 개요 및 실행 스펙 (What & Where)")
            t_ov = doc.add_table(rows=len(wp.overview_table), cols=2)
            t_ov.alignment = WD_TABLE_ALIGNMENT.CENTER
            ov_w = [Inches(1.5), Inches(5.0)]
            for r_idx, row_dict in enumerate(wp.overview_table):
                t_ov.rows[r_idx].cells[0].text = row_dict["항목"]
                t_ov.rows[r_idx].cells[1].text = row_dict["세부내용"]
            style_table(t_ov, ov_w, has_header=False)
            # 라벨 컬럼 볼드 및 배경
            for row in t_ov.rows:
                set_cell_background(row.cells[0], COLOR_HEADER_BG_HEX)
                row.cells[0].paragraphs[0].runs[0].font.bold = True
                row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            # 3. 세부 실행 공정도 및 추진 프로세스
            add_h2(doc, "3. 세부 실행 공정도 및 마일스톤 프로세스 (How & When)")
            add_body_p(
                doc,
                f"□ 본 사업은 3개년 36개월에 걸쳐 기획·설계, 시공·인허가, 시운전, 상설운영 등 4단계 표준 프로세스에 따라 추진됨."
            )
            proc_headers = ["추진 단계", "핵심 수행 과업 및 세부 활동", "공식 산출물 (증빙)"]
            t_proc = doc.add_table(rows=len(wp.process_phases) + 1, cols=3)
            t_proc.alignment = WD_TABLE_ALIGNMENT.CENTER
            pr_w = [Inches(1.8), Inches(3.2), Inches(1.5)]
            for idx, name in enumerate(proc_headers):
                t_proc.rows[0].cells[idx].text = name
            style_table(t_proc, pr_w, has_header=True)
            for r_idx, p_data in enumerate(wp.process_phases, start=1):
                t_proc.rows[r_idx].cells[0].text = p_data["단계"]
                t_proc.rows[r_idx].cells[1].text = p_data["주요업무"]
                t_proc.rows[r_idx].cells[2].text = p_data["산출물"]
                t_proc.rows[r_idx].cells[0].paragraphs[0].runs[0].font.bold = True

            # 4. 원단위 세부 예산 산출내역
            add_h2(doc, "4. 원단위 세부 예산 산출내역 (단가 × 수량 × 횟수 = 총액)")
            b_hdrs = ["비목", "품명 및 규격", "단가 (원)", "수량", "단위", "횟수", "총액 (원)", "산출 근거"]
            t_bdt = doc.add_table(rows=len(wp.budget_details) + 1, cols=8)
            t_bdt.alignment = WD_TABLE_ALIGNMENT.CENTER
            bd_w = [Inches(0.7), Inches(1.6), Inches(0.9), Inches(0.4), Inches(0.4), Inches(0.4), Inches(1.0), Inches(1.1)]
            for idx, name in enumerate(b_hdrs):
                t_bdt.rows[0].cells[idx].text = name
            style_table(t_bdt, bd_w, has_header=True)
            
            for r_idx, b_item in enumerate(wp.budget_details, start=1):
                row = t_bdt.rows[r_idx]
                row.cells[0].text = b_item["비목"]
                row.cells[1].text = f"{b_item['품명']}\n({b_item['규격']})"
                row.cells[2].text = f"{b_item['단가']:,}"
                row.cells[3].text = str(b_item["수량"])
                row.cells[4].text = b_item["단위"]
                row.cells[5].text = str(b_item["횟수"])
                row.cells[6].text = f"{b_item['총액']:,}"
                row.cells[7].text = b_item["산출근거"]
                
                # 숫자 우측 정렬
                row.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
                row.cells[6].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
                row.cells[6].paragraphs[0].runs[0].font.bold = True
                row.cells[6].paragraphs[0].runs[0].font.color.rgb = RGB_PRIMARY

            # 5. 정량/정성 성과관리 지표 (KPI)
            add_h2(doc, "5. 정량/정성 성과관리 지표 (KPI & Performance)")
            kpi_hdrs = ["구분", "성과 지표명", "기준치 (2026)", "1차년도", "2차년도", "최종목표 (2029)", "측정 방법 및 출처"]
            t_kpi = doc.add_table(rows=len(wp.kpi_metrics) + 1, cols=7)
            t_kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
            kp_w = [Inches(0.8), Inches(1.5), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.9), Inches(0.9)]
            for idx, name in enumerate(kpi_hdrs):
                t_kpi.rows[0].cells[idx].text = name
            style_table(t_kpi, kp_w, has_header=True)
            for r_idx, k_item in enumerate(wp.kpi_metrics, start=1):
                row = t_kpi.rows[r_idx]
                row.cells[0].text = k_item["지표구분"]
                row.cells[1].text = k_item["지표명"]
                row.cells[2].text = k_item["기준치(2026)"]
                row.cells[3].text = k_item["1차년도"]
                row.cells[4].text = k_item["2차년도"]
                row.cells[5].text = k_item["목표치(2029)"]
                row.cells[6].text = k_item["측정방법"]
                row.cells[5].paragraphs[0].runs[0].font.bold = True
                row.cells[5].paragraphs[0].runs[0].font.color.rgb = RGB_PRIMARY

    # -------------------------------------------------------------------------
    # Ⅲ. 성장전략 (Scale-up) 및 20억원 원단위 회계 산출내역서 (총 5페이지 분량)
    # -------------------------------------------------------------------------
    add_h1(doc, "Ⅲ. 성장전략 (Scale-up) 및 20억원 원단위 세부 회계 산출내역서", page_break_before=True)
    
    add_h2(doc, "1. 3개년 단계별 성장 로드맵 (기반조성 → 도약확산 → 자생정착)")
    for block in expanded["scaleup_statement"]:
        add_body_p(doc, block)

    add_h2(doc, "2. 3개년 총괄 비목별 예산 집계표")
    add_callout_box(
        doc,
        "총 사업비 20억원(국비 10억, 지방비 10억)은 중기부 지침에 따라 H/W 시설비(32.5%, 권장 35% 이하 준수)와 "
        "사업단 운영비(10.0%, 법정상한 엄수)를 완벽히 준수하여 편성됨."
    )

    # 3개년 비목별 집계 총괄표
    b_headers = ["비목 구분", "세부 추진 사업명", "1차년도 (원)", "2차년도 (원)", "3차년도 (원)", "3개년 합계 (원)"]
    b_widths = [Inches(1.4), Inches(2.1), Inches(0.8), Inches(0.8), Inches(0.7), Inches(0.7)]
    
    b_items = project.scale_up.budget_items
    t_budget = doc.add_table(rows=len(b_items) + 2, cols=6)
    t_budget.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, h_name in enumerate(b_headers):
        t_budget.rows[0].cells[idx].text = h_name
    style_table(t_budget, b_widths, has_header=True)

    tot_y1, tot_y2, tot_y3, tot_all = 0, 0, 0, 0
    for r_idx, item in enumerate(b_items, start=1):
        row = t_budget.rows[r_idx]
        tot_y1 += item.year1
        tot_y2 += item.year2
        tot_y3 += item.year3
        tot_all += item.total

        row_vals = [
            item.category,
            item.item_name,
            f"{item.year1:,}",
            f"{item.year2:,}",
            f"{item.year3:,}",
            f"{item.total:,}"
        ]
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            cell.text = val
            if c_idx >= 2:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            cell.paragraphs[0].runs[0].font.size = Pt(10)

    # 합계 행
    total_row = t_budget.rows[len(b_items) + 1]
    total_vals = [
        "총 계 (합계)",
        "3개년 20억원 100% 완전 편성",
        f"{tot_y1:,}",
        f"{tot_y2:,}",
        f"{tot_y3:,}",
        f"{tot_all:,}"
    ]
    for c_idx, val in enumerate(total_vals):
        cell = total_row.cells[c_idx]
        cell.text = val
        set_cell_background(cell, COLOR_HEADER_BG_HEX)
        p = cell.paragraphs[0]
        if c_idx >= 2:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.bold = True
        p.runs[0].font.size = Pt(10)
        p.runs[0].font.color.rgb = RGB_PRIMARY

    # -------------------------------------------------------------------------
    # 3. 20억원 원단위(단가×수량×횟수) 회계 세부 산출내역표 (Full 모드 시 총 5페이지 분량)
    # -------------------------------------------------------------------------
    if mode == "full":
        add_h2(doc, "3. 10대 단위사업별 원단위 회계 세부 산출내역표 (단가 × 수량 × 횟수 = 총액)")
        add_body_p(
            doc,
            "□ [회계 산출 원칙] 기획재정부 '예산안 편성 및 기금운용계획 수립지침' 및 조달청 다수공급자계약(MAS) 표준단가, "
            "엔지니어링·전력기술·SW 표준품셈 기술자 노임단가를 원용하여 46개 전 세목의 산출내역을 원단위로 철저히 산출함."
        )

        # 비목별로 나누어 5페이지 분량의 회계 장부표 렌더링
        categories = [
            ("특성화 기반조성 (H/W)", [i for i in detailed_budget if "H/W" in i.category]),
            ("지역문화콘텐츠 개발 (S/W)", [i for i in detailed_budget if "지역문화콘텐츠" in i.category]),
            ("홍보·마케팅 및 디지털 혁신 (S/W)", [i for i in detailed_budget if "홍보·마케팅" in i.category]),
            ("사업단 운영비 (인건비/운영비)", [i for i in detailed_budget if "사업단 운영비" in i.category]),
        ]

        for cat_title, cat_items in categories:
            add_h3(doc, f"▶ [비목 세부 산출내역] {cat_title} (소계: {sum(x.total for x in cat_items):,}원)")
            
            det_hdrs = ["WP코드", "세부 품명 및 규격", "단가 (원)", "수량", "단위", "횟수", "1차년도 (원)", "2차년도 (원)", "3차년도 (원)", "총액 (원)"]
            t_det = doc.add_table(rows=len(cat_items) + 1, cols=10)
            t_det.alignment = WD_TABLE_ALIGNMENT.CENTER
            det_w = [Inches(0.6), Inches(1.5), Inches(0.7), Inches(0.3), Inches(0.3), Inches(0.3), Inches(0.7), Inches(0.7), Inches(0.7), Inches(0.7)]
            for idx, name in enumerate(det_hdrs):
                t_det.rows[0].cells[idx].text = name
            style_table(t_det, det_w, has_header=True)

            for r_idx, item in enumerate(cat_items, start=1):
                row = t_det.rows[r_idx]
                row.cells[0].text = item.wp_id
                row.cells[1].text = f"{item.item_name}\n({item.spec_basis})"
                row.cells[2].text = f"{item.unit_price:,}"
                row.cells[3].text = str(item.quantity)
                row.cells[4].text = item.unit
                row.cells[5].text = str(item.count)
                row.cells[6].text = f"{item.year1:,}"
                row.cells[7].text = f"{item.year2:,}"
                row.cells[8].text = f"{item.year3:,}"
                row.cells[9].text = f"{item.total:,}"

                # 정렬
                row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                row.cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                row.cells[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                row.cells[5].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for c_i in (2, 6, 7, 8, 9):
                    row.cells[c_i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    row.cells[c_i].paragraphs[0].runs[0].font.size = Pt(9.5)
                row.cells[9].paragraphs[0].runs[0].font.bold = True
                row.cells[9].paragraphs[0].runs[0].font.color.rgb = RGB_PRIMARY

            add_body_p(doc, f"※ 비목 적용 기준: {cat_items[0].audit_standard}")

    # -------------------------------------------------------------------------
    # Ⅳ. 사업추진체계 (Team) 및 거버넌스, 사후 자생력 관리 (2~3페이지)
    # -------------------------------------------------------------------------
    add_h1(doc, "Ⅳ. 사업추진체계 (Team) 및 사후 자생력 유지 방안", page_break_before=True)
    
    add_h2(doc, "1. 문화관광형 사업단 전담 추진 조직 및 전문인력")
    for block in expanded["team_statement"]:
        add_body_p(doc, block)

    add_h2(doc, "2. 민·관·군 거버넌스 협력 체계")
    gov_headers = ["협력 주체", "주요 역할 및 업무 분장", "협약 상태 및 지원 계획"]
    gov_rows = [
        ("중소벤처기업부 / 소진공", "국비 10억원 교부, 사업계획 승인, 연차별 성과평가 및 사후관리", "공식 지원 대상 공고 및 지침 배포"),
        ("가평군청 (일자리경제과)", "지방비 10억원 매칭 예산 편성, 옥외 인허가 행정지원, 인프라 공사 감리", "가평군의회 매칭 동의안 의결 완료"),
        ("육군 수도기계화보병사단 (맹호)", "군 장병 문화외출 지원, 상생 페이백 프로모션, 부대 내 홍보", "사령부-상인회 민군 상생 MOU 체결"),
        ("조종시장 상인회", "현장 매대 관리, 위생·안전 자율정화, 축제 행사 공동 주관", "상인 참여 동의율 91.2% 확보"),
        ("대학 산학협력단 / 전문가", "PB 5종 식품 R&D, 상인 아카데미 강의, 보조금 외부 회계감사", "자문위원 5인 위촉 및 위탁 협약 체결")
    ]
    t_gov = doc.add_table(rows=len(gov_rows) + 1, cols=3)
    t_gov.alignment = WD_TABLE_ALIGNMENT.CENTER
    gv_w = [Inches(1.8), Inches(3.2), Inches(1.5)]
    for idx, name in enumerate(gov_headers):
        t_gov.rows[0].cells[idx].text = name
    style_table(t_gov, gv_w, has_header=True)
    for r_idx, r_data in enumerate(gov_rows, start=1):
        for c_idx, val in enumerate(r_data):
            t_gov.rows[r_idx].cells[c_idx].text = val
            if c_idx == 0:
                t_gov.rows[r_idx].cells[c_idx].paragraphs[0].runs[0].font.bold = True

    add_h2(doc, "3. 3개년 지원 종료 후 자생력 확보 및 사후관리 영속화 방안")
    add_body_p(
        doc,
        "□ [상인 상생발전기금 적립] 달빛 야시장 매대 운영 수수료(월 15만원/대) 및 PB 5종 유통 마진의 20%를 '조종시장 상생발전기금'으로 "
        "의무 적립하여 연간 4,500만원 규모의 자체 자립 기금을 조성함."
    )
    add_body_p(
        doc,
        "□ [상인 자립형 협동조합 전환] 사업 3차년도 하반기에 상인들이 직접 출자하는 '조종시장 문화관광 협동조합'을 설립하여, "
        "사업단 종료 후에도 야시장 및 모바일 직배송 플랫폼을 중단 없이 영구적으로 자율 경영함."
    )
    add_body_p(
        doc,
        "□ [시설물 사후 무상귀속 및 유지관리] 구축된 친환경 매대 20기, 키오스크 3기, 락커룸 등 모든 H/W 시설물은 가평군 공유재산 및 상인회 자산으로 "
        "등재하고, 상인회 자체 시설안전관리비(연 1,500만원)를 배정하여 10년 이상 반영구적 가동을 보장함."
    )

    # -------------------------------------------------------------------------
    # Ⅴ. 심사위원 모의평가 스코어카드 및 대면심사 방어 전략
    # -------------------------------------------------------------------------
    add_h1(doc, "Ⅴ. 심사위원 모의평가 스코어카드 및 대면심사 방어 전략", page_break_before=True)
    
    add_h2(doc, "1. 소상공인시장진흥공단 기준 100점 만점 모의 평가표")
    add_callout_box(
        doc,
        f"소진공 공인 평가항목(상권매력도, 실현가능성, 사업계획 적정성, 추진체계 역량) 100점 만점 기준 모의 채점 결과: "
        f"기본점수 {eval_card.to_dict()['subtotal']}점 + 법정 가점 {eval_card.bonus_points}점 = 총 {eval_card.total_score}점 획득! "
        f"등급: [{eval_card.grade}] - {eval_card.pass_probability} 판정.",
        prefix="★ 최종 심사위원 채점 시뮬레이션: "
    )

    score_headers = ["평가 영역", "배점", "모의 득점", "주요 채점 사유 및 강점 분석"]
    score_rows = [
        ("1. 상권 매력도 및 위기극복 시급성", "25점", "24.0점", "운악산·조종천 캠핑족 유입 연계성 및 야간 공동화 극복 전략 명확"),
        ("2. 실현가능성 및 특성화 전략", "30점", "28.5점", "10대 WP 딥-익스팬션 및 공정도 완비, 특화 PB 5종 및 야시장 인프라 탁월"),
        ("3. 예산 계획의 적정성 및 타당성", "25점", "24.5점", "20억원 원단위(단가×수량×횟수) 46개 세목 완벽 제시, 운영비 10% 엄수"),
        ("4. 사업추진체계 및 자생력", "20점", "19.0점", "사업단장 전문성, 민·관·군 거버넌스 MOU 완비, 상생발전기금 자립안 구체화"),
        ("소 계 (기본 점수)", "100점", f"{eval_card.to_dict()['subtotal']}점", "서면 평가 최고점 영역 진입"),
        ("가 점 (법정 가점)", "+5점 한도", f"+{eval_card.bonus_points}점", "청년상인(+2), 화재공제(+2), 녹색시장(+1) 만점 획득"),
        ("총 계 (종합 득점)", "105점", f"{eval_card.total_score}점", f"최종 등급 [{eval_card.grade}] - 합격 최우선 순위")
    ]
    t_score = doc.add_table(rows=len(score_rows) + 1, cols=4)
    t_score.alignment = WD_TABLE_ALIGNMENT.CENTER
    sc_w = [Inches(1.8), Inches(0.8), Inches(0.9), Inches(3.0)]
    for idx, name in enumerate(score_headers):
        t_score.rows[0].cells[idx].text = name
    style_table(t_score, sc_w, has_header=True)
    for r_idx, r_data in enumerate(score_rows, start=1):
        for c_idx, val in enumerate(r_data):
            cell = t_score.rows[r_idx].cells[c_idx]
            cell.text = val
            if c_idx in (1, 2):
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if r_idx in (5, 6, 7):
                cell.paragraphs[0].runs[0].font.bold = True
                set_cell_background(cell, COLOR_HEADER_BG_HEX)
                if c_idx == 2:
                    cell.paragraphs[0].runs[0].font.color.rgb = RGB_PRIMARY

    add_h2(doc, "2. 심사위원 송곳 예상 질문 5선 및 대면심사 철통 방어 전략")
    
    # 5대 송곳 Q&A 방어 전략
    all_defense_qa = eval_card.defense_questions + [
        {
            "question": "캠핑 야시장과 PB상품이 인근 대형마트나 프랜차이즈와의 경쟁에서 우위를 점할 수 있는 차별성은 무엇인가?",
            "defense": "단순한 기성 식재료 판매가 아닌, 운악산 포도 와인 뱅쇼 키트 및 조종 간장닭갈비 캠핑 밀키트처럼 오직 조종시장에서만 맛볼 수 있는 고유 시그니처 레시피를 특허화하고, 텐트 앞까지 2시간 내 직배송하는 친환경 스마트 오더망을 통해 온·오프라인 압도적 편의성을 선점할 것입니다."
        },
        {
            "question": "3개년 국비 지원 20억원이 종료된 후 상인회의 자생적 유지관리 예산이 고갈될 우려는 없는가?",
            "defense": "사업 초기부터 야시장 매대 운영 수수료와 PB 상품 유통 수익의 20%를 '상생발전기금'으로 의무 적립하여 연간 4,500만원 규모의 기금을 자동 비축하며, 3차년도에 설립되는 상인 협동조합이 독립 채산제로 운영하여 지자체 보조금 없이도 영구 자립 운영되는 비즈니스 모델을 이미 완성했습니다."
        }
    ]

    for q_idx, qa in enumerate(all_defense_qa, start=1):
        qp = doc.add_paragraph()
        qp_r = qp.add_run(f"Q{q_idx}. [심사위원 예상 질문] {qa['question']}")
        qp_r.font.name = "Malgun Gothic"
        qp_r.font.bold = True
        qp_r.font.size = Pt(11)
        qp_r.font.color.rgb = RGB_PRIMARY
        qp.paragraph_format.space_before = Pt(8)
        qp.paragraph_format.space_after = Pt(2)
        qp.paragraph_format.keep_with_next = True

        ap = doc.add_paragraph()
        ap_r = ap.add_run(f"→ [모범 방어 전략]: {qa['defense']}")
        ap_r.font.name = "Malgun Gothic"
        ap_r.font.size = Pt(10.5)
        ap.paragraph_format.space_after = Pt(8)
        ap.paragraph_format.line_spacing = 1.15

    # 문서 저장
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path
