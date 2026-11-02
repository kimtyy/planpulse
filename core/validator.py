"""
PlanPulse Statutory Competency Validator
법정 4대 기초역량 적격성 검증 로직 및 가점 산출 엔진
공고: 전통시장 및 상점가 활성화 지원사업(문화관광형) 표준
"""

from typing import Dict, List, Any
from planpulse.core.models import BasicCompetency


class ValidationResult:
    def __init__(self):
        self.is_eligible: bool = True
        self.reasons: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        self.bonus_points: float = 0.0
        self.bonus_breakdown: List[Dict[str, Any]] = []
        self.metrics_summary: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_eligible": self.is_eligible,
            "status": "적격 (PASS)" if self.is_eligible else "부적격 (FAIL)",
            "reasons": self.reasons,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "bonus_points": round(self.bonus_points, 1),
            "bonus_breakdown": self.bonus_breakdown,
            "metrics_summary": self.metrics_summary,
        }


def validate_statutory_competency(comp: BasicCompetency) -> ValidationResult:
    """
    중기부 및 소상공인시장진흥공단 문화관광형시장 법정 4대 기초역량 검증
    1. 상인회 가입율/사업참여 동의율: 60% 이상 (미달 시 탈락)
    2. 온누리상품권 가맹률: 50% 이상 (미달 시 탈락)
    3. 화재알림설비/소방안전: 필수 설치/적격 (미설치 시 탈락)
    4. 3대 고객신뢰(가격/원산지 80% 이상, 고객선 지키기, 결제거절 제재 이력 없음)
    + 가점 산정 (최대 5.0점 한도)
    """
    res = ValidationResult()

    # 1. 상인회 동의율 (기준: 60%)
    res.metrics_summary["상인회_동의율"] = f"{comp.agreement_rate:.1f}%"
    if comp.agreement_rate < 60.0:
        res.is_eligible = False
        res.reasons.append(
            f"상인회 가입/동의율({comp.agreement_rate:.1f}%)이 법정 최소 기준(60.0%)에 미달합니다."
        )
        res.recommendations.append("상인회 긴급 총회를 소집하여 사업참여 동의서를 추가 징구하십시오.")
    elif comp.agreement_rate < 75.0:
        res.warnings.append(
            f"상인회 동의율({comp.agreement_rate:.1f}%)이 법정 기준을 충족하나 심사위원 우대선(80% 이상)에 다소 미흡합니다."
        )

    # 2. 온누리상품권 가맹률 (기준: 50%)
    res.metrics_summary["온누리_가맹률"] = f"{comp.onnuri_rate:.1f}%"
    if comp.onnuri_rate < 50.0:
        res.is_eligible = False
        res.reasons.append(
            f"온누리상품권 가맹률({comp.onnuri_rate:.1f}%)이 법정 최소 기준(50.0%)에 미달합니다."
        )
        res.recommendations.append("소진공 온누리상품권 원클릭 가맹 신청을 통해 미가맹 점포를 긴급 등록하십시오.")
    elif comp.onnuri_rate < 80.0:
        res.warnings.append(
            f"온누리상품권 가맹률({comp.onnuri_rate:.1f}%)이 80% 미만입니다. 충전식 카드형 온누리상품권 가맹 확대를 권장합니다."
        )

    # 3. 화재안전 설비 (기준: 필수 완료)
    res.metrics_summary["화재안전_적격"] = "적격" if comp.fire_safety_completed else "미완료"
    if not comp.fire_safety_completed:
        res.is_eligible = False
        res.reasons.append(
            "화재알림시설 설치 완료 또는 소방시설 적격 판정 확인서가 구비되지 않았습니다."
        )
        res.recommendations.append("관할 소방서 소방합동점검 완료필증 또는 지자체 화재알림시설 확인서를 보완하십시오.")

    # 4. 3대 고객신뢰 및 결제편의
    res.metrics_summary["가격_원산지_표시율"] = f"{comp.price_tag_rate:.1f}%"
    if comp.price_tag_rate < 80.0:
        res.warnings.append(
            f"가격/원산지 표시율({comp.price_tag_rate:.1f}%)이 공고 권장선(80.0%)에 미달하여 정량평가 감점 우려가 있습니다."
        )
        res.recommendations.append("상인회 자율지도위원회를 통해 가격표시판 전면 부착 캠페인을 시행하십시오.")

    if not comp.customer_line_maintained:
        res.warnings.append("고객선(황색선) 지키기 미준수로 현장 실사 평가 시 불이익을 받을 수 있습니다.")

    if not comp.zero_payment_penalty:
        res.is_eligible = False
        res.reasons.append("최근 1년 이내 신용카드/현금영수증 발급거절 행정처분 이력이 존재하여 신청이 제한됩니다.")

    # 5. 가점 산정 (최대 5점 상한)
    total_bonus = 0.0

    # 청년상인 비율 (10% 이상 2점, 20% 이상 3점)
    if comp.youth_merchant_rate >= 20.0:
        bonus = 3.0
        total_bonus += bonus
        res.bonus_breakdown.append({"항목": "청년상인 밀집도 (20% 이상)", "가점": bonus})
    elif comp.youth_merchant_rate >= 10.0:
        bonus = 2.0
        total_bonus += bonus
        res.bonus_breakdown.append({"항목": "청년상인 밀집도 (10% 이상)", "가점": bonus})

    # 화재공제 가입률 (80% 이상 1점, 100% 가입 2점)
    if comp.fire_insurance_rate >= 95.0:
        bonus = 2.0
        total_bonus += bonus
        res.bonus_breakdown.append({"항목": "화재공제 전점포 가입 (95% 이상)", "가점": bonus})
    elif comp.fire_insurance_rate >= 80.0:
        bonus = 1.0
        total_bonus += bonus
        res.bonus_breakdown.append({"항목": "화재공제 우수 가입 (80% 이상)", "가점": bonus})

    # 친환경 녹색시장
    if comp.eco_friendly_market:
        bonus = 1.0
        total_bonus += bonus
        res.bonus_breakdown.append({"항목": "친환경·다회용기 녹색시장 협약", "가점": bonus})

    # 가점 5.0점 캡 적용
    res.bonus_points = min(total_bonus, 5.0)
    res.metrics_summary["최종_가점"] = f"+{res.bonus_points:.1f}점 (최대 5.0점)"

    return res
