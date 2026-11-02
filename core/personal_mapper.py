"""개인 정책자금 입력 데이터를 기관 공식 서식의 슬롯(FieldSlot)에 매핑한다.

슬롯 라벨(표의 왼쪽 칸 문구)을 키워드로 분류한다. 먼저 일치한 규칙이 우선하므로
구체적인 키워드를 앞에 둔다. 매핑되지 않은 슬롯은 빈 값으로 남기고 UI에서 직접 입력하게 한다.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from core.personal_loan import summarize_by_year


def _won(v: int) -> str:
    return f"{int(v):,}원"


def build_value_pool(d: Dict[str, Any]) -> Dict[str, str]:
    """app.py 의 개인 모드 데이터 딕셔너리 -> 서식에 넣을 문자열 값."""
    sched = d["schedule"]
    lines = [f"{r['month']}회차 원금 {r['principal']:,} / 이자 {r['interest']:,} / 납부 {r['payment']:,} / 잔액 {r['balance']:,}"
             for r in sched[:12]]
    years = summarize_by_year(sched)
    repay = (f"원리금균등상환, 연 {d['rate']:.2f}%, {d['term_months']}개월(거치 {d['grace_months']}개월)\n"
             + "\n".join(lines))
    year_txt = "\n".join(f"{y['year']}년차 상환액 {y['payment']:,}원 (잔액 {y['balance']:,}원)" for y in years)
    rev_txt = "\n".join(f"{i+1}차년도 {v:,}원" for i, v in enumerate(d["revenue_forecast"]))
    return {
        "business_name": d["business_name"], "biz_no": d["biz_no"], "owner_name": d["owner_name"],
        "industry": d["industry"], "start_year": f"{d['start_year']}년",
        "annual_revenue": _won(d["annual_revenue"]), "amount": _won(d["amount"]),
        "facility_amount": _won(d["facility_amount"]), "working_amount": _won(d["working_amount"]),
        "facility_use": d["facility_use"], "working_use": d["working_use"],
        "difficulty": d["difficulty"], "signature": d["signature"], "target": d["target"],
        "marketing": d["marketing"], "revenue_forecast": rev_txt,
        "repayment": repay, "repayment_year": year_txt,
        "career": (d["owner_career_text"] or f"관련 업종 경력 {d['career_years']}년"),
        "youth": "해당" if d["is_youth"] else "비해당",
        "female": "해당" if d["is_female"] else "비해당",
    }


# (키워드들, 값 키) - 앞쪽 규칙 우선
RULES: List[Tuple[Tuple[str, ...], str]] = [
    (("사업자등록번호", "사업자번호", "등록번호"), "biz_no"),
    (("시설자금",), "facility_amount"),
    (("운전자금",), "working_amount"),
    (("신청금액", "신청액", "자금규모", "대출금액", "융자금액", "희망금액"), "amount"),
    (("대표자", "성명", "신청인"), "owner_name"),
    (("상호", "업체명", "사업장명", "기업명", "업소명", "점포명"), "business_name"),
    (("업종", "업태"), "industry"),
    (("창업", "개업", "설립", "사업개시"), "start_year"),
    (("연간매출", "연매출", "매출액", "전년도매출", "최근매출"), "annual_revenue"),
    (("경영애로", "자금필요", "필요성", "신청사유", "자금사용사유", "신청사유"), "difficulty"),
    (("시설용도", "시설내역"), "facility_use"),
    (("운전용도", "운전내역"), "working_use"),
    (("상환계획", "상환방법", "상환"), "repayment"),
    (("추정매출", "매출계획", "매출전망"), "revenue_forecast"),
    (("시그니처", "대표상품", "대표메뉴", "주력상품", "주요상품", "경쟁력"), "signature"),
    (("타깃", "타겟", "고객층", "주요고객"), "target"),
    (("마케팅", "홍보", "판로"), "marketing"),
    (("경력", "역량", "자격"), "career"),
    (("청년",), "youth"),
    (("여성",), "female"),
]


def classify(text: str) -> Optional[str]:
    t = re.sub(r"\s+", "", text or "")
    for kws, key in RULES:
        if any(k in t for k in kws):
            return key
    return None


def map_slots(schema, pool: Dict[str, str]) -> Tuple[Dict[str, str], List[Any]]:
    """returns (slot_id -> value, 매핑 실패 슬롯 리스트). 문단 슬롯은 힌트 문구로 분류."""
    values: Dict[str, str] = {}
    unmapped = []
    for slot in schema.slots:
        basis = slot.hint if slot.p_idx >= 0 else slot.label
        key = classify(basis)
        if key and pool.get(key):
            values[slot.slot_id] = pool[key]
        else:
            unmapped.append(slot)
    return values, unmapped
