# 강제형 에이전트 개발 워크플로 및 스킬셋 설계 가이드

오픈소스 기능 조합 · 2026 에이전트 코딩 트렌드 · 사내 LLM 맥락 손실 대응

**참조 설계 문서**

기준일: 2026년 7월 13일

대상: 자체 개발 에이전트 워크플로와 재사용 가능한 스킬셋을 설계하는 프로젝트

본 문서는 특정 프레임워크를 그대로 도입하는 제안서가 아니라, 검증된 기능을 선택적으로 조합하고 프로젝트 고유의 정책·상태·평가 계층을 직접 소유하기 위한 설계 자료이다.

# 문서 사용법

이 문서는 현재 에이전트 코딩 생태계에서 주목받는 오픈소스 프로젝트의 기능을 “어디에, 어떤 강도로, 어떤 조건에서” 가져올지 결정하기 위한 참조 아키텍처다. 특히 사내 LLM이 장기 대화나 복잡한 작업에서 목표·제약·결정사항을 놓치는 상황을 전제로 한다.

| **읽는 목적** | **우선 참고할 장** |
| --- | --- |
| **전체 방향을 빠르게 결정** | 1장 핵심 결론, 3장 권장 아키텍처, 14장 최종 청사진 |
| **어떤 오픈소스 기능을 가져올지 선택** | 4장 단계별 기능 매핑, 5장 레포별 평가 |
| **워크플로 강제 수준을 정하기** | 6장 위험도 기반 강제 정책 |
| **사내 LLM 맥락 손실을 줄이기** | 7장 컨텍스트 아키텍처와 평가 기준 |
| **실제 SKILL.md와 저장소 구조 설계** | 8~10장 스킬 계약, 권장 스킬셋, 폴더 구조 |
| **도입과 성과 측정** | 12장 평가·롤아웃, 13장 안티패턴 |

| **중요한 전제** 이 문서에서 “강제”는 에이전트에게 긴 지시문을 항상 주입한다는 뜻이 아니다. 위험도에 따라 필요한 산출물·승인·검증을 결정론적으로 요구하고, 낮은 위험 작업에서는 절차를 줄이는 것을 의미한다. |
| --- |

# 1. 핵심 결론

| **결론** | **설계에 미치는 의미** |
| --- | --- |
| **하나의 거대한 프레임워크보다 조합 가능한 작은 스킬이 유리** | 전체 프로세스는 직접 소유하고, 인터뷰·TDD·리뷰·전문 지식은 외부 스킬에서 차용한다. |
| **전체 워크플로를 항상 동일하게 강제하면 소작업 비용이 폭증** | 작업 위험도와 사내 모델의 맥락 안정성을 함께 점수화해 Fast·Standard·Strict·Controlled 레인으로 분기한다. |
| **사내 LLM의 맥락 손실은 프롬프트만으로 해결되지 않음** | 상태를 파일로 외부화하고 단계별 새 세션·체크포인트·인계 패키지를 기본 구조로 둔다. |
| **에이전트 수보다 라우팅과 출력 계약이 중요** | 전문 에이전트는 필요할 때만 로드하고, 모든 역할은 입력·출력·권한·중단 조건을 명시한다. |
| **LLM 리뷰만으로 완료를 판정하면 안 됨** | 테스트·타입체크·브라우저 실행·정적 분석·변경 범위 검증 같은 결정론적 증거를 완료 조건으로 둔다. |
| **여러 프레임워크를 통째로 겹치면 충돌** | 오케스트레이터는 하나만 두고, 외부 프로젝트에서는 독립 스킬·체크리스트·평가 기법만 가져온다. |

## 권장 기본 구성

| **추천 청사진** 자체 Risk Router + Matt Pocock식 인터뷰·도메인 문서화 + OpenSpec식 변경 단위 명세 + GSD식 체크포인트·상태 파일 + Superpowers식 선택적 TDD·독립 리뷰 + gstack식 QA·릴리스 증거 + wshobson식 전문 플러그인 선택 설치 + 자체 평가·권한·감사 계층 |
| --- |

# 2. 2026년 에이전트 코딩과 스킬 생태계의 흐름

**프로세스 소유형 프레임워크에서 마이크로 스킬로**

GSD·BMAD·Spec Kit처럼 전체 개발 단계를 소유하는 방식과 함께, mattpocock/skills·addyosmani/agent-skills처럼 작고 수정 가능한 SKILL.md를 조합하는 방식이 급성장했다. 최근 대규모 분석에서는 재사용 스킬의 53%가 채택 후 수정되지 않았고, 수정도 주로 프로젝트 경로·도구·도메인 지식 추가에 집중됐다.[T1]

**프롬프트 엔지니어링에서 컨텍스트 엔지니어링으로**

장기 작업의 품질은 한 문장의 프롬프트보다 어떤 정책·도메인 지식·작업 상태·증거를 언제 로드하는지에 좌우된다. 컨텍스트를 에이전트의 운영체제로 보는 흐름이 강해지고 있다.[T5]

**긴 컨텍스트를 크게 만드는 것보다 파일 시스템으로 외부화**

긴 입력을 모델의 주의에만 맡기면 성능이 떨어질 수 있다. 반대로 코딩 에이전트가 파일과 도구를 이용해 대규모 자료를 직접 정리·검색하면 장문 처리 성능이 개선될 수 있다는 연구가 나왔다.[T2]

**전문 에이전트·모델 라우팅**

아키텍처·보안·리뷰에는 강한 모델, 문서·테스트·반복 실행에는 저비용 모델을 쓰는 계층형 라우팅이 일반화되고 있다. 역할 수 자체보다 정확한 라우팅·격리·출력 계약이 중요해졌다.

**평가 가능한 스킬**

스킬을 단순 Markdown이 아니라 버전·회귀·행동 평가가 필요한 소프트웨어 자산으로 다루기 시작했다. wshobson/agents의 plugin-eval, addyosmani/agent-skills의 행동 평가 논의가 대표적이다.

**검증 증거와 감사 가능성**

코드 생성 속도가 빨라질수록 리뷰·검증이 병목이 된다. 완료 보고가 아니라 테스트 로그, 변경 범위, 스펙 추적성, 브라우저·성능·보안 결과를 묶은 evidence bundle이 중요해졌다.

**스킬 공급망과 권한 관리**

스킬은 Markdown처럼 보여도 셸·네트워크·MCP·파일 접근을 유도할 수 있다. 조직에서는 허용된 스킬 카탈로그, 버전 고정, 권한 선언, 자동 실행 훅 검사와 감사 로그가 필요하다.

**모든 작업에 같은 절차가 아닌 적응형 강제**

최근 커뮤니티 불만은 계획·worktree·이중 리뷰가 소작업에도 강제될 때 집중된다. 트렌드는 “가장 엄격한 프레임워크”가 아니라 위험도·모호성·맥락 압력에 따라 절차를 조절하는 방식이다.

| **사내 모델에 대한 해석** 맥락을 자주 놓치는 모델에서는 “더 긴 AGENTS.md”가 해답이 아니다. 항상 로드되는 규칙은 더 짧게 만들고, 단계별로 필요한 파일을 명시적으로 로드하며, 각 단계 시작 시 목표·비목표·제약을 재확인하는 구조가 더 중요하다. 긴 컨텍스트 성능 저하 임계점은 모델마다 다르므로 내부 측정이 필요하다.[T3][T4] |
| --- |

# 3. 권장 시스템 아키텍처

권장 구조는 “하나의 오케스트레이터 + 계층화된 컨텍스트 + 조합 가능한 스킬 + 결정론적 검증기”다. 외부 레포는 각 계층의 부품으로 사용하고, 작업 상태와 정책의 원본은 프로젝트가 직접 소유한다.

