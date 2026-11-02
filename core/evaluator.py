"""
PlanPulse Evaluation Simulator & Defense Strategy Generator
소상공인시장진흥공단 문화관광형시장 심사위원 평가표(100점 만점 + 가점) 기반 모의 채점 및 대면평가 방어 전략 엔진
"""

from typing import Dict, List, Any
from planpulse.core.models import PlanPulseProject
from planpulse.core.validator import validate_statutory_competency
from planpulse.core.budget_engine import audit_budget_compliance


class EvaluationScorecard:
    def __init__(self):
        self.scores: Dict[str, float] = {}
        self.max_scores: Dict[str, float] = {
            "사업추진_타당성_상권분석": 30.0,
            "사업계획_적정성_실현가능성": 35.0,
            "예산편성_단계별추진전략": 20.0,
            "추진체계_사후자생력": 15.0,
        }
        self.bonus_points: float = 0.0
        self.total_score: float = 0.0
        self.grade: str = "A"
        self.pass_probability: str = "매우 높음 (선정 유력)"
        self.feedback_list: List[str] = []
        self.defense_questions: List[Dict[str, str]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scores": self.scores,
            "max_scores": self.max_scores,
            "subtotal": round(sum(self.scores.values()), 1),
            "bonus_points": self.bonus_points,
            "total_score": round(self.total_score, 1),
            "grade": self.grade,
            "pass_probability": self.pass_probability,
            "feedback_list": self.feedback_list,
            "defense_questions": self.defense_questions,
        }


