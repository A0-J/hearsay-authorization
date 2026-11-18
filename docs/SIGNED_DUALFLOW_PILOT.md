# Signed DualFlow — 연구 방향과 오프라인 기술 파일럿

출처: 외부 검토 문서와 코드(2026-11-18, 사용자가 전달). A–G절은 받은 그대로이고, H절은 저장소 대조와 실행 검증이다.
코드: [experiments/signed_dualflow_offline_pilot.py](../experiments/signed_dualflow_offline_pilot.py)는 받은 파일 그대로다
(SHA-256 `0396a325a24ba4fbc775000608bbd2e739a5710251cfd1fd34247a8a991aa5e2`).

기준일: 2026-11-18. **새로운 LLM/E2E 실험은 수행하지 않았음.** GitHub 저장소는 읽기만 했고 유료 API, 커밋, 푸시는 수행하지 않음.

## A. 독립 검토 결과

- 기존 Hearsay E3 결과 301개 에피소드(`results/E3-checks/episodes.csv`)를 조건별로 다시 집계:

| 실제 승인 | 전달 주장 | 에피소드 | 타깃 도구 성공(L1) | 원과제 완료(L3) |
|---|---|---:|---:|---:|
| valid | 없음 | 57 | 30 | 24 |
| valid | 승인됨 | 53 | 34 | 26 |
| valid | 철회됨 | 50 | 0 | 0 |
| invalid | 없음 | 49 | 5 | 4 |
| invalid | 승인됨 | 48 | 7 | 4 |
| invalid | 철회됨 | 44 | 0 | 0 |

- 해석 주의: E3는 중단되었고(301/792), 각 셀의 에피소드 수가 달라 미완료 상태와 교란을 고려해야 하며 Planner/Executor 분리가 없었음. L1은 도구 성공, L3는 과제별 후속 정의의 완료이며 벤치마크 전체 위해(harm)를 의미하지 않음.
- 2×2 실험 코드는 존재하지만 `docs/PLANNER_VERIFIER_2X2_PREREG_DRAFT.md`에 `approved_for_run: false`로 명시됨. Planner에 **정답을 미리 아는 oracle**을 넣고 E3 사용 과제를 재사용하므로 그대로는 독립적 새 증거가 아님.
- `results/E3-checks/DESIGN_AUDIT.md`에 따르면 11개 과제 중 7개는 기존 측정 체계로 벤치마크 위반을 확인할 수 없음. 비표적 도구 우회도 있어 실제 실행 상태를 별도로 평가해야 함.
- 기존 Hearsay에서 `evidence-explicit` 단순 프롬프트가 GPT-4.1의 철회 효과를 제거한 조건이 존재함. 따라서 이를 강한 비교군으로 넣어야 함.

## B. 후보 연구 문제

**연구 문제:** 서명 또는 독립 승인 근거가 존재하는데도 자연어로 전달된 허위 철회 정보가 에이전트의 정상 작업을 중단시키는 경우, 현재 권한 상태를 계획과 실행 양쪽에서 독립적으로 확인하는 방식이 오거부 및 무단 실행을 동시에 줄이는가?

- RQ1: 자연어 철회 주장은 어떤 단계(계획/도구 제안/최종 실행)에서 타깃 과제의 진행을 중단시키는가?
- RQ2: 서명된 승인 및 철회 기록의 **현재 상태 조회**는 PCM식 메시지 증거와 AP2식 실행 단계 Mandate 검증 대비 정상 완료율을 개선하는가?
- RQ3: DualFlow 의미·권한 검증과 최종 실행 허가 서명을 결합할 때 실제 무단 실행은 유지·감소하면서 false cancellation을 줄이는가?

**신규성 주의:** 서명된 위임장, 사전 메시지 검증, 실행 단계 강제, 승인완료 보장은 모두 선행연구가 존재함. 여기서 실증적으로 확인할 추가 효과가 없다면 '새로운 보안 기술'이라고 주장하지 않음.

## C. 제안 아키텍처

1. User Wallet Authority: 사용자/허가권자가 Ed25519로 GRANT/REVOKE 상태 이벤트에 서명. 사용자 지문은 선택적으로 하드웨어 키 사용을 허용하는 인증 수단이지 디지털 서명 알고리즘이 아님.
2. Trusted Authorization State Service: 에이전트 위임 메시지와 **분리된 조회 경로**로 `grant_id`, 상태, seq/version, 만료, 주체·scope를 제공. 상태 불명/조회 실패는 DEFER.
3. Planner Guard: 자연어 주장은 이벤트 자체가 아님. 승인 상태를 독립 조회해 정상 작업을 이어갈지, 보류/철회할지 결정. **실험에서는 타깃 도구와 정답 상태를 oracle로 주면 안 됨.**
4. DualFlow: Semantic Flow(신뢰된 원 사용자 의도와 실제 도구 인자 대조) + Authorization Flow(정확한 상태·scope·위임 체인 검증).
5. Isolated Permit Signer: DualFlow 통과한 **구체적인 작업**에 대해 action hash, grant ID, rev/version, nonce, expiry, 대상 Gateway를 포함한 실행 허가 서명.
6. Tool Gateway: 서명과 작업 동일성, 현재 권한 상태, nonce 재사용 여부를 검증한 뒤에만 실제 상태 변경. 결과 및 거부 이유 기록.