| **계층** | **직접 소유할 것** | **외부에서 참고할 기능** |
| --- | --- | --- |
| **A. 정책·헌법** | 보안·데이터·코딩·승인·배포의 비협상 규칙, 금지 도구, 권한 정책 | Spec Kit constitution, 조직 보안 기준 |
| **B. 위험도 라우터** | 작업 점수, 강제 레인, 모델 선택, human gate, context pressure | gstack의 역할 라우팅, Addy의 라이프사이클 구분 |
| **C. 워크플로 상태 머신** | Intake → Clarify → Spec → Plan → Execute → Review → Verify → Ship → Learn | OpenSpec 변경 흐름, GSD 단계·체크포인트, gstack QA/ship |
| **D. 조합형 스킬** | 인터뷰, 도메인 모델링, TDD, 진단, 리뷰, 인계 | mattpocock/skills, Superpowers, addyosmani/agent-skills |
| **E. 전문 에이전트** | 아키텍처·보안·데이터·SRE 등 필요 시 로드되는 역할 | wshobson/agents; agency-agents는 역할 아이디어 참고 |
| **F. 컨텍스트 저장소** | 용어, 결정, 명세, 계획, 상태, 인계, 증거, 소스 맵 | Matt의 CONTEXT/ADR, GSD STATE/ROADMAP, ACE식 점진 갱신 |
| **G. 결정론적 도구** | 테스트, 타입체크, 린트, diff 범위, 정책 검사, 배포 검증 | 각 레포의 명령은 참고하되 실행 로직은 프로젝트에서 관리 |
| **H. 평가·관측** | 스킬 버전, 성공률, 회귀, 토큰·시간, 맥락 회수율, human override | wshobson plugin-eval, Addy eval tier, 자체 golden tasks |

## 권장 워크플로 상태

| **상태** | **핵심 질문** | **필수 산출물** |
| --- | --- | --- |
| **INTAKE** | 무슨 작업이며 어떤 위험이 있는가? | TASK.md, risk score, 선택 레인 |
| **CLARIFY** | 사용자 의도·비목표·용어가 충분히 합의됐는가? | 결정 목록, 도메인 용어 업데이트 |
| **SPEC** | 무엇이 완료되어야 하는가? | SPEC.md, acceptance criteria, constraints |
| **PLAN** | 어떤 경계와 순서로 변경하는가? | PLAN.md, 영향 파일, rollback, test seams |
| **EXECUTE** | 계획과 제약을 지키며 작은 단위로 구현하는가? | 코드, 실행 로그, 상태 체크포인트 |
| **REVIEW** | 스펙 충족과 코드 품질을 독립적으로 검토했는가? | 리뷰 결과, 수정 목록, 미해결 위험 |
| **VERIFY** | 실제 환경에서 완료 증거가 있는가? | EVIDENCE.md, 테스트/브라우저/보안 결과 |
| **SHIP** | 승인·배포·롤백 조건이 충족됐는가? | release record, 배포 증거, rollback point |
| **LEARN** | 다음 작업에 남길 결정·실패 패턴이 있는가? | ADR/LESSONS 업데이트, eval fixture |

## 워크플로 설계의 비협상 원칙

정책·상태·결정의 원본은 대화가 아니라 버전 관리되는 파일이다.

오케스트레이션 스킬은 하나만 실행되며 다른 오케스트레이터를 재귀 호출하지 않는다.

전문 스킬과 에이전트는 필요한 단계에서만 로드한다.

모든 단계는 입력, 출력, 파일 쓰기 범위, 중단 조건, 다음 상태를 명시한다.

고위험 작업은 LLM의 자기평가가 아니라 결정론적 검증과 사람 승인을 요구한다.

워크플로 강제 수준은 작업 특성과 모델의 맥락 신뢰도에 따라 달라진다.

자동화는 기본적으로 가역적이며 destructive action은 별도 승인과 dry-run을 요구한다.

# 4. 단계별로 어떤 레포의 어떤 기능을 가져올 것인가

| **단계** | **추천 원천** | **가져올 기능** | **프로젝트 맞춤화** | **주요 위험** |
| --- | --- | --- | --- | --- |
| **Intake·라우팅** | 직접 구현 + addyosmani/agent-skills | 작업 종류·위험·필요 산출물 분류 | 기존 스킬의 이름보다 프로젝트 고유 위험 점수와 권한 정책을 우선 | 라우터가 복잡하면 모든 작업이 무거워짐 |
| **의도 명확화** | mattpocock/skills: grill-with-docs, grilling | 한 번에 한 질문, 사실은 도구로 확인, 결정만 사용자에게 확인 | 질문 상한·중간 요약·명시적 종료 승인 추가 | 과도한 질문, 모델이 곧바로 구현 시작 |
| **도메인 언어** | mattpocock: domain-modeling, CONTEXT.md, ADR | 용어를 짧고 일관되게 유지하고 지속 결정 기록 | CONTEXT는 용어만; 기능 결정은 SPEC/DECISIONS로 분리 | CONTEXT가 잡동사니 계획서가 되기 쉬움 |
| **변경 명세** | OpenSpec + Matt to-spec | 변경 단위로 요구·비목표·수용 기준 기록 | 프로젝트의 SPEC 스키마와 ID 추적성 도입 | 문서가 실제 구현과 분리될 수 있음 |
| **기업 정책 명세** | GitHub Spec Kit constitution | 조직 규칙과 비기능 요구를 명문화 | 전체 4단계 ceremony가 아니라 정책 템플릿만 차용 | 소작업에 과도한 파일·브랜치 생성 |
| **장기 계획·상태** | GSD/Open GSD | ROADMAP/STATE/체크포인트, 세션 간 지속성 | 상태 포맷과 checkpoint 규칙만 가져오고 전체 프레임워크 의존 축소 | 긴 흐름 자체가 컨텍스트를 소모할 수 있음 |
| **제품·엔지니어링 검토** | gstack: office-hours, plan-eng-review, review | 아이디어·설계·QA·ship 역할 분리 | 핵심 review/QA/ship 스킬만 선택 | 전체 스택은 역할·비용·설치 표면이 큼 |
| **구현 규율** | mattpocock implement/tdd + Superpowers TDD | 작은 vertical slice, red-green-refactor, 완료 전 테스트 | 비즈니스 로직·회귀 위험이 있을 때만 TDD 필수 | 기계적 변경에도 TDD 의식이 과도해질 수 있음 |
| **격리·병렬 작업** | Superpowers worktree, GSD phase isolation | 충돌 방지, 병렬 에이전트 격리 | 병렬·고위험·장기 작업에서만 자동 활성화 | 항상 강제하면 경로 혼동과 운영 비용 증가 |
| **전문가 투입** | wshobson/agents | 아키텍처·보안·언어·SRE 등 플러그인 단위 로드 | 허용 목록과 버전 고정, 출력 계약 축약 | 플러그인/호스트 변환 드리프트, 선택 과잉 |
| **역할 아이디어** | msitarzewski/agency-agents | 직무별 관점·산출물 아이디어 | 페르소나 전체보다 체크리스트와 책임만 추출 | 성격 중심 역할극, 중복 역할, 검증 부족 |
| **독립 리뷰** | Matt code-review + gstack review | 스펙 충족과 코드 품질을 다른 컨텍스트에서 검토 | reviewer는 구현 대화 요약 대신 spec·diff·evidence만 입력 | LLM judge가 서로의 오류를 반복할 수 있음 |
| **검증·출시** | gstack QA/ship + 자체 scripts | 브라우저·테스트·보안·릴리스 증거 묶음 | 결정론적 검증기를 source of truth로 설정 | 완료 보고만 있고 실제 실행 증거가 없을 수 있음 |
| **인계·기억** | Matt handoff + GSD checkpoints | 새 세션이 재구성할 수 있는 최소 인계 | 서술 기록과 실행 prompt를 분리; 커밋/파일 경로 고정 | 요약을 반복 갱신하면 세부가 소실됨 |
| **스킬 배포** | skills.sh, vercel-labs/skills식 패키징 | 도구별 설치·업데이트·선택 설치 | 사내 registry, checksum, 승인 버전 운영 | 자동 업데이트와 공급망 위험 |

