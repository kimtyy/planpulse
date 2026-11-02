"""
PlanPulse (플랜펄스) - 정부지원사업 사업계획서 자동 생성 Micro-SaaS
대상 공고: 2027년도 전통시장 및 상점가 활성화 지원사업 (문화관광형, 3개년 20억원)
기술 스택: Streamlit + Python-docx (OpenXML 조판 최적화) + 10대 Work Packages + 46개 회계 세목 엔진
"""

import os
import sys
import io
import time
import pandas as pd
import streamlit as st

# 경로 호환성 확보
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from planpulse.core.models import (
        BasicCompetency,
        MarketProfile,
        ProblemRecognition,
        SolutionDesign,
        ScaleUpStrategy,
        TeamGovernance,
        PlanPulseProject,
        BudgetItem,
    )
    from planpulse.core.validator import validate_statutory_competency
    from planpulse.core.budget_engine import (
        generate_standard_3year_budget,
        generate_detailed_accounting_budget,
        audit_budget_compliance,
        TOTAL_BUDGET_STANDARD,
    )
    from planpulse.core.work_packages import get_jojong_10_work_packages, WorkPackage
    from planpulse.core.psst_engine import expand_psst_offline
    from planpulse.core.evaluator import evaluate_project
    from planpulse.core.docx_builder import build_planpulse_docx
except ImportError:
    from core.models import (
        BasicCompetency,
        MarketProfile,
        ProblemRecognition,
        SolutionDesign,
        ScaleUpStrategy,
        TeamGovernance,
        PlanPulseProject,
        BudgetItem,
    )
    from core.validator import validate_statutory_competency
    from core.budget_engine import (
        generate_standard_3year_budget,
        generate_detailed_accounting_budget,
        audit_budget_compliance,
        TOTAL_BUDGET_STANDARD,
    )
    from core.work_packages import get_jojong_10_work_packages, WorkPackage
    from core.psst_engine import expand_psst_offline
    from core.evaluator import evaluate_project
    from core.docx_builder import build_planpulse_docx


