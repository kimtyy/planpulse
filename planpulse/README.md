# PlanPulse (플랜펄스)

> 정부지원사업(중기부/소진공 등) 사업계획서를 자동 생성해 주는 Micro-SaaS
> 
> **기준 공고**: 2027년도 전통시장 및 상점가 활성화 지원사업 (문화관광형, 3개년 20억원)

## 1. 아키텍처 및 폴더 구조
```
planpulse/
├── app.py                     # Streamlit 기반 5단계 문진 및 웹 애플리케이션
├── cli.py                     # 멀티 마켓 자동 생성 배치 CLI
├── test_jojong_build.py       # 가평 조종시장 30P+ 조판 검증 테스트 스크립트
├── HANDOVER_TO_ANTI.md        # 안티(Anti) 전담 작업 지시서 및 30P+ 확장 명세서
├── core/
│   ├── models.py              # 5단계 문진 및 예산 데이터 모델 (Pydantic)
│   ├── validator.py           # 법정 4대 기초역량 적격성 검증 로직
│   ├── work_packages.py       # [신설] 10대 단위사업(WP-01~10) 5대 프레임워크 딥-익스팬션 엔진
│   ├── budget_engine.py       # [확장] 20억원 원단위(단가×수량×횟수) 5페이지 회계 산출내역 엔진
│   ├── psst_engine.py         # PSST LLM 추론 및 개조식 비즈니스 팽창 엔진
│   ├── docx_builder.py        # [최적화] 30P+ 대용량 행정공문서 규격 조판 빌더 (OpenXML 최적화)
│   └── evaluator.py           # 심사위원 평가표(100점) 모의 채점 및 방어 엔진
```

## 2. 빠른 실행 방법

### 1) 가평 조종시장 30P+ 본 사업계획서 검증 및 자동 생성
```bash
python test_jojong_build.py
```

### 2) 터미널 CLI로 다른 시장 사업계획서 즉시 생성
```bash
python cli.py --market "가평 조종시장"
python cli.py --market "속초관광수산시장"
python cli.py --market "전주남부시장"
```

### 3) Streamlit 웹 애플리케이션 실행
```bash
streamlit run app.py
```

## 3. 핵심 모듈별 기능 명세
- **`work_packages.py` [신설]**: 10대 단위세부사업(WP-01~10)을 각 1.5~2페이지씩 5대 프레임워크(추진배경-사업개요-공정도-소요예산-성과지표)로 고밀도 팽창.
- **`budget_engine.py` [확장]**: 20억원의 10대 단위사업별 [단가(원) × 수량 × 횟수 = 총액]이 기재된 총 46개 세목의 5페이지 원단위 회계 세부 산출내역서 자동 생성 및 국비/지방비(각 10억), 사업단 운영비(10.0%), H/W(32.5%) 규정 감사.
- **`docx_builder.py` [최적화]**: 본문 11pt, 표 10pt 폰트 플로어 준수, OpenXML `w:tblHeader`(반복 헤더), `w:cantSplit`(행 분할 방지), `keep_with_next`(제목 이탈 방지)를 엄격히 적용하여 30페이지 이상의 완성형 국책 사업계획서 조판.
- **`validator.py`**: 상인회 가입율(60% 이상), 온누리 가맹률(50% 이상), 화재안전 적격성 판정 및 가점(+5점 한도) 계산.
- **`psst_engine.py`**: Problem-Solution-Scale-up-Team 개조식 공문서 팽창 (`□`, `○`, `-`, `ㆍ`).
- **`evaluator.py`**: 심사위원 평가표(100점 만점) 모의 채점 및 대면 심사용 송곳 Q&A 방어 전략 5선 제시.