| **조합 원칙** OpenSpec + Superpowers + gstack를 “통째로” 동시에 설치하지 않는다. 자체 상태 머신을 중심으로 필요한 스킬만 포팅하며, 동일 기능의 스킬은 하나만 source of truth로 선택한다. |
| --- |

# 5. 주요 레포별 평가와 권장 채택 방식

### mattpocock/skills

| **추천 역할** | 의도 명확화, 도메인 모델링, TDD, 진단, 리뷰, 인계의 기본 코어 |
| --- | --- |
| **채택 방식** | 필요한 SKILL.md를 복사하거나 사내 패키지로 포팅. 인터뷰 종료·산출물 추적·질문 상한을 자체 규칙으로 강화. |
| **강점** | 작고 조합 가능하며 직접 수정하기 쉽다. 오케스트레이션과 재사용 규율을 구분한다. |
| **주의점** | 합의 내용이 PRD·티켓·테스트까지 완전 추적되지 않을 수 있고, 모델이 질문 규칙이나 구현 금지를 어길 수 있다. |
| **적합한 상황** | 자체 워크플로를 만들면서 검증된 엔지니어링 습관을 가져오려는 프로젝트 |
| **주요 출처** | [R1] |

### addyosmani/agent-skills

| **추천 역할** | DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP의 경량 라이프사이클과 폭넓은 품질 기준 |
| --- | --- |
| **채택 방식** | 전체를 설치하기보다 라우터·계획·API/UX/성능/접근성·평가 설계를 참고. Matt 계열과 중복 스킬은 하나만 선택. |
| **강점** | 영역 커버리지가 넓고 스킬 평가·라우팅·agent-first 도구 논의가 활발하다. |
| **주의점** | 페르소나와 스킬 간 중복, 내장 명령 이름 충돌, 평가 fixture가 아직 잠정적인 부분이 있다. |
| **적합한 상황** | 개발 전 생명주기를 균형 있게 참고하거나 품질 체크리스트를 확장할 때 |
| **주요 출처** | [R2] |

### wshobson/agents

| **추천 역할** | 전문 에이전트·스킬·명령을 플러그인 단위로 선택 설치하는 마켓플레이스 |
| --- | --- |
| **채택 방식** | 프로젝트별 allowlist에서 1~3개 전문 플러그인만 설치. 생성된 호스트별 파일은 CI에서 정합성 검사. |
| **강점** | 199개 에이전트, 162개 스킬, 16개 오케스트레이터를 격리된 플러그인으로 제공하고 모델 등급·평가 도구를 갖춘다. |
| **주의점** | 멀티호스트 변환·설치 유지보수 표면이 크고, 숫자가 많아 정확한 선택과 라우팅이 어렵다. |
| **적합한 상황** | 보안·SRE·특정 언어·데이터 등 전문 지식이 일시적으로 필요할 때 |
| **주요 출처** | [R3] |

### msitarzewski/agency-agents

| **추천 역할** | 직무별 책임·산출물·관점 아이디어를 얻는 역할 사전 |
| --- | --- |
| **채택 방식** | 에이전트를 통째로 설치하기보다 필요한 역할 파일에서 책임·체크리스트·성공 지표만 추출. |
| **강점** | 직무 명칭과 기대 결과가 이해하기 쉽고 비개발 역할까지 폭넓다. |
| **주의점** | 페르소나와 말투가 기술적 출력 계약보다 앞설 수 있고, 역할 중복과 품질 편차가 크다. |
| **적합한 상황** | 팀에 부족한 관점을 브레인스토밍하거나 역할 카탈로그를 설계할 때 |
| **주요 출처** | [R4] |

### Fission-AI/OpenSpec

| **추천 역할** | 브라운필드 변경 단위 명세와 점진적 아카이브 |
| --- | --- |
| **채택 방식** | SPEC/CHANGE 구조를 기본 명세 포맷으로 차용하고 프로젝트 상태 머신과 연결. |
| **강점** | GSD·Spec Kit보다 가볍고 기존 코드베이스에 점진적으로 적용하기 좋다. |
| **주의점** | 구현 후 repair, ADR, cross-repo 명세, 강한 독립 검증은 별도 보강이 필요하다. |
| **적합한 상황** | 일상 기능 개발의 기본 명세 계층 |
| **주요 출처** | [R5] |

### GSD / Open GSD

| **추천 역할** | 장기 프로젝트 로드맵, 상태 파일, 체크포인트, 세션 간 지속성 |
| --- | --- |
| **채택 방식** | ROADMAP·STATE·phase checkpoint 개념을 포팅하고 명령·설치기는 최소화. |
| **강점** | 다단계·다세션 작업에서 프로젝트 맥락과 진행 상태를 보존하는 데 강하다. |
| **주의점** | 프로세스 자체가 길고 설정 표면이 넓으며, 컨텍스트 고갈 전에 체크포인트하지 못하는 사례가 있다. |
| **적합한 상황** | 대형 리팩터링, 여러 마일스톤, 내부 모델의 맥락 손실이 잦은 장기 작업 |
| **주요 출처** | [R6] |

### garrytan/gstack

| **추천 역할** | 제품 아이디어, 엔지니어링 검토, 디자인·QA·보안·ship 역할 |
| --- | --- |
| **채택 방식** | office-hours, plan-eng-review, review, QA, ship 등 필요한 단계만 포팅. |
| **강점** | 제품에서 배포까지 현실적인 역할과 증거 흐름을 제공한다. |
| **주의점** | 전체 설치 시 역할·도구·모델·브라우저 의존과 비용이 커지고 호스트 호환 문제가 발생할 수 있다. |
| **적합한 상황** | 제품팀의 설계 검토와 실제 QA·릴리스 증거를 강화할 때 |
| **주요 출처** | [R7] |

### obra/superpowers

| **추천 역할** | TDD, 독립 리뷰, 디버깅 규율, 선택적 worktree 격리 |
| --- | --- |
| **채택 방식** | TDD·spec review·code review를 고위험 레인에서만 필수화. worktree는 병렬·충돌 위험이 있을 때만. |
| **강점** | 에이전트가 바로 코딩하고 자기 결과를 승인하는 행동을 강하게 억제한다. |
| **주의점** | 상세 계획, 이중 리뷰, worktree가 소작업에 적용되면 토큰·시간이 크게 증가하고 경로 혼동이 생길 수 있다. |
| **적합한 상황** | 인증·결제·데이터 변경, 회귀 비용이 큰 기능 |
| **주요 출처** | [R8] |

### github/spec-kit

| **추천 역할** | 조직 헌법, 비기능 요구, 추적성, 표준 산출물 |
| --- | --- |
| **채택 방식** | constitution과 비기능 체크리스트를 정책 계층으로 차용하고 full ceremony는 Strict 이상에서만. |
| **강점** | 기업 정책과 요구사항을 명시적으로 버전 관리하고 팀 표준을 통일하기 좋다. |
| **주의점** | 작은 변경에도 과도한 문서·브랜치·파일을 만들 수 있고 구현 후 수정 루프가 무거워질 수 있다. |
| **적합한 상황** | 규제·감사·플랫폼 계약·조직 표준이 중요한 작업 |
| **주요 출처** | [R9] |

