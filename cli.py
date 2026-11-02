"""
PlanPulse Multi-Market CLI & Auto-Generator
시장 이름과 기본 키워드만 입력하면 즉시 공고 표준 사업계획서 DOCX를 자동 생성하는 엔진
"""

import os
import sys
import argparse

# Ensure planpulse is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from planpulse.core.models import (
        BasicCompetency,
        MarketProfile,
        ProblemRecognition,
        SolutionDesign,
        ScaleUpStrategy,
        TeamGovernance,
        PlanPulseProject,
    )
    from planpulse.core.budget_engine import generate_standard_3year_budget
    from planpulse.core.docx_builder import build_planpulse_docx
    from planpulse.core.evaluator import evaluate_project
except ImportError:
    from core.models import (
        BasicCompetency,
        MarketProfile,
        ProblemRecognition,
        SolutionDesign,
        ScaleUpStrategy,
        TeamGovernance,
        PlanPulseProject,
    )
    from core.budget_engine import generate_standard_3year_budget
    from core.docx_builder import build_planpulse_docx
    from core.evaluator import evaluate_project


MARKET_DATABASE = {
    "가평 조종시장": {
        "location": "경기도 가평군 조종면 현리 조종시장로 15 일원",
        "established_year": 1974,
        "total_stores": 120,
        "active_stores": 112,
        "main_items": "운악산 포도, 가평 잣, 맹호 바비큐, 로컬 임산물, 전통 먹거리",
        "crisis_reason": "수도권 25만 캠핑족 및 운악산 등산객 밀집 길목이나 야간 콘텐츠 부재로 18시 이후 91.2% 점포 소등 및 상권 공동화 심각",
        "stay_time": 35,
        "demographics": "인근 맹호부대 6천 장병 및 주말 면회객, 2040 조종천 캠핑객의 높은 유동 대비 시장 경유율 7.8% 불과",
        "night_status": "일몰 후 조기 폐점 및 보행로 조도(14.8 Lux) 낙후로 야간 체류 한계",
        "strengths": ["운악산 출렁다리·조종암·조종천 캠핑장 인접", "맹호부대 주둔지 배후 수요", "상인회 사업 참여율 91.2%"],
        "weaknesses": ["야간 조명 및 여행자 편의 쉼터 부족", "캠핑 맞춤형 PB 상품 및 직배송 인프라 결핍"],
        "opportunities": ["수도권 레트로 미식·캠핑 열풍", "중기부 문화관광형 및 충전식 온누리 활성화 정책"],
        "threats": ["대형 할인마트 및 온라인 새벽배송 잠식", "군 장병 복무기간 단축에 따른 상권 이탈"],
        "vision": "조종천 달빛 캠핑과 맹호 미식이 살아 숨 쉬는 수도권 대표 K-관광 마켓",
        "killer_content": "조종 달빛 캠핑 야시장 & 맹호 바비큐·포도와인 사계절 페스티벌",
        "hw_items": [
            "조종 달빛 캠핑 야시장 특화 매대(친환경 20개소) 제작 및 안전 인프라",
            "조종시장 고객지원센터 연계 복합 여행자 라운지 및 짐 보관 스테이션",
            "야간 조종천 낭만 조명거리 및 인터랙티브 미디어 파사드 시공"
        ],
        "sw_items": [
            "사계절 조종 캠핑 미식 페스티벌 (포도와인 & 맹호 바비큐 위크 연 20회)",
            "가평 조종면 특화 킬러 PB 5종(포도 뱅쇼 키트, 간장닭갈비 등) 개발",
            "운악산 출렁다리-조종암-조종시장 연계 모바일 스탬프 투어 및 리워드"
        ],
        "smart_items": [
            "다국어 지원 스마트 안내 키오스크 및 통합 디지털 사이니지 구축",
            "군 장병·면회객 우대 '밀리터리 프렌들리 상점가' 인증제 및 페이백",
            "조종천 캠핑장·펜션 직배송 모바일 스마트 오더 및 라이브커머스 스튜디오"
        ],
        "pm_profile": "문화관광 상권활성화 총괄 PM 10년 경력 (관광경영학 박사, 중기부 장관 표창)",
    },
    "속초관광수산시장": {
        "location": "강원특별자치도 속초시 중앙로147번길 12",
        "established_year": 1953,
        "total_stores": 450,
        "active_stores": 420,
        "main_items": "동해안 건어물, 닭강정, 붉은대게 가공식품, 오징어순대",
        "crisis_reason": "주말·성수기 과밀 및 주차난 반면 평일 비수기 매출 급감, 주 통과형 관광으로 주변 구도심 상생 미흡",
        "stay_time": 45,
        "demographics": "수도권 2040 관광객 및 가족단위 주말 집중, 평일 60대 이상 로컬 주민 위주",
        "night_status": "주말 야간 먹거리 골목 성황이나 평일 저녁 조기 폐점으로 야간 체류 한계",
        "strengths": ["전국구 인지도", "닭강정·해산물 등 킬러 F&B 집적", "속초항·아바이마을 도보 연계"],
        "weaknesses": ["평일·비수기 집객력 저하", "휴게 편의 및 디지털 물품보관함 부족"],
        "opportunities": ["동서고속화철도 개통 예정", "해양레저 및 워케이션 관광객 증가"],
        "threats": ["동해안 타 지자체 야시장 경쟁 심화", "수산물 원가 및 물류비 상승"],
        "vision": "동해의 맛과 멋을 품은 대한민국 대표 K-해양문화관광 마켓",
        "killer_content": "동해안 달빛 씨푸드 야시장 & 속초 붉은대게 쿠킹 버스킹 페스타",
        "hw_items": [
            "친환경 해산물 특화 스마트 야시장 매대 25개소 제작",
            "동해안 바다 감성 미디어아트 휴게 라운지 및 짐 보관센터 조성",
            "글로벌 다국어 스마트 키오스크 및 무인 모바일 결제존 구축"
        ],
        "sw_items": [
            "속초 씨푸드 야간 미식 페스티벌 및 분기별 셰프 콜라보 위크 운영",
            "속초 수산물 연계 시그니처 굿즈 및 대게 스낵 PB 상품 5종 개발",
            "속초 해변·아바이마을 연계 모바일 오션 스탬프 투어 운영"
        ],
        "smart_items": [
            "모바일 온누리상품권 100% 가맹 및 외국인 간편결제(알리/위챗/애플페이) 연동",
            "전국 당일 택배 스마트 물류 스테이션 및 통합 주문 앱 연동"
        ],
        "pm_profile": "해양관광 및 대형 축제 총괄 PM 10년 경력 (관광학 박사)",
    },
    "전주남부시장": {
        "location": "전북특별자치도 전주시 완산구 풍남문1길 19-3",
        "established_year": 1905,
        "total_stores": 310,
        "active_stores": 285,
        "main_items": "전주 콩나물국밥, 피순대, 청년몰 청년창업 굿즈, 공예품",
        "crisis_reason": "한옥마을 관광객의 시장 유입 한계(동선 단절), 청년몰 시설 노후화 및 신규 앵커 콘텐츠 부재",
        "stay_time": 40,
        "demographics": "한옥마을 2030 관광객 및 전주 구도심 로컬 주민",
        "night_status": "금·토 야시장 외 평일 야간 공동화 심화",
        "strengths": ["청년몰 1세대 상징성", "전주한옥마을 인접", "풍남문 역사문화 자원"],
        "weaknesses": ["청년몰 노후화", "평일 야간 콘텐츠 부재", "화재 취약 목조 구조 잔존"],
        "opportunities": ["K-컬처 전통 미식 열풍", "전주 관광거점도시 사업 연계"],
        "threats": ["신도심 상권 이동", "상인 고령화 및 임대료 갈등"],
        "vision": "전통과 청년 문화가 공존하는 K-헤리티지 레트로 관광 마켓",
        "killer_content": "전주 맛의 거리 달빛 야시장 & 청년몰 2.0 로컬 크리에이터 페스타",
        "hw_items": [
            "청년몰 2.0 스마트 리노베이션 및 청년 팝업스토어 인프라 구축",
            "풍남문 연계 야간 전통 등불 테마거리 및 한옥 감성 고객쉼터",
            "소방 연동형 스마트 전기 안전 센서 및 다국어 안내 사이니지 설치"
        ],
        "sw_items": [
            "사계절 전주 미식 버스킹 축제(막걸리·피순대 테마 페어) 운영",
            "전주 청년 크리에이터 협업 로컬 PB 굿즈 및 한옥 밀키트 개발",
            "전주한옥마을-남부시장-풍남문 연계 문화해설 모바일 투어패스 구축"
        ],
        "smart_items": [
            "충전식 온누리상품권 가맹 100% 및 청년몰 스마트 오더 도입",
            "라이브커머스 스튜디오 및 글로벌 택배 원스톱 데스크 운영"
        ],
        "pm_profile": "전통문화재단 및 상권 활성화 사업단 총괄 9년 경력",
    }
}


