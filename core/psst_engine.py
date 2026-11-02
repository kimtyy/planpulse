"""
PlanPulse PSST LLM Inference & Business Expansion Engine
사용자 5단계 간이 문진 입력 -> 정부지원사업 표준 PSST 프레임워크 및 개조식 공문서 체계로 비즈니스 팽창(Expansion)
"""

from typing import Dict, Any, Optional
from planpulse.core.models import PlanPulseProject


SYSTEM_PROMPT = """당신은 중소벤처기업부 및 소상공인시장진흥공단의 전통시장·상점가 활성화 지원사업(문화관광형시장 육성사업) 전담 공공 컨설턴트이자 수석 심사위원입니다.
사용자가 입력한 5단계 간이 문진 데이터를 분석하여, 심사위원이 만점을 부여할 수밖에 없는 고밀도의 공문서 표준 사업계획서 문장으로 팽창(Business Expansion)하십시오.

[작성 및 서술 원칙]
1. 문체 및 어조:
   - 철저한 공문서 개조식(Noun-phrase ending) 문체 사용 ('~함', '~추진', '~도모', '~구축', '~확보', '~강화').
   - 절대 문학적 수여동사나 종결어미('~합니다', '~할 것입니다')를 남발하지 말 것.
2. 기호 위계 체계 준수:
   - 1레벨: □ (핵심 전략 및 추진과제)
   - 2레벨: ○ (세부 실행 방안)
   - 3레벨: - (구체적 실행 내용 및 목표 수치)
   - 4레벨: ㆍ (보충 설명, 연계 대상 및 산출물)
3. 정량적 근거 및 기대효과 필수 명시:
   - 체류시간 증대(분 단위), 방문객 증가율(%), 온누리상품권 결제액 신장(%), 매출 증대율 등 수치화된 KPI 제시.
4. PSST 4대 프레임워크와의 완벽한 정렬:
   - P (Problem 인식): 상권 쇠퇴의 구조적 원인(인구감소, 야간 공동화, 고령화) 진단.
   - S (Solution 실현가능성): 킬러 문화관광 콘텐츠 및 H/W-S/W 융합 특성화.
   - S (Scale-up 성장전략): 3개년 연차별 성장 로드맵 및 20억원 예산 배분의 타당성.
   - T (Team 추진체계): 사업단 전문성, 상인회 추진위, 지자체 거버넌스 및 사후 자생력.
"""