### bmad-code-org/BMAD-METHOD

| **추천 역할** | 전체 SDLC 역할과 산출물, 제품·아키텍처·스토리·QA 프로세스 참고 |
| --- | --- |
| **채택 방식** | 전체 엔진보다 역할별 산출물 템플릿과 회고·스토리 흐름을 선택적으로 참고. |
| **강점** | 비개발 이해관계자가 참여하는 전체 제품 생명주기를 명시한다. |
| **주의점** | 역할 전환·상태 파일·프로세스가 복잡하며 숙련 팀에는 애자일 의식이 과도할 수 있다. |
| **적합한 상황** | 제품 조직 전체의 역할과 산출물을 설계하거나 교육·컨설팅할 때 |
| **주요 출처** | [R10] |

### vercel-labs/skills / skills.sh 계열

| **추천 역할** | 스킬 발견, 설치, 선택 배포와 포터블 패키징 |
| --- | --- |
| **채택 방식** | 사내 승인 registry, 버전 고정, checksum, 도구별 adapter 생성에 참고. |
| **강점** | SKILL.md를 재사용 가능한 패키지로 배포하는 표준화 흐름을 제공한다. |
| **주의점** | 외부 registry를 그대로 신뢰하면 자동 업데이트·악성 스크립트·권한 확장 위험이 있다. |
| **적합한 상황** | 여러 에이전트 도구에 동일한 스킬셋을 배포할 때 |
| **주요 출처** | [R11] |

# 6. 위험도 기반 워크플로 강제 정책

아래 점수는 시작용 휴리스틱이다. 실제 임계값은 사내 LLM과 팀의 작업 데이터로 보정해야 한다. 각 항목을 0~3점으로 평가하고 합계 및 자동 승격 조건으로 실행 레인을 결정한다.

| **평가 기준** | **0점** | **1점** | **2점** | **3점** |
| --- | --- | --- | --- | --- |
| **요구사항 모호성** | 명확한 단일 수정 | 일부 선택 필요 | 여러 이해관계·미정 사항 | 목표·범위 자체가 불명확 |
| **변경 범위** | 1~2 파일, 단일 모듈 | 단일 모듈 여러 파일 | 복수 모듈/API | 복수 저장소·플랫폼 |
| **데이터·보안** | 영향 없음 | 내부 비민감 데이터 | 개인·권한·외부 입력 | 인증·결제·비밀·파괴적 변경 |
| **가역성** | 즉시 revert 가능 | 간단한 롤백 | 데이터/배포 롤백 필요 | 비가역 마이그레이션·외부 계약 |
| **사용자·운영 영향** | 개발 편의 | 제한된 사용자 | 주요 사용자·SLA | 프로덕션 핵심 경로 |
| **병렬성·조정** | 단일 에이전트 | 작업 2개 독립 | 동일 코드베이스 병렬 | 교차 저장소·다중 에이전트 의존 |
| **맥락 압력** | 짧고 독립적 | 기존 지식 일부 필요 | 장기 대화·많은 문서 | 사내 모델이 반복적으로 제약을 놓침 |

| **합계** | **레인** | **강제 수준** | **기본 흐름** |
| --- | --- | --- | --- |
| **0~4** | FAST | 최소 | Intake → Execute → Verify |
| **5~9** | STANDARD | 중간 | Intake → Clarify/Spec → Plan-lite → Execute → Review → Verify |
| **10~14** | STRICT | 강함 | Clarify → Spec 승인 → Plan → 격리 Execute → 독립 Review → Verify → Ship 승인 |
| **15~21** | CONTROLLED | 최강 | STRICT + 보안/데이터 검토 + human gates + dry-run + rollback rehearsal + 감사 로그 |

## 자동 승격 조건

인증·인가, 결제, 개인정보, 비밀정보, 데이터 삭제·마이그레이션은 최소 STRICT.

프로덕션 destructive action, 롤백 불명확, 외부 API 계약 변경은 CONTROLLED.

사내 LLM이 동일 세션에서 핵심 제약을 두 번 이상 누락하면 한 레인 승격 또는 새 세션으로 재시작.

동일 파일을 둘 이상의 에이전트가 수정하거나 cross-repo 의존이 있으면 worktree/sandbox 및 ownership 강제.

테스트가 없거나 관측성이 낮은 영역은 영향 점수와 가역성 점수를 각각 최소 2점으로 처리.

## 레인별 필수 산출물

| **산출물** | **FAST** | **STANDARD** | **STRICT** | **CONTROLLED** |
| --- | --- | --- | --- | --- |
| **TASK.md** | 필수 | 필수 | 필수 | 필수 |
| **명시적 비목표** | 권장 | 필수 | 필수 | 필수 |
| **SPEC.md** | 선택 | 간략 | 상세 | 상세+승인 |
| **PLAN.md** | 선택 | 간략 | 필수 | 필수+rollback |
| **ADR** | 불필요 | 장기 결정 시 | 중요 결정 시 | 필수 검토 |
| **worktree/sandbox** | 불필요 | 병렬 시 | 기본 권장 | 필수 |
| **독립 spec review** | 불필요 | 선택 | 필수 | 필수+사람 검토 |
| **결정론적 증거** | 최소 테스트 | 테스트·lint | 전체 검증 | 전체+보안/배포 |
| **human approval** | 불필요 | 예외 시 | ship 전 | 단계별 |
| **HANDOFF/checkpoint** | 불필요 | 장기 시 | 단계별 | 단계별+감사 |

| **맥락 취약성 가중치** 사내 LLM이 논리적으로 약하지 않더라도 장문에서 제약을 잊는다면 “모델 품질”보다 “맥락 압력”을 위험 기준으로 취급한다. 같은 코드 변경이라도 대화·문서·도구 로그가 많으면 레인을 승격하거나 단계별 새 세션을 강제한다. |
| --- |

# 7. 사내 LLM의 맥락 손실을 전제로 한 컨텍스트 아키텍처

## 7.1 문제 정의

긴 컨텍스트를 지원한다는 것과 그 안의 모든 제약을 안정적으로 사용하는 것은 다르다. 최근 연구는 일부 모델에서 컨텍스트가 길어질수록 임계점 이후 성능이 급격히 하락하거나, 긴 에이전트 로그에서 위험 행동을 놓치는 비율이 크게 증가할 수 있음을 보여준다.[T3][T4] 반면 파일 시스템과 도구를 적극 활용하는 코딩 에이전트는 장문 자료를 외부 구조로 조직해 더 효과적으로 처리할 수 있다.[T2]

따라서 사내 모델에 대한 목표는 “모든 정보를 한 번에 기억시키기”가 아니라 “필요한 정보를 정확히 재구성할 수 있게 만들기”여야 한다.

## 7.2 다섯 종류의 기억을 분리