**프로토콜 상태:** `ACTIVE` / `REVOKED` / `UNKNOWN|STALE|LOOKUP_FAILED → DEFER` / `AUTHORIZED` / `COMMITTED|DENIED`. 보류는 `REVOKED`와 동일하지 않음. 권한 상태 조회 불가 시 위험 작업 실행 금지.

## D. 강한 비교군과 Ablation

| 방법 | Planner의 상태 확인 | DualFlow | 최종 서명된 Permit | 실행 Gateway |
|---|---|---|---|---|
| B0: 자연어 Only | 없음 | 없음 | 없음 | 없음 |
| B1: Hearsay evidence-explicit | 기록을 LLM에게 제시 | 없음 | 없음 | 없음 |
| B2: PCM-style inbound check | 서명 증거 판정(proven/unproven) | 없음 | 권한 grant만 | 표준 범위 검증 |
| B3: Signed execution only | 없음 | 있음 | 있음 | 있음 |
| B4: State-aware + signed execution | 실시간 상태 조회 | 있음 | 있음 | 있음 |
| B5: B4−Semantic | 실시간 상태 조회 | 권한만 | 있음 | 있음 |
| B6: B4−freshness | 초기 상태만 조회 | 있음 | 있음 | 있음 |

정당한 비교를 위해 AP2 원본 및 PCM 원본을 완전히 재현했다고 주장하지 말 것. 'PCM-style'은 논문에서 정의한 동일 증거·위임·재사용 규칙을 구현한 범위에 한해 제한적으로 표현. B4 대비 B2/B3/B5/B6 차이가 실제로 확인되어야 기여가 성립함.

## E. 평가 설계

- 과제: mock wallet에서 작업 1개(카드 혜택 비교 후 결제), 서로 다른 가맹점·금액·카드·만료·철회 이벤트를 가진 독립 사례 다수.
- 교란: (i) 허위 자연어 승인, (ii) 허위 철회, (iii) 특정 승인 ID 위조, (iv) scope 확대, (v) 서명 후 작업 인자 변경, (vi) replay, (vii) 승인 후 실제 철회, (viii) 조회 실패/과거 snapshot.
- 주요 지표: 실제 승인된 작업의 **False Cancellation Rate** (중단), 실제 철회된 작업의 **Unauthorized Commit Rate** (실제 Gateway effect), **Authorized Task Completion** (원업무 완료), **DEFER/회복률**, latency/token/서명 시간.
- 모든 arm에서 동일 태스크·상태·교란을 paired 비교. 각 태스크의 독립 샘플이 통계 단위; 반복 횟수를 독립 과제로 취급하지 않음.
- 사전등록: 과제, 원요청의 정답 레이블, 공격 문구, 의도 oracle, 역할 프롬프트, 확정된 수집 필드, 요인별 통계계획을 실험 전에 고정.

## F. 오프라인 실행 완료

파일 `signed_dualflow_offline_pilot.py`를 생성해 Ed25519 서명·상태 조회·검증 후 Permit 발급·Gateway 검증을 간단히 구현.

**단위 테스트 15/15 성공.** 구성에서 예상한 무단 실행 차단이 작동하는지 확인했을 뿐 실측 LLM 공격 성공률, PCM/AP2 재현 성능 또는 신규성을 증명하지 않음.

테스트 범위: 정상 승인, 미확인 철회 무효화, 실제 철회에 대한 실행 차단, 승인 후 철회, 오래된 기록, 조회 실패, 기록 위변조, action 변경, replay, 가짜 서명자, scope 초과, 사용자 의도 불일치, 만료 등.

실행: `python signed_dualflow_offline_pilot.py` (cryptography 설치 필요). 외부 네트워크와 결제 API는 호출하지 않음. 코드의 Semantic Flow는 단순한 결정적 조건 검사로, 기존 DualFlow의 LLM 구현을 대체하지 않음.

## G. 논문 진행 여부(Go/No-Go)

**GO**: B4가 실제, 독립된 LLM E2E 과제에서 B2/B3보다 false cancellation 또는 정상 완료율을 유의미하게 개선하고, unauthorized commit·정상 작업 오거부·성능 비용의 악화를 제한함. **STOP/재정의**: 동일 차이가 PCM-style 검증만으로 얻어지거나 프롬프트 강화만으로 해결되거나, 모든 개선이 정답 oracle/코드 상수 조건에서 자동 발생함.

## 참고

