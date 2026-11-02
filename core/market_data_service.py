"""전국 전통시장 공공데이터 자동완성 서비스.

검색 우선순위
1) 공공데이터포털 API: 키가 있을 때만 호출 (인자 / DATA_GO_KR_API_KEY / st.secrets)
2) 내장 대표 시장 프로필 (BUILTIN_MARKETS)
3) 미등록 시장: 시장명/지역 키워드 기반 자동완성 프로필 생성

주의: data_quality 가 "프로젝트 프리셋" 인 값은 PlanPulse 기존 프리셋이고,
"참고용 추정" / "자동 생성" 값은 공식 통계로 검증되지 않은 대략치다.
반드시 소진공 시장정보 등으로 확인 후 수정해야 한다.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

PREFILL_FIELDS = [
    "market_name", "location", "established_year", "total_stores",
    "active_stores", "main_items", "agreement_rate", "onnuri_rate",
]

_EST = "참고용 추정"

BUILTIN_MARKETS: List[Dict[str, Any]] = [
    {
        "market_name": "가평 조종시장", "region": "경기도 가평군",
        "location": "경기도 가평군 조종면 현리 조종시장로 15 일원",
        "established_year": 1974, "total_stores": 120, "active_stores": 112,
        "main_items": "운악산 포도, 가평 잣, 맹호 바비큐, 조종 청정 간장닭갈비, 로컬 농특산물",
        "agreement_rate": 91.2, "onnuri_rate": 94.5, "data_quality": "프로젝트 프리셋",
    },
    {
        "market_name": "가평 잣고을 전통시장", "region": "경기도 가평군",
        "location": "경기도 가평군 가평읍 장터길 19",
        "established_year": 1965, "total_stores": 120, "active_stores": 112,
        "main_items": "가평 잣, 잣 막걸리, 잣한과, 로컬 임산물, 전통 먹거리",
        "agreement_rate": 91.2, "onnuri_rate": 94.5, "data_quality": "프로젝트 프리셋",
    },
    {
        "market_name": "속초관광수산시장", "region": "강원특별자치도 속초시",
        "location": "강원특별자치도 속초시 중앙로147번길 12",
        "established_year": 1953, "total_stores": 450, "active_stores": 440,
        "main_items": "동해안 건어물, 닭강정, 붉은대게 가공식품, 오징어순대",
        "agreement_rate": 85.0, "onnuri_rate": 90.0, "data_quality": "공식 검증(사용자 제공)",
    },
    {
        "market_name": "전주 남부시장", "region": "전북특별자치도 전주시",
        "location": "전북특별자치도 전주시 완산구 풍남문1길 19-3",
        "established_year": 1905, "total_stores": 310, "active_stores": 300,
        "main_items": "전주 콩나물국밥, 피순대, 청년몰 공예품",
        "agreement_rate": 85.0, "onnuri_rate": 90.0, "data_quality": "공식 검증(사용자 제공)",
    },
    {
        "market_name": "제주 동문수산시장", "region": "제주특별자치도 제주시",
        "location": "제주특별자치도 제주시 관덕로14길 20",
        "established_year": 1945, "total_stores": 380, "active_stores": 370,
        "main_items": "제주 은갈치, 옥돔, 감귤·한라봉, 오메기떡",
        "agreement_rate": 85.0, "onnuri_rate": 90.0, "data_quality": "공식 검증(사용자 제공)",
    },
    {
        "market_name": "춘천 풍물시장", "region": "강원특별자치도 춘천시",
        "location": "강원특별자치도 춘천시 영서로 2352-20 (온의동)",
        "established_year": 1989, "total_stores": 160, "active_stores": 150,
        "main_items": "춘천 닭갈비, 막국수, 메밀전병, 로컬 산채류",
        "agreement_rate": 85.0, "onnuri_rate": 90.0, "data_quality": "공식 검증(사용자 제공)",
    },
]

# 지역 키워드 -> (표준 행정구역, 대표 품목 힌트)
REGION_HINTS = {
    "서울": ("서울특별시", "의류, 식료품, 분식"), "부산": ("부산광역시", "수산물, 어묵, 씨앗호떡"),
    "대구": ("대구광역시", "약재, 섬유, 막창"), "인천": ("인천광역시", "수산물, 닭강정, 순대"),
    "광주": ("광주광역시", "떡갈비, 오리탕, 농산물"), "대전": ("대전광역시", "칼국수, 농산물"),
    "울산": ("울산광역시", "수산물, 한우"), "세종": ("세종특별자치시", "로컬푸드, 농산물"),
    "수원": ("경기도 수원시", "통닭, 농산물"), "가평": ("경기도 가평군", "잣, 포도, 농특산물"),
    "양평": ("경기도 양평군", "로컬푸드, 농산물"), "속초": ("강원특별자치도 속초시", "수산물, 닭강정"),
    "강릉": ("강원특별자치도 강릉시", "수산물, 커피, 초당순두부"),
    "춘천": ("강원특별자치도 춘천시", "닭갈비, 막국수"),
    "원주": ("강원특별자치도 원주시", "농산물, 치악산 특산물"),
    "청주": ("충청북도 청주시", "농산물, 육거리 먹거리"),
    "천안": ("충청남도 천안시", "호두과자, 농산물"), "전주": ("전북특별자치도 전주시", "비빔밥, 콩나물국밥"),
    "여수": ("전라남도 여수시", "수산물, 갓김치"), "목포": ("전라남도 목포시", "홍어, 수산물"),
    "포항": ("경상북도 포항시", "과메기, 수산물"), "안동": ("경상북도 안동시", "찜닭, 간고등어"),
    "경주": ("경상북도 경주시", "황남빵, 농산물"), "창원": ("경상남도 창원시", "수산물, 농산물"),
    "통영": ("경상남도 통영시", "수산물, 꿀빵"), "제주": ("제주특별자치도 제주시", "감귤, 흑돼지, 수산물"),
    "서귀포": ("제주특별자치도 서귀포시", "감귤, 수산물"),
}


def _norm(s: str) -> str:
    return re.sub(r"\s+|전통|시장|상점가|관광", "", s or "")


def _build_generated_profile(keyword: str) -> Dict[str, Any]:
    region, items = "", "지역 특산물, 농수산물, 식료품"
    for key, (r, it) in REGION_HINTS.items():
        if key in keyword:
            region, items = r, it
            break
    name = keyword.strip()
    if not name.endswith(("시장", "상점가")):
        name += " 시장"
    return {
        "market_name": name, "region": region or "지역 미확인",
        "location": f"{region} {name} 일원" if region else f"{name} 소재지 (직접 입력 필요)",
        "established_year": 1990, "total_stores": 100, "active_stores": 90,
        "main_items": items, "agreement_rate": 70.0, "onnuri_rate": 70.0,
        "data_quality": "자동 생성(가상값)",
    }


def _to_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(str(v).strip()))
    except Exception:
        return default


API_URL = "http://api.data.go.kr/openapi/tn_pubr_public_trdit_mrkt_api"


def resolve_api_key(api_key: Optional[str] = None) -> Optional[str]:
    """우선순위: 인자 > 환경변수 DATA_GO_KR_API_KEY > Streamlit secrets."""
    if api_key:
        return api_key
    env = os.environ.get("DATA_GO_KR_API_KEY", "").strip()
    if env:
        return env
    try:
        import streamlit as st
        return st.secrets.get("DATA_GO_KR_API_KEY") or None
    except Exception:
        return None


def _search_api(keyword: str, api_key: str) -> List[Dict[str, Any]]:
    """공공데이터포털 전국전통시장표준데이터 API 조회. 실패 시 빈 리스트."""
    q = urllib.parse.urlencode({
        "serviceKey": urllib.parse.unquote(api_key), "type": "json",
        "mrktNm": keyword, "pageNo": "1", "numOfRows": "10",
    })
    try:
        with urllib.request.urlopen(f"{API_URL}?{q}", timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception:
        return []
    items = (data.get("response", {}).get("body", {}) or {}).get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    if isinstance(items, dict):
        items = [items]
    out = []
    for it in items if isinstance(items, list) else []:
        total = _to_int(it.get("storCo"), 0)
        loc = it.get("rdnmadr") or it.get("lnbradr") or ""
        out.append({
            "market_name": it.get("mrktNm") or keyword,
            "region": " ".join(loc.split()[:2]),
            "location": loc,
            "established_year": _to_int(it.get("opnYear"), 0) or 1990,
            "total_stores": total, "active_stores": max(total - 10, 0),
            "main_items": it.get("trtmntPrdlst", ""),
            "agreement_rate": 70.0, "onnuri_rate": 70.0,
            "data_quality": "공공데이터 API(영업점포는 추정, 역량수치는 기본값)",
        })
    return out


def search_public_market_data(keyword: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """시장 이름으로 검색해 프로필 후보 리스트를 반환한다. 키워드가 있으면 항상 1건 이상 반환."""
    keyword = (keyword or "").strip()
    if not keyword:
        return []
    results: List[Dict[str, Any]] = []
    key = resolve_api_key(api_key)
    if key:
        results.extend(_search_api(keyword, key))
    nk = _norm(keyword)
    for m in BUILTIN_MARKETS:
        nm = _norm(m["market_name"])
        if nk and (nk in nm or nm in nk):
            results.append(dict(m))
    if not results:
        results.append(_build_generated_profile(keyword))
    return results


def to_prefill(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {k: profile[k] for k in PREFILL_FIELDS if k in profile}