| **기억 종류** | **내용** | **권장 파일** | **수명** | **쓰기 주체** |
| --- | --- | --- | --- | --- |
| **정책 기억** | 금지 사항, 권한, 승인, 품질 기준 | CONSTITUTION.md / policy.yaml | 장기 | 관리자·보안 |
| **의미 기억** | 도메인 용어, 개념 관계, 시스템 경계 | GLOSSARY.md / CONTEXT.md / CONTEXT-MAP.md | 장기 | domain-modeling skill + 사람 |
| **결정 기억** | 왜 선택했는지, 대안, 결과 | ADR/*.md / DECISIONS.md | 장기 | clarify/spec 단계 |
| **작업 기억** | 현재 목표, 계획, 진행, 다음 행동 | TASK.md / PLAN.md / STATE.json | 작업 수명 | 오케스트레이터 |
| **증거 기억** | 테스트, diff, 로그, 스크린샷, 배포 결과 | EVIDENCE.md / artifacts/ | 작업+감사 | 도구·검증기 |
| **인계 기억** | 새 세션이 재구성할 최소 정보 | HANDOFF.md | 단계/세션 | handoff skill |

## 7.3 항상 로드하는 정보는 최소화

AGENTS.md나 시스템 프롬프트에는 모든 설계 지식이 아니라 다음만 둔다.

프로젝트의 워크플로 진입점과 상태 파일 위치

비협상 보안·권한 규칙과 destructive action 금지

작업 시작 시 읽어야 할 TASK/STATE/CONTEXT-MAP 경로

완료 전에 실행해야 하는 결정론적 검증 명령

불확실하거나 맥락이 충돌할 때 중단하고 재구성하는 규칙

나머지 기술 지식·도메인 설명·과거 결정은 CONTEXT-MAP을 통해 필요할 때만 로드한다. “항상 로드되는 문서의 길이”를 줄이는 것이 첫 번째 최적화다.

## 7.4 단계별 Context Package

**권장 작업 디렉터리**

| task/<TASK-ID>/
├── TASK.md          # 목표, 비목표, 위험 점수, 현재 레인
├── DECISIONS.md     # 인터뷰에서 확정된 결정과 미결정 항목
├── SPEC.md          # 수용 기준, 제약, 추적 ID
├── PLAN.md          # 단계, 영향 파일, 테스트 경계, 롤백
├── STATE.json       # 현재 단계, 완료 항목, 다음 행동, 커밋 SHA
├── EVIDENCE.md      # 실행한 검증과 결과 위치
├── HANDOFF.md       # 새 세션용 재구성 지침
└── artifacts/       # 로그, 리포트, 스크린샷 |
| --- |

## 7.5 Context Refresh Protocol

각 단계 시작 시 TASK.md, STATE.json, 해당 단계 산출물만 새 컨텍스트에 로드한다.

에이전트는 작업 전에 목표·비목표·핵심 제약·현재 단계·완료 조건을 구조화해 다시 진술한다.

재진술 결과를 원본 파일과 결정론적으로 비교하거나 최소한 constraint ID 누락을 검사한다.

단계 중 중요한 결정이 생기면 대화 요약이 아니라 DECISIONS/ADR에 append-only로 기록한다.

긴 도구 출력은 원문을 artifacts에 저장하고 EVIDENCE에는 결과·경로·해시만 남긴다.

단계 완료 후 HANDOFF를 만들고 다음 단계는 가능하면 새 세션·새 서브에이전트에서 시작한다.

요약을 반복해서 다시 요약하지 않는다. 이전 요약을 덮어쓰기보다 원본 링크와 변경분을 유지한다.

## 7.6 체크포인트 트리거

| **트리거** | **권장 행동** |
| --- | --- |
| **단계 완료** | STATE, DECISIONS, EVIDENCE, HANDOFF 갱신 후 새 세션 고려 |
| **핵심 제약 누락 1회** | 현재 단계 중단, source files 재로드, 제약 재진술 |
| **핵심 제약 누락 2회** | 새 세션으로 재시작 또는 상위 모델/사람 검토로 승격 |
| **대규모 도구 로그·diff 생성** | 원문을 파일로 이동하고 요약·인덱스만 컨텍스트에 유지 |
| **작업 범위 변경** | 기존 SPEC/PLAN을 직접 덮지 않고 change record 생성 후 재승인 |
| **병렬 에이전트 결과 합류** | 각 HANDOFF와 evidence를 병합하는 별도 integrator 세션 사용 |
| **모델이 현재 디렉터리·브랜치 혼동** | 즉시 stop; pwd/git status/commit SHA를 결정론적으로 재확인 |

## 7.7 시작용 컨텍스트 예산 휴리스틱

아래 비율은 보편 법칙이 아니라 내부 실험의 시작점이다. 실제 모델별로 성공률과 비용을 측정해 조정한다.

| **구성** | **권장 시작 범위** | **설계 의도** |
| --- | --- | --- |
| **항상 로드되는 정책·라우팅** | 전체 유효 컨텍스트의 10~15% 이하 | 고정 지시가 작업 정보와 경쟁하지 않게 함 |
| **TASK/SPEC/현재 상태** | 10~20% | 현재 작업 계약을 충분히 명확하게 유지 |
| **온디맨드 코드·도메인 자료** | 25~40% | 경로와 질문을 기준으로 필요한 자료만 선택 |
| **도구 출력·diff·검증 결과** | 15~25% | 원문은 파일에 두고 핵심 결과만 로드 |
| **추론·예외·응답 여유** | 20% 이상 | 임계점 접근과 출력 잘림 방지 |

## 7.8 사내 모델용 맥락 신뢰도 평가

| **평가 시나리오** | **측정 항목** | **실패 시 설계 조치** |
| --- | --- | --- |
| **Buried constraint** | 긴 문서 중간의 금지 조건을 구현에 반영하는가 | critical constraint를 TASK 상단과 phase gate에 반복 |
| **Cross-file reasoning** | 여러 파일의 인터페이스·불변식을 연결하는가 | CONTEXT-MAP, 명시적 파일 목록, symbol query 도구 |
| **Long-running execution** | 여러 단계 후에도 목표·비목표가 유지되는가 | 단계별 새 세션, checkpoint, state machine |
| **Tool-log distraction** | 긴 테스트·빌드 로그 뒤에도 핵심 실패를 식별하는가 | 구조화 로그 파서, 실패 요약기, 원문 외부화 |
| **Role switching** | 구현자에서 리뷰어로 전환 시 자기합리화를 피하는가 | 새 컨텍스트 독립 reviewer, 구현 대화 미주입 |
| **Handoff reconstruction** | HANDOFF만으로 다음 세션이 정확히 재개하는가 | handoff template 개선, commit/file refs 추가 |
| **Conflict detection** | SPEC·PLAN·코드가 충돌할 때 멈추는가 | constraint ID와 자동 trace 검사, fail-closed |
| **Directory/branch awareness** | worktree·브랜치 위치를 끝까지 유지하는가 | 각 명령 전 cwd/ref guard, shell wrapper |

## 7.9 Context Health Gate 예시

**개념적 게이트 스키마**

| phase_start_gate:
  require:
    - task_id
    - current_phase
    - goal_summary
    - non_goals
    - critical_constraints[]
    - expected_outputs[]
    - repo_root
    - branch_or_worktree
    - baseline_commit
  checks:
    - every critical constraint ID is present
    - current git ref matches STATE.json
    - required source files are readable
    - no unresolved decision blocks execution
  on_failure:
    - stop
    - refresh context package
    - escalate lane after repeated failure |
| --- |

| **권장 운영 원칙** 사내 모델을 “기억이 약한 사람”처럼 보조하는 것이 아니라 “상태를 직접 소유하지 않는 실행 엔진”으로 취급한다. 상태·정책·결정은 시스템이 소유하고 모델은 매 단계 이를 재구성해 작업한다. |
| --- |

# 8. 스킬 분류와 표준 계약

## 8.1 네 종류로 분리

| **종류** | **설명** | **예시** | **핵심 제약** |
| --- | --- | --- | --- |
| **사용자 호출 오케스트레이터** | 사람이 시작하고 단계·질문·산출물을 조정 | /intake, /grill, /plan, /ship | 다른 사용자 호출 오케스트레이터를 재귀 호출하지 않음 |
| **모델 호출 규율 스킬** | 작업 중 조건이 맞으면 자동 적용되는 엔지니어링 원칙 | tdd, domain-modeling, minimal-change, code-design | 작고 단일 목적; 상태 머신을 소유하지 않음 |
| **전문 에이전트** | 별도 컨텍스트에서 특정 관점으로 분석·실행 | security reviewer, SRE, database expert | 입력과 출력 스키마, 읽기/쓰기 권한 제한 |
| **결정론적 실행기** | LLM 없이 명령·정책·검증을 수행 | test runner, diff guard, policy checker | 성공/실패와 증거 경로를 기계 판독 가능하게 반환 |

## 8.2 SKILL.md 계약 필드

| **필드** | **필수 내용** |
| --- | --- |
| **name / version** | 고유 이름, semantic version, upstream source와 commit |
| **purpose** | 한 문장으로 정의된 단일 책임 |
| **invocation** | user-invoked / model-invoked / internal-only |
| **triggers / anti-triggers** | 언제 써야 하며 언제 쓰면 안 되는가 |
| **preconditions** | 필요한 상태·파일·승인·도구 |
| **context inputs** | 정확한 파일과 데이터; 전체 저장소를 암묵적으로 요구하지 않음 |
| **questions** | 사용자에게 물을 결정과 도구로 확인할 사실을 구분 |
| **outputs** | 파일·JSON·리뷰 결과의 스키마와 추적 ID |
| **state writes** | 수정 가능한 파일과 append/replace 정책 |
| **tools / permissions** | 허용 도구, 네트워크, 셸, 쓰기 경로, destructive 금지 |
| **stop conditions** | 불확실성, 충돌, 실패, 승인 대기 시 중단 규칙 |
| **handoff** | 다음 상태, 필요한 evidence와 context package |
| **evals** | positive/negative/pressure/long-context 테스트 케이스 |
| **observability** | 시작·완료·실패·비용·모델·버전 로그 |

## 8.3 스킬 템플릿

**예시: 프로젝트 맞춤형 clarify 스킬**

| ---
name: clarify-with-docs
version: 0.1.0
invocation: user
purpose: Resolve product and design decisions before specification.
source: mattpocock/skills@<commit>
---

## Trigger
Use when requirements, terminology, scope, or trade-offs are unresolved.
Do not use for mechanical changes with an approved spec.

## Preconditions
- TASK.md exists
- current phase is CLARIFY
- repo facts may be inspected with read-only tools

## Process
1. Read TASK.md and relevant CONTEXT-MAP entries.
2. Ask one decision question at a time; include a recommended answer.
3. Look up facts instead of asking the user.
4. Every 5 decisions, summarize unresolved branches.
5. Never implement; require explicit transition approval.

## Writes
- Append decisions to DECISIONS.md with D-IDs.
- Update glossary terms only in CONTEXT.md.
- Create ADR only for durable architectural decisions.

## Stop
- conflicting source documents
- security or legal ambiguity
- context recall gate failure

## Output
- resolved_decision_ids[]
- unresolved_decision_ids[]
- proposed_next_phase
- context_files_modified[] |
| --- |

# 9. 권장 V1 스킬셋

처음부터 수십 개 에이전트를 만들지 말고, 아래 7개 사용자 호출 코어와 5개 모델 호출 규율로 시작하는 것이 적절하다.

| **스킬** | **종류** | **주요 원천** | **책임** | **강제 레인** |
| --- | --- | --- | --- | --- |
| **/intake** | 오케스트레이터 | 자체 + Addy | 작업 분류, 위험 점수, 모델·레인·상태 생성 | 모든 레인 |
| **/clarify** | 오케스트레이터 | Matt grill-with-docs | 질문, 용어, 결정, 비목표 확정 | STANDARD 이상 또는 모호성>0 |
| **/spec** | 오케스트레이터 | OpenSpec + Matt to-spec | 수용 기준, 제약, 추적 ID, 변경 명세 | STANDARD 이상 |
| **/plan** | 오케스트레이터 | GSD + gstack plan review | 단계, 영향 파일, 테스트 seam, rollback | STANDARD 간략 / STRICT 상세 |
| **/implement** | 오케스트레이터 | Matt implement + Superpowers | 작은 단위 구현, 상태 갱신, 규율 스킬 호출 | 모든 레인 |
| **/review** | 오케스트레이터 | Matt code-review + gstack | spec/standards 독립 리뷰와 수정 루프 | STANDARD 이상 |
| **/verify-ship** | 오케스트레이터 | gstack QA/ship + 자체 scripts | evidence 수집, 승인, 배포·롤백 기록 | 모든 레인; 강도 차등 |
| **domain-modeling** | 모델 규율 | Matt | 용어·경계·ADR 갱신 | 필요 시 |
| **tdd** | 모델 규율 | Matt/Superpowers | red-green-refactor와 vertical slice | 회귀 위험/STRICT |
| **diagnosing-bugs** | 모델 규율 | Matt/Superpowers | 재현→최소화→가설→계측→수정→회귀 | 버그 작업 |
| **minimal-change** | 모델 규율 | agency-agents 아이디어 + 자체 | 요청 외 변경·리팩터링 억제 | FAST/STANDARD |
| **context-checkpoint** | 모델 규율 | GSD + 자체 | STATE/EVIDENCE/HANDOFF 갱신 | 장기·STRICT 이상 |

