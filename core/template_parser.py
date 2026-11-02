import os
from typing import List, Dict, Any
import docx

class FieldSlot:
    def __init__(self, slot_id: str, label: str, field_type: str, hint: str = "", table_idx: int = -1, row_idx: int = -1, col_idx: int = -1, p_idx: int = -1):
        self.slot_id = slot_id
        self.label = label
        self.field_type = field_type  # text, textarea
        self.hint = hint
        self.table_idx = table_idx
        self.row_idx = row_idx
        self.col_idx = col_idx
        self.p_idx = p_idx

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "label": self.label,
            "field_type": self.field_type,
            "hint": self.hint,
            "table_idx": self.table_idx,
            "row_idx": self.row_idx,
            "col_idx": self.col_idx,
            "p_idx": self.p_idx,
        }

class DocumentSchema:
    def __init__(self, doc_title: str):
        self.doc_title = doc_title
        self.slots: List[FieldSlot] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_title": self.doc_title,
            "slots": [s.to_dict() for s in self.slots]
        }

def parse_docx_template(docx_path: str) -> DocumentSchema:
    doc = docx.Document(docx_path)
    title = os.path.basename(docx_path).replace(".docx", "")
    schema = DocumentSchema(doc_title=title)

    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            cells = row.cells
            num_cells = len(cells)
            if num_cells >= 2:
                for c_idx in range(0, num_cells - 1, 2):
                    label_text = cells[c_idx].text.strip()
                    val_text = cells[c_idx + 1].text.strip()
                    if 2 <= len(label_text) <= 30:
                        slot_id = f"SLOT_T{t_idx}_R{r_idx}_C{c_idx+1}"
                        field_type = "textarea" if ("내용" in label_text or "사유" in label_text or "계획" in label_text) else "text"
                        hint = val_text if val_text else f"{label_text}을(를) 입력하세요."
                        slot = FieldSlot(slot_id, label_text, field_type, hint, t_idx, r_idx, c_idx + 1)
                        schema.slots.append(slot)

    for p_idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if text.startswith("[") and ("작성" in text or "기재" in text or "예시" in text):
            slot_id = f"SLOT_P{p_idx}"
            slot = FieldSlot(slot_id, f"서술 항목 (문단 {p_idx+1})", "textarea", text, p_idx=p_idx)
            schema.slots.append(slot)

    return schema
