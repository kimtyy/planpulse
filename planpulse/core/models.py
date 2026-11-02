"""
PlanPulse Core Data Models (Pydantic v1 compatible)
전통시장 및 상점가 활성화 지원사업(문화관광형) 5단계 문진 및 데이터 모델
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class BasicCompetency(BaseModel):
    """법정 4대 기초역량 및 가점 항목"""
    agreement_rate: float = Field(..., description="상인회 가입율 및 사업참여 동의율 (%)")
    onnuri_rate: float = Field(..., description="온누리상품권 가맹률 (%)")
    fire_safety_completed: bool = Field(True, description="화재알림설비 설치 완료 또는 소방시설 적격 여부")
    fire_insurance_rate: float = Field(..., description="전통시장 화재공제 가입률 (%)")
    price_tag_rate: float = Field(..., description="가격/원산지 표시율 (%)")
    customer_line_maintained: bool = Field(True, description="고객선(황색선) 지키기 준수 여부")
    zero_payment_penalty: bool = Field(True, description="신용카드/현금영수증 발급거절 제재 이력 없음")
    
    # 가점 항목
    youth_merchant_rate: float = Field(0.0, description="청년상인(만 39세 이하) 점포 비율 (%)")
    eco_friendly_market: bool = Field(False, description="친환경/다회용기 보임 녹색시장 협약 여부")
    local_government_matching_rate: float = Field(50.0, description="지방비 매칭 비율 (%) (기본 50%)")


class MarketProfile(BaseModel):
    """1단계: 시장 기본정보 및 상권 개요"""
    market_name: str = Field(..., description="시장/상점가 정식 명칭")
    location: str = Field(..., description="시장 소재지 (시/군/구 및 도로명주소)")
    established_year: int = Field(..., description="개설연도")
    total_stores: int = Field(..., description="총 점포 수")
    active_stores: int = Field(..., description="영업 점포 수")
    main_items: str = Field(..., description="주요 취급 품목 및 지역 특산물")
    competency: BasicCompetency = Field(..., description="법정 4대 기초역량 지표")


class ProblemRecognition(BaseModel):
    """2단계: 문제인식 및 환경분석 (Problem)"""
    core_crisis_reason: str = Field(..., description="상권 쇠퇴 및 당면 위기 핵심 요인")
    customer_stay_time_minutes: int = Field(..., description="현재 평균 고객 체류시간 (분)")
    visitor_demographics: str = Field(..., description="주요 방문 고객층 및 한계점 (예: 60대 이상 위주)")
    night_weekend_vitality: str = Field(..., description="야간 및 주말/공휴일 상권 활성화 상태")
    swot_strengths: List[str] = Field(default_factory=list, description="강점(S)")
    swot_weaknesses: List[str] = Field(default_factory=list, description="약점(W)")
    swot_opportunities: List[str] = Field(default_factory=list, description="기회(O)")
    swot_threats: List[str] = Field(default_factory=list, description="위협(T)")


class SolutionDesign(BaseModel):
    """3단계: 실현가능성 및 특성화 솔루션 (Solution)"""
    vision_statement: str = Field(..., description="사업 비전 및 슬로건")
    killer_content_concept: str = Field(..., description="핵심 문화관광 킬러 콘텐츠 (야시장, 특화거리 등)")
    hw_infrastructure: List[str] = Field(default_factory=list, description="H/W 기반시설 개선 항목")
    sw_programs: List[str] = Field(default_factory=list, description="S/W 특성화 및 체험·축제 프로그램")
    smart_convenience: List[str] = Field(default_factory=list, description="스마트 결제, 키오스크, 배송 등 편의 혁신")


class BudgetItem(BaseModel):
    category: str = Field(..., description="비목 분류")
    item_name: str = Field(..., description="세부 사업명")
    year1: int = Field(..., description="1차년도 예산 (원)")
    year2: int = Field(..., description="2차년도 예산 (원)")
    year3: int = Field(..., description="3차년도 예산 (원)")
    total: int = Field(..., description="3개년 합계 (원)")
    description: str = Field("", description="산출 내역 및 주요 내용")


class ScaleUpStrategy(BaseModel):
    """4단계: 성장전략 및 3개년 연차별 계획 (Scale-up)"""
    year1_goal: str = Field(..., description="1차년도 핵심 목표 (기반조성)")
    year2_goal: str = Field(..., description="2차년도 핵심 목표 (도약 및 확산)")
    year3_goal: str = Field(..., description="3차년도 핵심 목표 (자생력 및 정착)")
    total_budget: int = Field(2000000000, description="총 사업비 (기본 20억원)")
    government_fund: int = Field(1000000000, description="국비 지원금 (기본 10억원)")
    local_fund: int = Field(1000000000, description="지방비 지원금 (기본 10억원)")
    budget_items: List[BudgetItem] = Field(default_factory=list, description="세부 비목별 예산표")


class TeamGovernance(BaseModel):
    """5단계: 사업추진체계 및 상인회 역량 (Team)"""
    project_manager_profile: str = Field(..., description="사업단장 경력 및 전문성 요약")
    staff_composition: List[str] = Field(default_factory=list, description="사업단 전담인력 구성")
    merchant_committee_role: str = Field(..., description="상인회 추진위원회 조직 및 역할")
    local_governance: str = Field(..., description="지자체(시·군·구), 전문가, 지역자원 연계 체계")
    post_management_plan: str = Field(..., description="3개년 사업 종료 후 자생적 운영 관리 방안")


class PlanPulseProject(BaseModel):
    """전체 사업계획서 프로젝트 통합 스키마"""
    market_profile: MarketProfile
    problem: ProblemRecognition
    solution: SolutionDesign
    scale_up: ScaleUpStrategy
    team: TeamGovernance