## 선택형 전문 플러그인

| **영역** | **추천 역할** | **로드 조건** | **출력** |
| --- | --- | --- | --- |
| **아키텍처** | software architect / codebase design | 복수 모듈, 새 경계, 대형 리팩터링 | 대안·trade-off·ADR 후보 |
| **보안/IAM** | security, identity-access | 인증·권한·외부 입력·비밀 | threat model, severity, blocking findings |
| **데이터** | database optimizer / data engineer | 스키마·쿼리·마이그레이션 | migration plan, rollback, validation queries |
| **SRE/운영** | SRE / incident commander | 배포·SLO·장애·용량 | runbook, SLO impact, observability gaps |
| **프론트엔드/UX** | frontend / accessibility | UI·브라우저·접근성 | browser evidence, a11y findings |
| **결제** | payments & billing | 결제·웹훅·구독 | idempotency, reconciliation, failure scenarios |

# 10. 권장 저장소 구조와 파일 책임

**권장 구조**

| .agent-system/
├── CONSTITUTION.md          # 비협상 정책
├── risk-policy.yaml         # 점수와 자동 승격
├── model-policy.yaml        # 모델/비용/권한 라우팅
├── workflows/               # 유일한 상태 머신
├── skills/                  # 사용자·모델 호출 스킬
├── agents/                  # 선택형 전문 역할
├── tools/                   # 결정론적 실행기
├── adapters/                # Claude/Codex/Cursor/사내 런타임 변환
├── evals/                   # golden tasks, context stress tests
└── registry.lock            # 승인 스킬 버전·해시

docs/agent-context/
├── CONTEXT-MAP.md           # 어떤 질문에 어떤 문서를 읽는지
├── GLOSSARY.md              # 도메인 용어만
├── adr/                     # 장기 결정
├── architecture/            # 시스템 경계와 인터페이스
└── lessons/                 # 검증된 반복 실패 패턴

tasks/<TASK-ID>/
├── TASK.md
├── DECISIONS.md
├── SPEC.md
├── PLAN.md
├── STATE.json
├── EVIDENCE.md
├── HANDOFF.md
└── artifacts/ |
| --- |

## 파일 소유권 규칙

