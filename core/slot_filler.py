import copy
import os
import shutil
from typing import Dict, List

import docx
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

from core.template_parser import DocumentSchema


def _find_template_rpr(paragraphs: List[Paragraph]):
    """칸 안에서 서식 견본이 될 rPr 을 찾는다: 첫 run 의 rPr -> 문단 부호(pPr/rPr)."""
    for p in paragraphs:
        for r in p.runs:
            rpr = r._r.find(qn("w:rPr"))
            if rpr is not None:
                return rpr
    for p in paragraphs:
        ppr = p._p.find(qn("w:pPr"))
        if ppr is not None:
            rpr = ppr.find(qn("w:rPr"))
            if rpr is not None:
                return rpr
    return None


def _write_keep_format(paragraphs: List[Paragraph], text: str, default_pt: float) -> None:
    """기존 run 서식(글꼴·크기·굵기·색 등 rPr 전체)과 문단 서식(pPr)을 복사해 텍스트만 교체한다."""
    first = paragraphs[0]
    tmpl = _find_template_rpr(paragraphs)
    tmpl = copy.deepcopy(tmpl) if tmpl is not None else None

    # 첫 문단의 run 제거, 나머지 문단 제거 (첫 문단 pPr 은 유지)
    for p in paragraphs[1:]:
        p._p.getparent().remove(p._p)
    for child in list(first._p):
        if child.tag != qn("w:pPr"):
            first._p.remove(child)

    lines = text.split("\n")
    prev = first
    for i, line in enumerate(lines):
        if i == 0:
            para = first
        else:
            new_p = copy.deepcopy(first._p)
            for child in list(new_p):
                if child.tag != qn("w:pPr"):
                    new_p.remove(child)
            prev._p.addnext(new_p)
            para = Paragraph(new_p, first._parent)
        run = para.add_run(line)
        old = run._r.find(qn("w:rPr"))
        if old is not None:
            run._r.remove(old)
        if tmpl is not None:
            run._r.insert(0, copy.deepcopy(tmpl))
        else:  # 견본이 전혀 없는 빈 칸일 때만 기본 서식
            run.font.name = "Malgun Gothic"
            run.font.size = Pt(default_pt)
        prev = para


def fill_template_slots(template_docx_path: str, schema: DocumentSchema, slot_values: Dict[str, str], output_path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    shutil.copy2(template_docx_path, output_path)
    doc = docx.Document(output_path)

    for slot in schema.slots:
        val = slot_values.get(slot.slot_id)
        if not val:
            continue

        if 0 <= slot.table_idx < len(doc.tables):
            table = doc.tables[slot.table_idx]
            if slot.row_idx < len(table.rows):
                row = table.rows[slot.row_idx]
                if slot.col_idx < len(row.cells):
                    cell = row.cells[slot.col_idx]
                    _write_keep_format(cell.paragraphs, val, 10)
        elif 0 <= slot.p_idx < len(doc.paragraphs):
            _write_keep_format([doc.paragraphs[slot.p_idx]], val, 11)

    doc.save(output_path)
    return output_path
