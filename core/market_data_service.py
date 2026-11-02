"""전국 전통시장 공공데이터 자동완성 서비스.

검색 우선순위
1) (선택) 공공데이터포털 API: api_key 와 환경변수 MARKET_API_URL 이 모두 설정된 경우에만 호출
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
        "location": "강원특별자치도 속초시 중앙로147번길 16",
        "established_year": 1970, "total_stores": 150, "active_stores": 140,
        "main_items": "수산물, 건어물, 닭강정, 젓갈, 오징어순대",
        "agreement_rate": 85.0, "onnuri_rate": 90.0, "data_quality": _EST,
    },
    {
        "market_name": "전주 남부시장", "region": "전북특별자치도 전주시",
        "location": "전북특별자치도 전주시 완산구 풍남문2길 63",
        "established_year": 1905, "total_stores": 300, "active_stores": 270,
        "main_items": "콩나물국밥, 청년몰 먹거리, 한과, 한약재, 농산물",
        "agreement_rate": 85.0, "onnuri_rate": 90.0, "data_quality": _EST,
    },
    {
        "market_name": "제주 동문시장", "region": "제주특별자치도 제주시",
        "location": "제주특별자치도 제주시 오현길 90",
        "established_year": 1945, "total_stores": 400, "active_stores": 360,
        "main_items": "감귤, 흑돼지, 수산물, 오메기떡, 한라봉",
        "agreement_rate": 85.0, "onnuri_rate": 90.0, "data_quality": _EST,
    },
    {
        "market_name": "춘천 풍물시장", "region": "강원특별자치도 춘천시",
        "location": "강원특별자치도 춘천시 (상세 주소 직접 입력 필요)",
        "established_year": 1990, "total_stores": 100, "active_stores": 90,
        "main_items": "농산물, 닭갈비 재료, 막국수, 잡화",
        "agreement_rate": 80.0, "onnuri_rate": 85.0, "data_quality": _EST,
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
        return int(str(v).strip()[:4] if False else float(str(v).strip()))
    except Exception:
        return default


def _search_api(keyword: str, api_key: str) -> List[Dict[str, Any]]:
    """환경변수 MARKET_API_URL(공공데이터포털 전통시장 API 엔드포인트)이 설정된 경우에만 호출."""
    url = os.environ.get("MARKET_API_URL", "").strip()
    if not url:
        return []
    q = urllib.parse.urlencode({"serviceKey": api_key, "marketName": keyword, "type": "json"})
    try:
        with urllib.request.urlopen(f"{url}?{q}", timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception:
        return []
    items = data.get("response", {}).get("body", {}).get("items", [])
    if isinstance(items, dict):
        items = items.get("item", [])
    out = []
    for it in items if isinstance(items, list) else []:
        stores = _to_int(it.get("storCnt"), 0)
        out.append({
            "market_name": it.get("mrktNm") or it.get("marketName") or keyword,
            "region": it.get("rdnmadr", ""),
            "location": it.get("rdnmadr") or it.get("lnmadr", ""),
            "established_year": _to_int(str(it.get("estblYr", ""))[:4], 1990) or 1990,
            "total_stores": stores, "active_stores": stores,
            "main_items": it.get("trtmntPrdlst", ""),
            "agreement_rate": 70.0, "onnuri_rate": 70.0,
            "data_quality": "공공데이터 API(주소·점포·품목 외 역량수치는 기본값)",
        })
    return out


def search_public_market_data(keyword: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """시장 이름으로 검색해 프로필 후보 리스트를 반환한다. 키워드가 있으면 항상 1건 이상 반환."""
    keyword = (keyword or "").strip()
    if not keyword:
        return []
    results: List[Dict[str, Any]] = []
    if api_key:
        results.extend(_search_api(keyword, api_key))
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