| **파일** | **쓰기 권한** | **금지 사항** |
| --- | --- | --- |
| **CONSTITUTION.md** | 관리자/보안 승인 PR | 작업 에이전트가 임의 변경 |
| **GLOSSARY.md** | domain-modeling 제안 + 사람 리뷰 | 기능 요구·계획·임시 메모 저장 |
| **ADR** | spec/architecture 단계 + 승인 | 이미 승인된 결정을 조용히 덮어쓰기 |
| **TASK/SPEC/PLAN** | 해당 상태의 오케스트레이터 | 구현자가 요구사항을 자신에게 유리하게 수정 |
| **STATE.json** | 오케스트레이터/결정론적 상태 도구 | 자유 형식 서술, 커밋/ref 누락 |
| **EVIDENCE.md** | 검증기·도구 + 오케스트레이터 | 실행하지 않은 테스트를 완료로 표시 |
| **HANDOFF.md** | context-checkpoint skill | 대화 요약만 남기고 원본 경로·SHA 생략 |
| **registry.lock** | 관리자/CI | 자동 최신 버전 무검증 설치 |

# 11. 대표 실행 시나리오

## 시나리오 A: 작은 UI 문구와 스타일 수정

점수 예: 2점, FAST. /intake가 범위와 비목표를 TASK에 기록하고, minimal-change 규율로 구현한 뒤 lint·타입체크·브라우저 스냅샷만 요구한다. grill, 상세 SPEC, worktree, 이중 리뷰는 생략한다.

## 시나리오 B: 기존 서비스의 중간 규모 API 기능

점수 예: 8점, STANDARD. /clarify로 API 동작과 오류 계약을 확정하고 OpenSpec식 SPEC을 작성한다. plan-lite에서 변경 파일·테스트 seam을 명시하고, TDD로 vertical slice를 구현한다. 새 컨텍스트 reviewer가 스펙 충족과 코드 품질을 분리 검토하며 통합 테스트 증거를 남긴다.

## 시나리오 C: 결제 웹훅과 데이터 마이그레이션

자동 STRICT 또는 CONTROLLED. payments/IAM/data 전문가를 선택 로드하고, threat model·idempotency·reconciliation·rollback·dry-run을 필수화한다. worktree/sandbox, 단계별 사람 승인, 독립 리뷰, 스테이징 리허설과 복구 쿼리가 없으면 ship하지 않는다.

## 시나리오 D: 사내 LLM으로 여러 주에 걸친 리팩터링

맥락 압력이 높아 최소 STRICT. GSD식 phase와 체크포인트를 사용하되 각 phase를 새 세션에서 실행한다. PLAN을 파일·모듈 경계로 나누고, STATE.json과 baseline commit을 매 단계 확인한다. 장문 대화는 유지하지 않고, HANDOFF와 원본 파일 링크를 이용해 재구성한다. 두 번 이상 제약을 놓치면 더 강한 모델 또는 사람 integrator로 승격한다.

# 12. 평가, 관측, 롤아웃

## 12.1 핵심 지표

| **지표** | **정의** | **좋은 방향** |
| --- | --- | --- |
| **완료 성공률** | 수용 기준을 모두 충족한 작업 비율 | 상승 |
| **회귀율** | 배포 후 되돌림·핫픽스·테스트 회귀 | 하락 |
| **맥락 회수율** | 새 세션이 목표·비목표·제약 ID를 정확히 복원한 비율 | 상승 |
| **제약 누락률** | 구현·리뷰에서 critical constraint가 빠진 비율 | 하락 |
| **인간 개입률** | 정상 흐름 중 사람이 방향을 재설정한 횟수 | 적정 수준까지 하락 |
| **증거 완전성** | 필수 검증 결과와 원본 경로가 존재하는 비율 | 상승 |
| **계획/코드 비율** | 워크플로 산출물 크기 대비 실제 변경량 | 소작업에서 과도하지 않게 |
| **시간·토큰 비용** | 레인별 평균 비용과 대기 시간 | 품질을 유지하며 하락 |
| **리뷰 유효 적중률** | 리뷰 finding 중 실제 수정 가치가 있었던 비율 | 상승 |
| **범위 이탈률** | 요청 외 파일·기능 변경 | 하락 |
| **handoff 재개 시간** | 새 세션이 유효 작업을 시작하기까지 걸린 시간 | 하락 |

## 12.2 내부 평가 세트

작은 기계적 변경: 절차가 과도해지지 않는지 평가.

모호한 기능: grill/clarify가 핵심 결정을 빠뜨리지 않는지 평가.

긴 문서의 숨겨진 제약: 맥락 회수율과 phase gate 평가.

교차 모듈 리팩터링: 계획·파일 경계·상태 인계 평가.

보안·결제 작업: fail-closed와 human gate 평가.

긴 실패 로그: 실제 root cause와 핵심 오류 식별 평가.

병렬 에이전트: 파일 ownership, 충돌, merge evidence 평가.

악성/모호한 외부 지시: 권한·프롬프트 인젝션 저항 평가.

## 12.3 롤아웃 단계

| **단계** | **운영 방식** | **승격 조건** |
| --- | --- | --- |
| **0. 설계·Replay** | 과거 작업 20~50개를 재생해 레인과 산출물 평가 | 기존 방식 대비 명백한 회귀가 없음 |
| **1. Shadow** | 워크플로가 제안·기록만 하고 개발자가 기존 방식으로 수행 | 위험 분류와 맥락 gate 정확도 확보 |
| **2. Optional** | 팀이 선택 사용; 실패와 수정 패턴 수집 | STANDARD에서 품질·비용 개선 |
| **3. Default** | 일반 작업의 기본값, opt-out 허용 | 회귀율·범위 이탈률 개선 |
| **4. Enforced** | 고위험 영역에서 강제, 예외는 승인·로그 | 권한·감사·rollback 검증 완료 |

## 12.4 포크와 업스트림 관리

외부 스킬을 그대로 vendor하지 말고 source repo, commit, license, local diff를 registry.lock에 기록한다.

행동 계약은 유지하고 프로젝트 경로·도구·권한·출력 스키마를 adapter로 분리한다.

업스트림 변경은 자동 반영하지 않고 eval suite를 통과한 후 승격한다.

로컬 수정이 원본의 약 20~30%를 넘거나 상태 모델이 충돌하면 독립 구현으로 전환을 검토한다.

모델·호스트별 포맷 생성은 하나의 중립 source에서 자동화하고 생성물 drift를 CI에서 검사한다.

# 13. 피해야 할 안티패턴

| **안티패턴** | **문제** | **대안** |
| --- | --- | --- |
| **프레임워크 스태킹** | GSD·Superpowers·OpenSpec·gstack를 모두 설치해 각자 계획·상태·리뷰를 소유하게 함 | 자체 상태 머신 하나를 두고 기능만 포팅 |
| **에이전트 카탈로그 전체 로드** | 수백 개 역할을 항상 검색·라우팅 대상으로 둠 | 프로젝트 allowlist와 온디맨드 설치 |
| **AGENTS.md 비대화** | 도메인·아키텍처·과거 결정·도구 설명을 한 파일에 모두 포함 | 정책만 최소 유지하고 CONTEXT-MAP으로 계층화 |
| **역할극 중심 에이전트** | 성격·말투는 길지만 입력·출력·도구·성공 조건이 없음 | 책임·권한·결과 스키마 중심 |
| **LLM 리뷰를 테스트로 간주** | 리뷰어가 “좋아 보인다”고 말하면 완료 | 결정론적 evidence gate |
| **항상 worktree·항상 TDD** | 변경 성격과 무관하게 모든 ceremony 강제 | 위험도와 병렬성에 따라 조건부 활성화 |
| **반복 요약 덮어쓰기** | 긴 대화를 계속 요약해 하나의 문서를 갱신 | append-only 결정과 원본 링크, 단계별 handoff |
| **구현자가 스펙 수정** | 구현 난이도 때문에 요구를 조용히 축소 | 요구 변경은 상태 전이·재승인 |
| **자동 최신 스킬 설치** | 외부 registry의 최신 버전을 즉시 사용 | 승인 버전·해시·eval gate |
| **비용만 최적화** | 저렴한 모델로 모든 설계·보안·리뷰 실행 | 업무 위험과 모델 신뢰도 기반 라우팅 |

