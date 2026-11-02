import os
import shutil
from typing import Dict, Any
import docx
from docx.shared import Pt
from core.template_parser import DocumentSchema

def fill_template_slots(template_docx_path: str, schema: DocumentSchema, slot_values: Dict[str, str], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
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
                    cell.text = val
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.name = "Malgun Gothic"
                            run.font.size = Pt(10)
        elif 0 <= slot.p_idx < len(doc.paragraphs):
            p = doc.paragraphs[slot.p_idx]
            p.text = val
            for run in p.runs:
                run.font.name = "Malgun Gothic"
                run.font.size = Pt(11)

    doc.save(output_path)
    return output_path