def expand_psst_offline(project: PlanPulseProject) -> Dict[str, Any]:
    """
    Frontier LLM 연동 없이도 즉시 작동하는 고품질 결정론적 비즈니스 팽창 엔진
    사용자의 짧은 문진 입력을 실제 소진공 20억원 공고 표준 서식에 부합하는 서술형/개조식 본문으로 완성.
    """
    m = project.market_profile
    p = project.problem
    s = project.solution
    sc = project.scale_up
    t = project.team
    c = m.competency

    expanded = {}

    # 1. 사업 요약 (Executive Summary)
    expanded["executive_summary"] = (
        f"본 사업은 {m.location}에 위치한 전통시장인 [{m.market_name}]을 대상으로, "
        f"당면한 상권 침체({p.core_crisis_reason})를 극복하고 고유의 문화관광 자원({m.main_items})을 결합하여 "
        f"향후 3년간 총 20억원(국비 10억원, 지방비 10억원)을 투입, '2027 문화관광형 명품시장'으로 도약시키는 사업임.\n"
        f"□ 핵심 비전: {s.vision_statement}\n"
        f"□ 킬러 콘텐츠: {s.killer_content_concept}\n"
        f"□ 3대 정량 목표: 평균 체류시간 {p.customer_stay_time_minutes}분 → 90분 이상 확대, "
        f"온누리상품권 가맹률 {c.onnuri_rate:.1f}% → 100% 달성, 3개년 누적 방문객 40% 증대 도모."
    )

    # 2. 문제인식 (Problem)
    expanded["problem_statement"] = [
        f"□ 상권 쇠퇴 및 고객 이탈의 구조적 한계 직면\n"
        f"  ○ 외부 상권 유출 및 방문 고객 고령화 심화\n"
        f"    - 현재 주요 방문 고객층이 '{p.visitor_demographics}'에 편중되어 소비 주도층인 2030 MZ 및 가족단위 유입 단절\n"
        f"    - 당면 핵심 위기: {p.core_crisis_reason}\n"
        f"    - 인근 대형 유통시설 및 온라인 이커머스 확산으로 주중 일평균 매출의 지속적 하락세 지속",
        
        f"□ 체류시간 부족 및 야간·주말 경제 공동화 한계\n"
        f"  ○ 통과형 소비 패턴에 따른 객단가 저하\n"
        f"    - 현행 방문객 평균 체류시간이 {p.customer_stay_time_minutes}분에 불과하여 단순 장보기 위주의 소비 패턴 고착화\n"
        f"    - 야간 및 주말 현황: {p.night_weekend_vitality}\n"
        f"    - 해질녘 이후 조기 폐점 및 조명 어두움으로 인한 '야간 소비 절벽' 현상 가속화",

        f"□ 시장 내·외부 환경 SWOT 종합 분석\n"
        f"  ○ 강점(S): {', '.join(p.swot_strengths) if p.swot_strengths else '우수한 지역 접근성 및 오랜 역사성'}\n"
        f"  ○ 약점(W): {', '.join(p.swot_weaknesses) if p.swot_weaknesses else '노후화된 시설 및 야간 콘텐츠 결여'}\n"
        f"  ○ 기회(O): {', '.join(p.swot_opportunities) if p.swot_opportunities else '지역 생태관광객 증가 및 로컬 미식 열풍'}\n"
        f"  ○ 위협(T): {', '.join(p.swot_threats) if p.swot_threats else '지방 소멸 위기 및 온라인 쇼핑 플랫폼 급성장'}"
    ]

    # 3. 실현가능성 (Solution)
    hw_str = "\n".join([f"    - {hw}" for hw in s.hw_infrastructure]) if s.hw_infrastructure else "    - 야시장 친환경 매대 및 야간 조명 경관거리 조성\n    - 복합 고객쉼터 및 인터랙티브 미디어 포토존 구축"
    sw_str = "\n".join([f"    - {sw}" for sw in s.sw_programs]) if s.sw_programs else "    - 사계절 로컬 푸드 페스티벌 및 주말 버스킹 공연\n    - 지역 특산물 연계 시그니처 PB상품 및 밀키트 개발"
    smart_str = "\n".join([f"    - {sm}" for sm in s.smart_convenience]) if s.smart_convenience else "    - 충전식 카드형 온누리상품권 100% 가맹 및 모바일 결제 지원\n    - 다국어 지원 스마트 안내 키오스크 설치"

    expanded["solution_statement"] = [
        f"□ 비전 및 핵심 추진방향\n"
        f"  ○ 비전: {s.vision_statement}\n"
        f"  ○ 킬러 콘텐츠: {s.killer_content_concept}\n"
        f"  ○ 추진 목표: '찾아오고 머물고 싶은 오감만족 문화관광형 랜드마크 마켓' 구현",

        f"□ 특성화 기반조성 (H/W 인프라 개선)\n"
        f"  ○ 매력적인 시장 공간 리노베이션 및 관광 편의 환경 고도화\n"
        f"{hw_str}\n"
        f"    ㆍ 안전 및 환경 기준: 소방안전 기준 및 화재알림 연동형 전력 부하 관리 시스템 동시 시공",

        f"□ 지역문화콘텐츠 개발 및 활성화 (S/W 프로그램)\n"
        f"  ○ 지역 고유의 자원과 스토리를 결합한 집객형 문화콘텐츠 론칭\n"
        f"{sw_str}\n"
        f"    ㆍ 관광 연계: 인근 주요 관광지 및 레저 명소와 패키징한 모바일 스탬프 투어 운영",

        f"□ 스마트 혁신 및 3대 고객편의 서비스 고도화\n"
        f"  ○ 결제 편의성 극대화 및 고객 신뢰도 제고\n"
        f"{smart_str}\n"
        f"    ㆍ 가격/원산지표시 100% 달성 및 고객선(황색선) 지키기 상시 모니터링 체계 가동"
    ]

    # 4. 성장전략 및 로드맵 (Scale-up)
    expanded["scaleup_statement"] = [
        f"□ 3개년 단계별 추진 로드맵\n"
        f"  ○ 1차년도(2027년, 7.0억원) - [기반조성기]: {sc.year1_goal}\n"
        f"    - 야시장 기반 인프라 조성, 상인회 추진위원회 조직화, 특화 PB 상품 R&D 및 시제품 출시\n"
        f"  ○ 2차년도(2028년, 8.0억원) - [확산·도약기]: {sc.year2_goal}\n"
        f"    - 잣고을 야시장 주말 상설 운영, 광역 축제 연계 홍보, 숏폼 서포터즈 100인 가동, PB 유통망 확장\n"
        f"  ○ 3차년도(2029년, 5.0억원) - [정착·자생력기]: {sc.year3_goal}\n"
        f"    - 상인 협동조합 자립 운영 전환, 전국 우수시장 박람회 유치, 자립형 페스티벌 흑자 구조 안착",

        f"□ 3개년 20억원 연차별 재원 조달 및 비목 배분 원칙\n"
        f"  ○ 총 사업비 20억원: 국비 10억원(50%), 지방비 10억원(50%) 완전 매칭\n"
        f"  ○ 비목 배분 타당성: S/W(문화콘텐츠 및 마케팅) 57.5%, H/W(인프라) 32.5%, 운영비 10.0%로 "
        f"소진공 권장 비율을 엄격 준수하여 일회성 시설투자를 지양하고 지속가능 콘텐츠에 집중 배분"
    ]

    # 5. 사업추진체계 및 팀 역량 (Team)
    expanded["team_statement"] = [
        f"□ 사업단 전담 추진체계 구축 및 전문인력 배치\n"
        f"  ○ 총괄 사업단장: {t.project_manager_profile}\n"
        f"  ○ 전담 조직 구성:\n"
        + "\n".join([f"    - {st}" for st in t.staff_composition]),

        f"□ 상인회 및 민관학 협력 거버넌스 운영\n"
        f"  ○ 상인회 추진위원회: {t.merchant_committee_role}\n"
        f"    - 동의율 {c.agreement_rate:.1f}%의 높은 상인 결속력을 바탕으로 자율정화 및 점포별 특화 동참 유도\n"
        f"  ○ 민관학 거버넌스: {t.local_governance}\n"
        f"    - 지자체 전담부서(일자리경제과 등)와 분기별 운영평가 및 예산 정산 회의 정례화",

        f"□ 사업 종료 후 사후관리 및 자생력 확보 방안\n"
        f"  ○ 지속가능한 자립 플랫폼 구축: {t.post_management_plan}\n"
        f"  ○ 야시장 운영 수익 및 PB상품 판매 수익의 일정 비율을 '상인 상생발전기금'으로 적립하여 지원 종료 후에도 축제 및 시설 유지관리 영구화"
    ]

    return expanded