# 14. 최종 권장 청사진

| **권장 V1** 자체 /intake 라우터와 상태 머신을 먼저 만든다. mattpocock/skills에서 clarify·domain-modeling·tdd·diagnose·review·handoff를 포팅하고, OpenSpec의 변경 단위 SPEC을 채택한다. GSD에서 STATE·checkpoint·phase 개념을 가져오며, gstack에서는 QA·ship 증거 흐름을 가져온다. 전문 역할은 wshobson/agents에서 allowlist 방식으로 선택한다. Spec Kit·BMAD·agency-agents는 정책·산출물·역할 아이디어의 참고 자료로 사용한다. |
| --- |

## 구현 우선순위

| **우선순위** | **구현 항목** | **완료 기준** |
| --- | --- | --- |
| **1** | TASK/STATE/EVIDENCE/HANDOFF 스키마와 phase state machine | 새 세션이 HANDOFF로 작업을 재개하고 상태가 기계 판독됨 |
| **2** | 위험도 라우터와 Fast/Standard/Strict/Controlled 정책 | 과거 작업 replay에서 사람 판단과 대체로 일치 |
| **3** | clarify → spec → implement → review → verify 코어 스킬 | 10~20개 golden task에서 추적성·성공률 기준 통과 |
| **4** | 맥락 health gate와 사내 모델 stress test | 제약 누락을 감지하고 refresh/escalate 가능 |
| **5** | 결정론적 tool/evidence layer | 테스트·diff·보안·배포 결과가 표준 JSON/Markdown으로 수집 |
| **6** | 전문 agent allowlist와 모델 라우팅 | 필요할 때만 로드되고 권한·비용·출력이 관측됨 |
| **7** | 사내 registry와 adapter 생성 | 버전 고정, 해시, 라이선스, 도구별 변환 CI |

## 최종 판단 기준

프로젝트가 성공했는지는 스킬 수나 자동 생성 PR 수가 아니라 다음 질문으로 판단해야 한다.

사내 LLM이 긴 대화 없이도 파일 기반 상태에서 정확히 작업을 재개하는가?

작은 작업은 빠르게 끝나고, 위험한 작업만 절차가 강해지는가?

모든 중요 결정이 스펙·티켓·코드·테스트·증거로 추적되는가?

에이전트가 틀렸을 때 어디서 맥락이 유실되었는지 재현할 수 있는가?

외부 스킬과 모델을 교체해도 프로젝트의 정책·상태·평가 자산이 남는가?

사람의 승인과 책임이 필요한 경계가 명확한가?

# 부록 A. 출처와 조사 기준

GitHub 레포는 공식 README와 공개 이슈를 중심으로 기능·장단점을 정리했다. 연구 문헌은 2025~2026년 공개 preprint를 포함하며, 일부는 동료평가 전이므로 방향성 근거로 사용하고 사내 결정에는 자체 평가를 병행해야 한다.

**[R1] mattpocock/skills. **공식 GitHub 저장소.  — 작고 수정 가능하고 조합 가능한 엔지니어링 스킬, grill-with-docs, TDD, review, handoff

**[R2] addyosmani/agent-skills. **공식 GitHub 저장소.  — 개발 생명주기 스킬, 평가·라우팅·agent-first 도구 논의

**[R3] wshobson/agents. **공식 GitHub 저장소.  — 플러그인·에이전트·스킬·오케스트레이터와 멀티호스트 지원

**[R4] msitarzewski/agency-agents. **공식 GitHub 저장소.  — 직무별 AI 에이전트 페르소나와 산출물 카탈로그

**[R5] Fission-AI/OpenSpec. **공식 GitHub 저장소.  — 변경 단위 spec-driven development

**[R6] Open GSD / GSD. **공식 GitHub 저장소.  — 로드맵, 상태, phase, checkpoint 기반 장기 워크플로

**[R7] garrytan/gstack. **공식 GitHub 저장소.  — 제품·엔지니어링·디자인·QA·보안·릴리스 스킬

**[R8] obra/superpowers. **공식 GitHub 저장소.  — TDD, worktree, 서브에이전트 구현·리뷰 규율

**[R9] github/spec-kit. **공식 GitHub 저장소.  — constitution→specify→plan→tasks→implement 구조

**[R10] bmad-code-org/BMAD-METHOD. **공식 GitHub 저장소.  — 역할 기반 전체 SDLC와 애자일 산출물

**[R11] vercel-labs/skills. **공식 GitHub 저장소.  — 스킬 설치·배포 생태계 참고

**[T1] From Registry to Repository: How AI Agent Skills Are Written, Adapted, and Maintained. **arXiv preprint (2026).  — 18,463 registry skills와 23,199 personal-use skills 분석; 재사용·수정 패턴

**[T2] Coding Agents are Effective Long-Context Processors. **arXiv preprint (2026).  — 파일 시스템·도구를 통한 장문 자료 처리의 효율

**[T3] Intelligence Degradation in Long-Context LLMs. **arXiv preprint (2026).  — 특정 오픈소스 모델에서 장문 임계점 이후 성능 저하; 모델별 검증 필요

**[T4] Classifier Context Rot: Monitor Performance Degrades with Context Length. **arXiv preprint (2026).  — 긴 에이전트 transcript에서 위험 행동 탐지 성능 저하와 주기적 reminder 효과

**[T5] Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models. **arXiv preprint (2025).  — 컨텍스트를 점진적으로 축적·성찰·정리하는 playbook 접근

# 부록 B. 프로젝트 설계 검토 체크리스트

☐ 오케스트레이터가 하나이며 상태 전이의 원본이 명확하다.

☐ Fast 레인이 있어 소작업이 문서 ceremony에 묶이지 않는다.

☐ 인증·결제·데이터·배포 작업은 자동 승격된다.

☐ AGENTS.md는 최소 규칙과 문서 맵만 포함한다.

☐ CONTEXT/GLOSSARY와 SPEC/PLAN의 책임이 분리되어 있다.

☐ 작업 상태는 대화가 아니라 STATE.json 등에 저장된다.

☐ 단계별 HANDOFF가 커밋 SHA, 파일 경로, 미결정을 포함한다.

☐ 사내 모델의 long-context stress test와 buried-constraint 테스트가 있다.

☐ 핵심 제약 누락 시 refresh·새 세션·모델 승격 규칙이 있다.

☐ 외부 스킬은 source commit, license, local diff, checksum이 기록된다.

☐ 전문 에이전트는 allowlist와 필요 시 로딩을 사용한다.

☐ 각 스킬은 trigger, anti-trigger, input, output, permission, stop 조건이 있다.

☐ LLM 리뷰와 결정론적 검증이 분리되어 있다.

☐ EVIDENCE에 실행 명령, 결과, 원본 artifact 경로가 남는다.

☐ 업스트림 업데이트는 자동 반영되지 않고 eval을 통과한다.

☐ 성공률뿐 아니라 맥락 회수율, 제약 누락률, 범위 이탈률을 측정한다.

— 문서 끝 —