def evaluate_project(project: PlanPulseProject) -> EvaluationScorecard:
    """
    공식 심사 배점표 기반 알고리즘 채점
    """
    card = EvaluationScorecard()
    comp_val = validate_statutory_competency(project.market_profile.competency)
    is_budget_ok, budget_errs, budget_sum = audit_budget_compliance(project.scale_up.budget_items)

    # 1. 사업추진 타당성 및 상권분석 (배점 30점)
    score1 = 0.0
    # 기초역량 (10점 만점)
    if comp_val.is_eligible:
        score1 += 8.5
        if project.market_profile.competency.agreement_rate >= 80.0:
            score1 += 1.5
    else:
        score1 += 4.0
        card.feedback_list.append("법정 4대 기초역량 일부 미달로 1차 서류평가 탈락 위험이 있습니다.")

    # 문제인식 구체성 (10점 만점)
    if len(project.problem.core_crisis_reason) > 20 and project.problem.customer_stay_time_minutes > 0:
        score1 += 9.5
    else:
        score1 += 7.0
        card.feedback_list.append("상권 쇠퇴 원인 및 체류시간 데이터의 구체성을 보강하십시오.")

    # 비전 명확성 (10점 만점)
    if len(project.solution.vision_statement) > 10:
        score1 += 9.5
    else:
        score1 += 7.5

    card.scores["사업추진_타당성_상권분석"] = min(round(score1, 1), 30.0)

    # 2. 사업계획 적정성 및 실현가능성 (배점 35점)
    score2 = 0.0
    # 킬러 콘텐츠 차별성 (15점)
    if len(project.solution.killer_content_concept) > 15:
        score2 += 14.0
    else:
        score2 += 11.0

    # H/W - S/W 균형도 (10점)
    hw_ratio = budget_sum.get("hw_ratio", 32.5)
    if 25.0 <= hw_ratio <= 35.0:
        score2 += 10.0
    elif hw_ratio <= 40.0:
        score2 += 8.5
    else:
        score2 += 6.0
        card.feedback_list.append(f"H/W 비율({hw_ratio:.1f}%)이 다소 높아 시설위주 사업으로 오인될 수 있습니다.")

    # 스마트 편의 및 고객신뢰 (10점)
    if project.solution.smart_convenience and project.market_profile.competency.onnuri_rate >= 80.0:
        score2 += 9.5
    else:
        score2 += 8.0

    card.scores["사업계획_적정성_실현가능성"] = min(round(score2, 1), 35.0)

    # 3. 예산편성 및 단계별 추진전략 (배점 20점)
    score3 = 0.0
    # 3개년 로드맵 타당성 (10점)
    if project.scale_up.year1_goal and project.scale_up.year2_goal and project.scale_up.year3_goal:
        score3 += 9.5
    else:
        score3 += 7.0

    # 20억원 예산 배분 및 운영비 한도 (10점)
    if is_budget_ok:
        score3 += 10.0
    else:
        score3 += 6.5
        card.feedback_list.extend(budget_errs)

    card.scores["예산편성_단계별추진전략"] = min(round(score3, 1), 20.0)

    # 4. 추진체계 및 사후 자생력 (배점 15점)
    score4 = 0.0
    # 사업단 전문성 (5점)
    if len(project.team.project_manager_profile) > 15:
        score4 += 4.8
    else:
        score4 += 3.5

    # 상인회 동의율 및 거버넌스 (5점)
    if project.market_profile.competency.agreement_rate >= 80.0:
        score4 += 5.0
    elif project.market_profile.competency.agreement_rate >= 60.0:
        score4 += 4.0

    # 사후 자생력 (5점)
    if len(project.team.post_management_plan) > 15:
        score4 += 4.8
    else:
        score4 += 3.5

    card.scores["추진체계_사후자생력"] = min(round(score4, 1), 15.0)

    # 가점 합산
    card.bonus_points = comp_val.bonus_points
    base_sum = sum(card.scores.values())
    card.total_score = round(base_sum + card.bonus_points, 1)

    # 등급 산정
    if card.total_score >= 90.0:
        card.grade = "S (최우수)"
        card.pass_probability = "매우 높음 (선정 최상위권 유력)"
    elif card.total_score >= 82.0:
        card.grade = "A (우수)"
        card.pass_probability = "높음 (선정 안정권)"
    elif card.total_score >= 70.0:
        card.grade = "B (보통)"
        card.pass_probability = "경쟁권 (면접 방어 필요)"
    else:
        card.grade = "C (미흡)"
        card.pass_probability = "위험 (계획서 전면 재보완 필요)"

    # 대면 심사 방어 예상 질의 3선 (Q&A Strategy)
    card.defense_questions = [
        {
            "question": f"3년간 20억원의 대규모 예산이 투입되는데, 인프라 조성(H/W) 종료 후 3차년도 이후에도 야시장 및 문화행사가 지속될 수 있습니까?",
            "defense": f"3차년도부터 상인 협동조합 자립 운영 체계로 전환하며, 야시장 매대 운영 수수료 및 PB상품 판매 수익의 20%를 '상인 상생발전기금'으로 상시 적립하여 보조금 중단 후에도 자생적으로 운영되는 수익 환류 모델을 구축했습니다."
        },
        {
            "question": f"현재 상인 평균 연령이 높은 편인데, 스마트 키오스크나 모바일 온누리상품권 등 디지털 결제 시스템에 상인들이 원활히 적응할 수 있습니까?",
            "defense": f"상인 동의율이 {project.market_profile.competency.agreement_rate:.1f}%에 달하며, 사업단 전담 매니저 1:1 방문 코칭과 청년상인 서포터즈를 1:1로 매칭하는 멘토링제를 운영하여 디지털 격차를 해소하고 전 점포 모바일 결제 정착을 실현합니다."
        },
        {
            "question": f"인근 대형마트 및 관광지와 비교할 때 본 시장만의 결정적인 집객 차별화 요소는 무엇입니까?",
            "defense": f"단순 장보기 시장이 아닌 '{project.solution.killer_content_concept}'을 중심으로 인근 관광 자원과 결합된 모바일 스탬프 투어를 운영하여 관광객 평균 체류시간을 {project.problem.customer_stay_time_minutes}분에서 90분 이상으로 극대화하는 머무는 문화체험형 마켓입니다."
        }
    ]

    return card