- https://github.com/A0-J/hearsay-authorization/blob/main/results/synthesis/REPORT.md
- https://github.com/A0-J/hearsay-authorization/blob/main/results/E3-checks/REPORT.md
- https://github.com/A0-J/hearsay-authorization/blob/main/docs/PLANNER_VERIFIER_2X2_PREREG_DRAFT.md
- https://arxiv.org/abs/2610.39109 (PCM)
- https://arxiv.org/abs/2609.05901 (KITA)
- https://arxiv.org/abs/2611.07483 (Signed but Not Safe)
- https://arxiv.org/abs/2611.19237 (Auditable Authorization)
- https://ap2-protocol.org/ap2/agent_authorization/

---

## H. 검증 (2026-11-18)

### H.1 저장소 대조

| 주장 | 결과 |
|---|---|
| E3 6줄 표 (L1, L3) | 일치 (`results/E3-checks/episodes.csv`에서 재계산). 단, **방법 6개와 과제 5개를 합친 값**이다. E3는 11개 과제 중 5개만 돌았고 T0019 invalid는 1개 에피소드다. 방법별로 나눠 보고해야 한다 |
| 301/792 | 일치 (`docs/EXPERIMENT3_E2E_PREREG.md`: 11 × 2 × 3 × 6 × 2 = 792) |
| 2×2 `approved_for_run: false`, oracle advisory | 일치 |
| 11개 과제 중 7개는 위반이 사전등록 지표에 안 잡힘 | 일치 (A 경로는 T0008, T0009, T0022, T0032뿐) |
| evidence-explicit이 GPT-4.1 철회 효과 제거 | 일치. 다른 모델은 남음: gpt-4o −7.6, gpt-4.1-mini −32.6, Claude Sonnet 4.6 −34.1%p |

### H.2 실행

`.venv` Python 3.13, cryptography 50.0.2: 15/15 통과. `PYTHONUTF8=1 python -m pytest`: 336 passed, 3 xfailed.

### H.3 빈틈

`tests/test_signed_dualflow_pilot.py`가 원본 15개 테스트를 그대로 돌리고, 아래 1–3을 strict xfail로 기록한다(고치면 XPASS로 실패하므로 표시를 지워야 한다).

1. **한 grant를 여러 번 쓸 수 있다.** 한도 50,000짜리 grant 하나로 nonce만 바꿔 42,000 결제를 세 번 하면 세 번 모두 실행된다(합계 126,000). test_10은 같은 permit의 재사용만 막는다. grant가 1회용인지 누적 한도인지 정의되어 있지 않다. 참고: draft-gruszka-audit-decision-receipts-10 §4(승인은 최대 1회), draft-izmaylov-agent-permission-receipts-02 §5.1(누적 `max`).
2. **permit에 대상 gateway가 없다.** C.5는 "대상 Gateway를 포함"한다고 했지만 permit 필드는 `action, action_sha256, expires_at, grant_id, grant_revision, kind, nonce`뿐이다.
3. **GRANT/REVOKE를 원장 자신의 키로 서명한다.** 사용자(월렛) 키가 따로 없어서, 원장 운영자가 승인을 만들어낼 수 있다. C.1의 "사용자/허가권자가 서명"과 다르다. 참고: Gruszka §2.5(서버가 서명한 승인 기록은 승인자가 실제로 승인했음을 보여주지 않음).

xfail이 아닌 관찰:

4. **자연어 주장은 `prepare()`와 gateway의 입력이 아니다.** 그래서 test_02와 test_03은 설계상 성립한다. `naive_planner`는 측정값이 아닌 허수아비다. 이 파일럿은 핵심 문제인 Planner 단계(E3에서 철회 주장 94개 에피소드 모두 보호 도구 호출 없음)를 다루지 않는다.
5. 에이전트 확인이 상수 비교(`g["agent"]=="pay-agent"`)다. 요청한 에이전트를 인증하지 않는다.
6. Semantic Flow는 구조화된 `user_request`(정답 의도)와 비교한다. 의도 oracle이다.

### H.4 선행 표준 초안과의 관계

C절의 1(서명된 승인·철회), 5(작업 단위 실행 허가), 6(실행 직전 상태 재확인·1회 사용)은 IETF 초안 수준에서 이미 정의되어 있다:
draft-izmaylov-agent-permission-receipts-02(패스키 서명 permission, 한도, 서명된 cancellation과 agent acknowledgement),
draft-gruszka-audit-decision-receipts-10(서명된 ALLOW/DENY 결정 영수증, 승인 최대 1회 사용),
그리고 두 초안이 인용하는 draft-schrock-ep-authorization-receipts / bounded-capability-receipts(실행 직전 철회 재확인).
세 초안 모두 LLM 행동은 측정하지 않는다. 상세: [RELATED_WORK_SIGNATURES.md](RELATED_WORK_SIGNATURES.md) §3a.