def generate_market_plan(market_name: str, output_dir: str = "artifacts/file_generation/ttl=63d/output") -> str:
    """임의의 시장에 대해 2027 문화관광형 사업계획서 DOCX를 즉시 생성"""
    preset = MARKET_DATABASE.get(market_name)
    if not preset:
        # 일반 시장 자동 프로파일 생성
        preset = {
            "location": f"대한민국 주요 도심 ({market_name} 상권)",
            "established_year": 1975,
            "total_stores": 150,
            "active_stores": 138,
            "main_items": "지역 농수산물, 전통 먹거리, 생활잡화",
            "crisis_reason": "주변 대형마트 진입 및 온라인 소비 전환에 따른 고객 체류시간 감소",
            "stay_time": 30,
            "demographics": "50~70대 단골 고객 편중, 청년층 및 외래 관광객 유입 부족",
            "night_status": "일몰 후 조기 폐점으로 인한 상권 야간 공동화",
            "strengths": ["오랜 전통과 지역 상징성", "상인회 결속력", "대중교통 접근성"],
            "weaknesses": ["야간 볼거리 부족", "디지털 결제 환경 개선 필요"],
            "opportunities": ["로컬 문화관광 활성화 정책", "지역 축제와의 연계 잠재력"],
            "threats": ["원도심 인구 감소", "온라인 배송 시장 확대"],
            "vision": f"{market_name} 고유의 매력을 살린 지역 대표 문화관광형 명품시장",
            "killer_content": f"{market_name} 사계절 특화 야시장 & 로컬 미식 버스킹 페스티벌",
            "hw_items": [
                "특화 야시장 친환경 규격 조리 매대 제작",
                "복합 고객 쉼터 및 인터랙티브 포토존 조성",
                "스마트 안내 키오스크 및 통합 디지털 사이니지 구축"
            ],
            "sw_items": [
                "주말 문화예술 버스킹 및 로컬 페스티벌 운영",
                "지역 특산물 활용 시그니처 PB상품 및 밀키트 개발",
                "인근 관광자원 연계 모바일 스탬프 투어 운영"
            ],
            "smart_items": [
                "충전식 카드형 온누리상품권 100% 가맹 및 스마트 결제 지원",
                "디지털 역량강화 교육 및 온라인 판로 지원"
            ],
            "pm_profile": "상권 활성화 및 공공 문화프로젝트 총괄 8년 경력 전문가",
        }

    comp = BasicCompetency(
        agreement_rate=92.5,
        onnuri_rate=95.0,
        fire_safety_completed=True,
        fire_insurance_rate=89.0,
        price_tag_rate=93.0,
        customer_line_maintained=True,
        zero_payment_penalty=True,
        youth_merchant_rate=19.0,
        eco_friendly_market=True,
    )

    project = PlanPulseProject(
        market_profile=MarketProfile(
            market_name=market_name,
            location=preset["location"],
            established_year=preset["established_year"],
            total_stores=preset["total_stores"],
            active_stores=preset["active_stores"],
            main_items=preset["main_items"],
            competency=comp,
        ),
        problem=ProblemRecognition(
            core_crisis_reason=preset["crisis_reason"],
            customer_stay_time_minutes=preset["stay_time"],
            visitor_demographics=preset["demographics"],
            night_weekend_vitality=preset["night_status"],
            swot_strengths=preset["strengths"],
            swot_weaknesses=preset["weaknesses"],
            swot_opportunities=preset["opportunities"],
            swot_threats=preset["threats"],
        ),
        solution=SolutionDesign(
            vision_statement=preset["vision"],
            killer_content_concept=preset["killer_content"],
            hw_infrastructure=preset["hw_items"],
            sw_programs=preset["sw_items"],
            smart_convenience=preset["smart_items"],
        ),
        scale_up=ScaleUpStrategy(
            year1_goal="기반조성기: 인프라 정비, 상인 역량강화 및 특화 콘텐츠 시제품 론칭",
            year2_goal="확산도약기: 특화 야시장 상설화, 광역 투어패스 연계, PB 유통망 확대",
            year3_goal="정착자생력기: 상인 협동조합 자립 운영 전환 및 자생적 수익 모델 정착",
            budget_items=generate_standard_3year_budget(),
        ),
        team=TeamGovernance(
            project_manager_profile=preset["pm_profile"],
            staff_composition=[
                "기획·운영 팀장 (문화관광 축제 기획 5년 이상)",
                "홍보·마케팅 매니저 (디지털 마케팅 및 SNS 바이럴 전담)",
                "회계·정산 매니저 (보조금 집행 및 정산 5년 경력)"
            ],
            merchant_committee_role="상인회장을 중심으로 5대 분과(기획, 안전, 영업, 청년, 자율정화) 책임 운영",
            local_governance="지자체(시·군·구 일자리경제과) - 상인회 - 지역 문화재단 - 대학 산학협력단 협의체",
            post_management_plan="야시장 수수료 및 PB 판매 수익의 20%를 상생발전기금으로 적립하여 지속 운영",
        ),
    )

    safe_name = market_name.replace(" ", "_")
    out_file = os.path.join(output_dir, f"2027_전통시장_문화관광형_사업계획서_{safe_name}.docx")
    build_planpulse_docx(project, out_file)
    card = evaluate_project(project)
    print(f"[{market_name}] DOCX 생성 완료: {out_file} (평가점수: {card.total_score}점, 등급: {card.grade})")
    return out_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", type=str, default="속초관광수산시장", help="대상 시장 명칭")
    args = parser.parse_args()
    generate_market_plan(args.market)