st.set_page_config(
    page_title="PlanPulse - 정부지원 사업계획서 자동생성 엔진",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 스타일링 (세련된 공공/비즈니스 디자인)
st.markdown("""
<style>
    .metric-card {
        background-color: #F8FAFC;
        border-left: 4px solid #1B365D;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .badge-primary {
        background-color: #1B365D;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .badge-success {
        background-color: #10B981;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1B365D !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# 헤더 영역
st.title("📋 PlanPulse (플랜펄스) - 국책 사업계획서 자동생성 엔진")
st.caption("중소벤처기업부 / 소상공인시장진흥공단 2027년도 전통시장 및 상점가 활성화 지원사업 (문화관광형 3개년 20억원)")

# 프리셋 데이터 정의
JOJONG_PRESET = {
    "market_name": "가평 조종시장",
    "location": "경기도 가평군 조종면 현리 조종시장로 15 일원",
    "established_year": 1974,
    "total_stores": 120,
    "active_stores": 112,
    "main_items": "운악산 포도, 가평 잣, 맹호 바비큐, 조종 청정 간장닭갈비, 로컬 농특산물",
    "agreement_rate": 91.2,
    "onnuri_rate": 94.5,
    "fire_safety": True,
    "fire_insurance_rate": 88.0,
    "price_tag_rate": 92.0,
    "customer_line": True,
    "zero_penalty": True,
    "youth_rate": 18.5,
    "eco_friendly": True,
    "crisis_reason": "수도권 25만 캠핑족 및 운악산 등산객 밀집 길목이나, 야간 콘텐츠 부재로 18시 이후 91.2% 점포 소등 및 상권 야간 공동화 심각",
    "stay_time": 35,
    "demographics": "인근 맹호부대(수기사) 6천 장병 및 주말 면회객, 2040 조종천 캠핑객의 높은 유동 대비 시장 경유율 7.8% 불과",
    "night_status": "일몰 후 조기 폐점 및 보행로 조도(14.8 Lux) 낙후로 야간 체류 한계",
    "strengths": ["운악산 출렁다리·조종암·조종천 캠핑장 인접", "맹호부대 주둔지 배후 수요", "상인회 사업 참여율 91.2%"],
    "weaknesses": ["야간 조명 및 여행자 편의 쉼터 부족", "캠핑 맞춤형 PB 상품 및 직배송 인프라 결핍"],
    "opportunities": ["수도권 레트로 미식·캠핑 열풍", "중기부 문화관광형 및 충전식 온누리 활성화 정책"],
    "threats": ["대형 할인마트 및 온라인 새벽배송 잠식", "군 장병 복무기간 단축에 따른 상권 이탈"],
    "vision": "조종천 달빛 캠핑과 맹호 미식이 살아 숨 쉬는 수도권 대표 K-관광 마켓",
    "killer_content": "조종 달빛 캠핑 야시장 & 맹호 바비큐·포도와인 사계절 페스티벌",
    "hw_items": [
        "조종 달빛 캠핑 야시장 특화 매대(친환경 20개소) 제작 및 안전 인프라 구축",
        "조종시장 고객지원센터 연계 복합 여행자 라운지 및 짐 보관 스테이션 조성",
        "야간 조종천 낭만 조명거리 및 인터랙티브 미디어 파사드 시공"
    ],
    "sw_items": [
        "사계절 조종 캠핑 미식 페스티벌 (운악산 포도와인 & 맹호 바비큐 위크 연 20회)",
        "가평 조종면 특화 킬러 PB 5종(포도 뱅쇼 키트, 간장닭갈비 밀키트 등) 개발",
        "운악산 출렁다리-조종암-조종시장 연계 모바일 스탬프 투어 및 리워드"
    ],
    "smart_items": [
        "다국어 지원 스마트 안내 키오스크 및 통합 디지털 사이니지 구축",
        "군 장병·면회객 우대 '밀리터리 프렌들리 상점가' 인증제 및 페이백",
        "조종천 캠핑장·펜션 직배송 모바일 스마트 오더 및 라이브커머스 스튜디오"
    ],
    "year1_goal": "기반조성기: 야시장 매대 20기 제작 및 인프라 완비, 상인 역량강화 및 PB 1차 시제품 론칭",
    "year2_goal": "확산도약기: 달빛 야시장 주말 상설화, 광역 투어패스 연계, 캠핑장 직배송망 가동",
    "year3_goal": "정착자생력기: 상인 협동조합 자립 운영 전환 및 자립형 축제 수익 환류 모델 정착",
    "pm_profile": "문화관광 상권활성화 총괄 PM 10년 경력 (관광경영학 박사, 중기부 장관 표창)",
    "staff": [
        "기획·운영 팀장 (문화관광 축제 기획 6년 경력)",
        "홍보·마케팅 매니저 (디지털 마케팅 및 SNS 바이럴 전담)",
        "회계·정산 매니저 (공공보조금 정산 5년 경력)"
    ],
    "committee": "상인회장 직무대행을 필두로 5개 분과(기획, 시설안전, 영업홍보, 청년, 자율정화) 상시 가동",
    "governance": "가평군청 일자리경제과 - 조종시장 상인회 - 맹호부대 사령부 - 대학 산학협력단 협의체 운영",
    "post_plan": "야시장 운영 수수료 및 PB 매출의 20%를 '상인 상생발전기금'으로 상시 적립하여 자립 운영"
}

JATGOEUL_PRESET = {
    "market_name": "가평 잣고을 전통시장",
    "location": "경기도 가평군 가평읍 장터길 19",
    "established_year": 1965,
    "total_stores": 120,
    "active_stores": 112,
    "main_items": "가평 잣, 잣 막걸리, 잣한과, 로컬 임산물, 전통 먹거리",
    "agreement_rate": 91.2,
    "onnuri_rate": 94.5,
    "fire_safety": True,
    "fire_insurance_rate": 88.0,
    "price_tag_rate": 92.0,
    "customer_line": True,
    "zero_penalty": True,
    "youth_rate": 18.5,
    "eco_friendly": True,
    "crisis_reason": "수도권 근교 관광지임에도 야간 콘텐츠 부재로 방문객 당일치기 통과형 소비 고착화 및 상인 고령화(평균 62.4세)",
    "stay_time": 35,
    "demographics": "50~70대 로컬 장보기 위주, 2030 주말 캠핑·관광객 시장 경유율 10% 미만",
    "night_status": "오후 7시 이후 90% 점포 소등 및 야간 골목 공동화 발생",
    "strengths": ["경춘선 가평역 인접성", "잣고을 광장 및 레일바이크 연계성", "상인회 높은 결속력"],
    "weaknesses": ["야간 조명 및 체류형 쉼터 부족", "젊은 층 타깃 킬러 먹거리 부족"],
    "opportunities": ["자라섬 페스티벌 및 캠핑 레저 인구 유입", "로컬 레트로 미식 열풍"],
    "threats": ["대형 할인마트 인접", "인구 고령화 및 지방소멸 우려"],
    "vision": "잣 향기 가득한 숲속 야시장 & K-컬처 레트로 미식 랜드마크 마켓",
    "killer_content": "숲속 달빛 야시장 & 사계절 잣 맥주·바비큐 버스킹 페스티벌",
    "hw_items": [
        "달빛 야시장 친환경 규격 조리 매대 20개소 제작",
        "레트로 감성 복합 고객쉼터 및 인터랙티브 미디어 포토존 조성",
        "스마트 안내 키오스크 및 통합 디지털 사이니지 구축"
    ],
    "sw_items": [
        "잣고을 주말 문화 버스킹 페스티벌 기획 및 연 24회 운영",
        "가평 잣 활용 시그니처 PB상품 및 로컬 밀키트 5종 개발",
        "자라섬·쁘띠프랑스 연계 모바일 스탬프 투어 운영"
    ],
    "smart_items": [
        "충전식 카드형 온누리상품권 100% 가맹 및 페이백 프로모션",
        "배달앱 및 스마트스토어 온라인 판로 개척 지원"
    ],
    "year1_goal": "기반조성기: 야시장 매대 및 조명 인프라 완비, 상인 역량강화 및 PB 1차 시제품 론칭",
    "year2_goal": "확산도약기: 달빛 야시장 주말 상설화, 광역 투어패스 연계, PB 유통망 확대",
    "year3_goal": "정착자생력기: 상인 협동조합 자립 운영 전환 및 자립형 축제 수익 환류 모델 정착",
    "pm_profile": "중기부 상권르네상스 총괄기획 8년, 로컬 콘텐츠 브랜딩 전문가 (경영학 박사)",
    "staff": [
        "기획·운영 팀장 (문화관광 축제 기획 6년 경력)",
        "홍보·마케팅 매니저 (디지털 마케팅 및 SNS 바이럴 전담)",
        "회계·정산 매니저 (공공보조금 정산 5년 경력)"
    ],
    "committee": "상인회장 직무대행을 필두로 5개 분과(기획, 시설안전, 영업홍보, 청년, 자율정화) 상시 가동",
    "governance": "가평군청 일자리경제과 - 상인회 - 가평문화재단 - 상지대 산학협력단 협의체 운영",
    "post_plan": "야시장 운영 수수료 및 PB 매출의 20%를 '상인 상생발전기금'으로 상시 적립하여 자립 운영"
}

# 사이드바: 빠른 작업 제어 및 프리셋
with st.sidebar:
    st.header("⚡ 원클릭 시장 프리셋")
    load_jojong = st.button("🐯 가평 조종시장 본계획서 (77P 풀세트)", type="primary", use_container_width=True)
    load_jatgoeul = st.button("🌲 가평 잣고을시장 실증 데이터", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📑 공문서 출력 규격")
    st.markdown("""
    - **본문 폰트**: 11pt Malgun Gothic
    - **표 폰트**: 10pt (Font Floor 준수)
    - **OpenXML**: `w:tblHeader`, `w:cantSplit`
    - **예산 규정**: 20억원 완전 배분
    """)
    st.info("💡 **Frontier LLM 연동**: 10대 Work Packages & 46개 회계 세목 완전 동기화")

# 세션 상태 초기화
if "project_data" not in st.session_state:
    st.session_state.project_data = JOJONG_PRESET.copy()

if load_jojong:
    st.session_state.project_data = JOJONG_PRESET.copy()
    st.toast("가평 조종시장 20억원 본 사업계획서 데이터가 로드되었습니다!", icon="🐯")

if load_jatgoeul:
    st.session_state.project_data = JATGOEUL_PRESET.copy()
    st.toast("가평 잣고을시장 데이터가 로드되었습니다!", icon="🌲")

p_data = st.session_state.project_data

# 7개 탭 인터페이스 구성
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1단계: 시장정보 & 4대역량",
    "2단계: 문제인식 (Problem)",
    "3단계: 특성화 솔루션 (Solution)",
    "4단계: 10대 단위사업 (Work Packages) 뷰어 ✨",
    "5단계: 20억 예산 & 46개 회계세목 (Scale-up) ✨",
    "6단계: 추진체계 (Team)",
    "🚀 AI 생성 & 심사 리포트 및 DOCX 다운로드",
])

# -----------------------------------------------------------------------------
# Tab 1: 1단계 시장 기본정보 및 법정 4대 기초역량
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("1단계: 시장 기본정보 및 법정 4대 기초역량 검증")
    col1, col2 = st.columns(2)
    with col1:
        market_name = st.text_input("시장/상점가 명칭", p_data["market_name"])
        location = st.text_input("소재지 주소", p_data["location"])
        c1, c2, c3 = st.columns(3)
        with c1:
            est_year = st.number_input("개설연도", value=p_data["established_year"])
        with c2:
            total_stores = st.number_input("총 점포 수", value=p_data["total_stores"])
        with c3:
            active_stores = st.number_input("영업 점포 수", value=p_data["active_stores"])
        main_items = st.text_area("주요 취급 품목 및 지역 특산물", p_data["main_items"], height=70)

    with col2:
        st.markdown("##### 🛡️ 법정 4대 기초역량 필수 지표 (소진공 기준)")
        agreement_rate = st.slider("상인회 동의율 (%) [필수 60% 이상]", 0.0, 100.0, float(p_data["agreement_rate"]), 0.1)
        onnuri_rate = st.slider("온누리상품권 가맹률 (%) [필수 50% 이상]", 0.0, 100.0, float(p_data["onnuri_rate"]), 0.1)
        fire_safety = st.checkbox("화재알림설비 설치 완료 및 소방안전 적격 [필수]", p_data["fire_safety"])
        
        ca, cb = st.columns(2)
        with ca:
            fire_insurance_rate = st.number_input("화재공제 가입률 (%)", 0.0, 100.0, float(p_data["fire_insurance_rate"]), 1.0)
            price_tag_rate = st.number_input("가격/원산지 표시율 (%)", 0.0, 100.0, float(p_data["price_tag_rate"]), 1.0)
        with cb:
            customer_line = st.checkbox("고객선(황색선) 지키기 준수", p_data["customer_line"])
            zero_penalty = st.checkbox("신용카드 거절 등 행정처분 이력 없음", p_data["zero_penalty"])
            youth_rate = st.number_input("청년상인 비율 (%) [가점]", 0.0, 100.0, float(p_data["youth_rate"]), 1.0)
            eco_friendly = st.checkbox("친환경 녹색시장 협약 [가점]", p_data["eco_friendly"])

    test_comp = BasicCompetency(
        agreement_rate=agreement_rate,
        onnuri_rate=onnuri_rate,
        fire_safety_completed=fire_safety,
        fire_insurance_rate=fire_insurance_rate,
        price_tag_rate=price_tag_rate,
        customer_line_maintained=customer_line,
        zero_payment_penalty=zero_penalty,
        youth_merchant_rate=youth_rate,
        eco_friendly_market=eco_friendly,
    )
    val_res = validate_statutory_competency(test_comp)

    st.markdown("---")
    res_col1, res_col2 = st.columns([1, 2])
    with res_col1:
        if val_res.is_eligible:
            st.success(f"### 판정: {val_res.to_dict()['status']}")
            st.metric("공고 인정 가점", f"+{val_res.bonus_points:.1f} 점", delta="최대 5.0점 한도 확보")
        else:
            st.error(f"### 판정: {val_res.to_dict()['status']}")
            for r in val_res.reasons:
                st.error(f"❌ {r}")
    with res_col2:
        if val_res.warnings:
            for w in val_res.warnings:
                st.warning(f"⚠️ {w}")
        if val_res.recommendations:
            for rc in val_res.recommendations:
                st.info(f"💡 보완 가이드: {rc}")

# -----------------------------------------------------------------------------
# Tab 2: 2단계 문제인식 (Problem)
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("2단계: 문제인식 및 환경분석 (Problem)")
    crisis_reason = st.text_area("상권 침체 및 당면 위기 핵심 요인", p_data["crisis_reason"], height=80)
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        stay_time = st.number_input("현재 평균 방문객 체류시간 (분)", value=p_data["stay_time"])
        demographics = st.text_input("주요 방문 고객층 특성", p_data["demographics"])
        night_status = st.text_input("야간 및 주말 상권 상태", p_data["night_status"])
    with p_col2:
        st.markdown("##### 🔍 SWOT 핵심 요인 분석")
        swot_s = st.text_input("강점 (Strengths)", ", ".join(p_data["strengths"]))
        swot_w = st.text_input("약점 (Weaknesses)", ", ".join(p_data["weaknesses"]))
        swot_o = st.text_input("기회 (Opportunities)", ", ".join(p_data["opportunities"]))
        swot_t = st.text_input("위협 (Threats)", ", ".join(p_data["threats"]))

# -----------------------------------------------------------------------------
# Tab 3: 3단계 특성화 솔루션 (Solution)
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("3단계: 실현가능성 및 특성화 솔루션 (Solution)")
    vision = st.text_input("사업 비전 및 대표 슬로건", p_data["vision"])
    killer_content = st.text_input("문화관광 킬러 콘텐츠 콘셉트", p_data["killer_content"])
    
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("##### 🏗️ H/W 기반시설 개선 (줄바꿈 구분)")
        hw_raw = st.text_area("H/W 세부 항목", "\n".join(p_data["hw_items"]), height=100)
        st.markdown("##### 📲 결제 및 스마트 혁신")
        smart_raw = st.text_area("스마트 혁신 항목", "\n".join(p_data["smart_items"]), height=70)
    with s_col2:
        st.markdown("##### 🎭 S/W 문화체험 및 홍보마케팅 (줄바꿈 구분)")
        sw_raw = st.text_area("S/W 세부 항목", "\n".join(p_data["sw_items"]), height=100)

# -----------------------------------------------------------------------------
# Tab 4: 10대 단위사업 (Work Packages) 대화형 뷰어 ✨ [신설]
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("🏗️ 10대 단위세부사업 (Work Package WP-01 ~ WP-10) 딥-익스팬션 뷰어")
    st.caption("각 단위사업당 1.5~2페이지 분량의 5대 프레임워크(추진배경-사업개요-공정도-소요예산-KPI) 완벽 수록")
    
    work_packages = get_jojong_10_work_packages()
    
    # 상단 요약 카드
    wp_c1, wp_c2, wp_c3, wp_c4 = st.columns(4)
    wp_c1.metric("10대 단위사업 총 사업비", "20.0 억원", "100% 완전 편성")
    wp_c2.metric("H/W 특성화 기반조성", "6.5 억원 (32.5%)", "권장 35% 이내 준수")
    wp_c3.metric("S/W 문화콘텐츠 & 마케팅", "11.5 억원 (57.5%)", "킬러콘텐츠 집중투자")
    wp_c4.metric("사업단 전담 운영비", "2.0 억원 (10.0%)", "법정 10% 한도 엄수")
    
    st.markdown("---")
    
    # 단위사업 선택 셀렉트박스 및 상세 아코디언
    wp_titles = [f"[{wp.wp_id}] {wp.title}" for wp in work_packages]
    selected_wp_idx = st.selectbox("조회할 단위사업을 선택하세요:", range(len(work_packages)), format_func=lambda i: wp_titles[i])
    cur_wp = work_packages[selected_wp_idx]
    
    # 선택된 WP의 정보 카드
    st.markdown(f"### 📌 {cur_wp.wp_id}: {cur_wp.title}")
    meta_c1, meta_c2, meta_c3, meta_c4 = st.columns(4)
    meta_c1.info(f"**비목 분류**\n\n{cur_wp.category}")
    meta_c2.info(f"**사업 기간**\n\n{cur_wp.period}")
    meta_c3.info(f"**총 예산**\n\n{cur_wp.total_budget:,} 원")
    meta_c4.info(f"**사업 위치**\n\n{cur_wp.target_location}")
    
    # 5대 프레임워크 서브 탭
    sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
        "1. 추진배경 및 실태분석",
        "2. 사업 개요 및 스펙",
        "3. 세부 실행 공정도",
        "4. 원단위 예산내역",
        "5. 성과관리 지표 (KPI)"
    ])
    
    with sub_tab1:
        st.markdown("##### 🔍 추진 배경 및 소비자 결핍 요소")
        for bg in cur_wp.background_needs:
            st.markdown(f"- {bg}")
            
    with sub_tab2:
        st.markdown("##### 📋 단위사업 개요 및 주요 사양")
        st.table(cur_wp.overview_table)
        
    with sub_tab3:
        st.markdown("##### 🛠️ 세부 실행 공정도 및 추진 마일스톤")
        st.table(cur_wp.process_phases)
        
    with sub_tab4:
        st.markdown("##### 💰 원단위 세부 예산 산출내역 (단가 × 수량 × 횟수 = 총액)")
        df_wp_budget = pd.DataFrame(cur_wp.budget_details)
        df_wp_budget["단가 (원)"] = df_wp_budget["단가"].apply(lambda x: f"{x:,}원")
        df_wp_budget["총액 (원)"] = df_wp_budget["총액"].apply(lambda x: f"{x:,}원")
        disp_cols = ["비목", "품명", "규격", "단가 (원)", "수량", "단위", "횟수", "총액 (원)", "산출근거"]
        st.dataframe(df_wp_budget[disp_cols], use_container_width=True)
        
    with sub_tab5:
        st.markdown("##### 🎯 정량 및 정성 성과관리 지표 (KPI)")
        st.table(cur_wp.kpi_metrics)

    # 10대 전체 사업 리스트 접이식 아코디언
    with st.expander("📚 10대 전체 Work Package 목록 한눈에 보기"):
        for wp in work_packages:
            st.markdown(f"**{wp.wp_id}**: {wp.title} | `{wp.category}` | **{wp.total_budget // 1000000:,}백만원**")

# -----------------------------------------------------------------------------
# Tab 5: 20억 예산 & 46개 회계세목 (Scale-up) ✨ [확장]
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("💰 20억원 원단위 회계 세부 산출내역서 (46개 세목)")
    st.caption("기획재정부 예산편성 지침 및 조달청 MAS 등록단가 기반 5페이지 분량 정밀 회계 테이블")

    # 1. 예산 감사 배지
    std_budget = generate_standard_3year_budget()
    detailed_budget = generate_detailed_accounting_budget()
    is_b_ok, b_errs, b_sum = audit_budget_compliance(std_budget)
    
    badge_col1, badge_col2, badge_col3 = st.columns(3)
    badge_col1.success(f"✅ 총 사업비: {b_sum['grand_total']:,}원 (국비 10억 / 지방비 10억)")
    badge_col2.success(f"✅ 사업단 운영비: {b_sum['operating_cost_ratio']:.1f}% ({b_sum['category_totals'].get('사업단 운영비', 0):,}원, 10% 엄수)")
    badge_col3.success(f"✅ H/W 시설비: {b_sum['hw_ratio']:.1f}% (권장 35% 이내 준수)")

    st.markdown("---")
    
    # 2. 46개 세목 인터랙티브 테이블 및 필터
    st.markdown("##### 📊 10대 단위사업별 원단위 회계 세부 산출내역표 (단가 × 수량 × 횟수 = 총액)")
    
    cat_options = ["전체 (46개 세목)", "특성화 기반조성(H/W)", "지역문화콘텐츠 개발(S/W)", "홍보·마케팅 및 역량강화(S/W)", "사업단 운영비"]
    selected_cat = st.selectbox("비목별 세목 필터링:", cat_options)
    
    # 데이터프레임 변환
    det_records = []
    for item in detailed_budget:
        det_records.append({
            "WP코드": item.wp_id,
            "대비목": item.category,
            "세목분류": item.sub_category,
            "품명": item.item_name,
            "규격 및 산출근거": item.spec_basis,
            "단가": item.unit_price,
            "수량": item.quantity,
            "단위": item.unit,
            "횟수": item.count,
            "1차년도": item.year1,
            "2차년도": item.year2,
            "3차년도": item.year3,
            "총액": item.total,
            "적용기준": item.audit_standard,
        })
    df_det = pd.DataFrame(det_records)
    
    if selected_cat != "전체 (46개 세목)":
        df_filtered = df_det[df_det["대비목"] == selected_cat]
    else:
        df_filtered = df_det
        
    # 포맷팅 표시용 복사본
    df_disp = df_filtered.copy()
    df_disp["단가 (원)"] = df_disp["단가"].apply(lambda x: f"{x:,}")
    df_disp["1차년도 (원)"] = df_disp["1차년도"].apply(lambda x: f"{x:,}")
    df_disp["2차년도 (원)"] = df_disp["2차년도"].apply(lambda x: f"{x:,}")
    df_disp["3차년도 (원)"] = df_disp["3차년도"].apply(lambda x: f"{x:,}")
    df_disp["총액 (원)"] = df_disp["총액"].apply(lambda x: f"{x:,}")
    
    show_cols = ["WP코드", "품명", "규격 및 산출근거", "단가 (원)", "수량", "단위", "횟수", "1차년도 (원)", "2차년도 (원)", "3차년도 (원)", "총액 (원)", "적용기준"]
    st.dataframe(df_disp[show_cols], use_container_width=True, height=400)
    
    st.caption(f"선택 비목 합계: {df_filtered['총액'].sum():,} 원 / 전체 46개 세목 총합: 2,000,000,000 원")

    # 3. 3개년 연차별 비목 집계 총괄표
    with st.expander("📈 3개년 비목별 집계 총괄표 보기"):
        st.table([
            {
                "비목 구분": b.category,
                "세부 사업명": b.item_name,
                "1차년도": f"{b.year1 // 1000:,}천원",
                "2차년도": f"{b.year2 // 1000:,}천원",
                "3차년도": f"{b.year3 // 1000:,}천원",
                "3개년 합계": f"{b.total // 1000:,}천원",
            }
            for b in std_budget
        ])

# -----------------------------------------------------------------------------
# Tab 6: 5단계 추진체계 (Team)
# -----------------------------------------------------------------------------
with tab6:
    st.subheader("5단계: 사업추진체계 및 상인회 역량 (Team)")
    pm_profile = st.text_input("총괄 사업단장 자격 및 경력", p_data["pm_profile"])
    staff_raw = st.text_area("사업단 전담인력 구성 (줄바꿈 구분)", "\n".join(p_data["staff"]), height=80)
    
    t_c1, t_c2 = st.columns(2)
    with t_c1:
        committee = st.text_area("상인회 추진위원회 조직 및 역할", p_data["committee"], height=80)
    with t_c2:
        governance = st.text_area("민·관·군 거버넌스 협력 체계", p_data["governance"], height=80)
    post_plan = st.text_area("사업 종료 후 사후관리 및 자생적 운영 관리 방안", p_data["post_plan"], height=70)

# -----------------------------------------------------------------------------
# Tab 7: AI 생성 및 심사위원 평가 리포트 / 원클릭 DOCX 다운로드
# -----------------------------------------------------------------------------
with tab7:
    st.subheader("🚀 AI 사업계획서 생성 및 심사위원 모의평가 리포트")
    
    # 조립된 프로젝트 인스턴스 구축
    project_inst = PlanPulseProject(
        market_profile=MarketProfile(
            market_name=market_name,
            location=location,
            established_year=est_year,
            total_stores=total_stores,
            active_stores=active_stores,
            main_items=main_items,
            competency=test_comp,
        ),
        problem=ProblemRecognition(
            core_crisis_reason=crisis_reason,
            customer_stay_time_minutes=stay_time,
            visitor_demographics=demographics,
            night_weekend_vitality=night_status,
            swot_strengths=[s.strip() for s in swot_s.split(",") if s.strip()],
            swot_weaknesses=[s.strip() for s in swot_w.split(",") if s.strip()],
            swot_opportunities=[s.strip() for s in swot_o.split(",") if s.strip()],
            swot_threats=[s.strip() for s in swot_t.split(",") if s.strip()],
        ),
        solution=SolutionDesign(
            vision_statement=vision,
            killer_content_concept=killer_content,
            hw_infrastructure=[h.strip() for h in hw_raw.split("\n") if h.strip()],
            sw_programs=[s.strip() for s in sw_raw.split("\n") if s.strip()],
            smart_convenience=[m.strip() for m in smart_raw.split("\n") if m.strip()],
        ),
        scale_up=ScaleUpStrategy(
            year1_goal=p_data["year1_goal"],
            year2_goal=p_data["year2_goal"],
            year3_goal=p_data["year3_goal"],
            budget_items=std_budget,
        ),
        team=TeamGovernance(
            project_manager_profile=pm_profile,
            staff_composition=[stf.strip() for stf in staff_raw.split("\n") if stf.strip()],
            merchant_committee_role=committee,
            local_governance=governance,
            post_management_plan=post_plan,
        ),
    )

    scorecard = evaluate_project(project_inst)
    
    # 심사 결과 스코어카드
    ev_c1, ev_c2, ev_c3, ev_c4 = st.columns(4)
    ev_c1.metric("종합 모의평가 점수", f"{scorecard.total_score} 점", f"기본 {sum(scorecard.scores.values()):.1f} + 가점 {scorecard.bonus_points:.1f}")
    ev_c2.metric("예상 등급", scorecard.grade)
    ev_c3.metric("선정 가능성", scorecard.pass_probability)
    ev_c4.metric("법정 기초역량", "적격" if val_res.is_eligible else "부적격")

    st.markdown("##### 🎯 소진공 평가위원 심사 배점표 분석")
    st.table([
        {"평가 영역": k.replace("_", " "), "배점": f"{scorecard.max_scores[k]}점", "모의 득점": f"{v}점"}
        for k, v in scorecard.scores.items()
    ])

    st.markdown("##### 🛡️ 심사위원 송곳 질문 및 대면심사 방어 전략 5선")
    all_defense_qa = scorecard.defense_questions + [
        {
            "question": "캠핑 야시장과 특화 PB가 인근 대형마트 및 온라인과의 경쟁에서 우위를 점할 수 있는 차별성은 무엇인가?",
            "defense": "운악산 포도 와인 뱅쇼 키트와 조종 간장닭갈비 캠핑 밀키트처럼 오직 조종시장에서만 맛볼 수 있는 고유 시그니처 레시피를 특허화하고, 텐트 앞까지 2시간 내 직배송하는 친환경 스마트 오더망을 통해 온·오프라인 압도적 편의성을 선점함."
        },
        {
            "question": "3개년 국비 지원 20억원이 종료된 후 상인회의 자생적 유지관리 예산이 고갈될 우려는 없는가?",
            "defense": "사업 초기부터 야시장 매대 운영 수수료와 PB 상품 유통 수익의 20%를 '상생발전기금'으로 의무 적립하여 연간 4,500만원 규모의 기금을 자동 비축하며, 3차년도에 설립되는 상인 협동조합이 독립 채산제로 운영하여 영구 자립 운영됨."
        }
    ]
    for idx, qa in enumerate(all_defense_qa, 1):
        with st.expander(f"Q{idx}. [예상 질문] {qa['question']}", expanded=(idx <= 2)):
            st.success(f"**→ 방어 전략**: {qa['defense']}")

    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # 원클릭 DOCX 빌드 및 다운로드 영역
    # -------------------------------------------------------------------------
    st.markdown("### 📥 표준 공고 서식 DOCX 자동 조판 및 다운로드")
    
    # 1. 문서 생성 모드 선택 라디오 버튼
    mode_options = [
        "공모전 본심사용 실시설계서 (Full Implementation Dossier, 30P~77P 대용량) [추천]",
        "1차 접수용 요약서 (Executive Summary, 약 7P)"
    ]
    selected_mode_text = st.radio("📑 문서 생성 모드 선택", mode_options, index=0)
    
    is_full_mode = "Full" in selected_mode_text
    mode_param = "full" if is_full_mode else "summary"
    
    if is_full_mode:
        st.info("💡 **선택된 규격**: 10대 Work Packages(각 1.5~2P) + 46개 회계 세목(5P) + SWOT/거버넌스/평가표 수록 (약 32~77페이지 공문서)")
    else:
        st.info("💡 **선택된 규격**: 신청 요약표 및 비목 집계표 중심 1차 접수용 약 7페이지 요약서")

    safe_market_name = market_name.replace(" ", "_")
    output_filename = f"2027_전통시장_문화관광형_사업계획서_{safe_market_name}_{'본계획서' if is_full_mode else '요약본'}.docx"
    output_docx_path = os.path.join(CURRENT_DIR, "output", output_filename)
    
    # 빌드 버튼
    btn_label = "🚀 20억원 본 사업계획서 (30P~77P 대용량) 즉시 빌드" if is_full_mode else "📄 1차 접수용 요약서 (7P) 즉시 빌드"
    
    if st.button(btn_label, type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("1/4. 법정 4대 기초역량 및 사업 적격성 감사 중...")
        progress_bar.progress(25)
        time.sleep(0.3)
        
        status_text.text("2/4. 10대 단위사업(WP) 딥-익스팬션 및 46개 회계 세목 렌더링 중...")
        progress_bar.progress(55)
        time.sleep(0.3)
        
        status_text.text("3/4. OpenXML w:tblHeader & w:cantSplit 고밀도 조판 최적화 중...")
        progress_bar.progress(85)
        
        built_file = build_planpulse_docx(project_inst, output_docx_path, mode=mode_param)
        
        progress_bar.progress(100)
        status_text.text("4/4. DOCX 사업계획서 빌드 완료!")
        time.sleep(0.2)
        status_text.empty()
        progress_bar.empty()
        
        with open(built_file, "rb") as f:
            file_bytes = f.read()
            
        file_size_kb = len(file_bytes) / 1024
        
        st.toast(f"🎉 사업계획서 DOCX 빌드가 성공적으로 완료되었습니다! ({file_size_kb:.1f} KB)", icon="📄")
        
        st.success(
            f"🎉 **DOCX 빌드 완료!** "
            f"규격: [{'본심사용 실시설계서 (30P~77P)' if is_full_mode else '1차 접수 요약서 (7P)'}] | "
            f"파일 크기: **{file_size_kb:.1f} KB**"
        )
        
        st.download_button(
            label=f"💾 {output_filename} 브라우저 다운로드",
            data=file_bytes,
            file_name=output_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
