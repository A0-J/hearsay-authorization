# 선행연구 조사: 에이전트 간 디지털 서명 기반 권한 승인

조사일: 2026-11-18 (지도교수 미팅 후속). 범위: arXiv 초록 페이지와 공개 문서.
**모든 항목은 초록 수준에서만 확인했다. 본문은 아직 읽지 않았다.** 수치는 초록에 적힌 값이다.

## 1. 결론 요약

- "에이전트 간 서명 위임"은 **이미 활발한 분야**다. 2025–2026년에 프로토콜·시스템 논문이 다수 나왔다.
  따라서 "서명으로 위임하자"는 제안만으로는 공백이 아니다.
- **자연어 전달 vs 서명 전달을 LLM으로 직접 비교한 실험도 이미 1편 있다**(Signed but Not Safe, 2026-11).
  다만 대상은 *요구사항 전달*이고, 승인·철회 같은 *권한 상태 결정*은 다루지 않는다(초록 기준).
- 서명된 승인·철회, 실행 직전 재확인, 승인 1회 사용은 **IETF 초안 수준으로 이미 정의**되어 있다(§3a).
  PCM은 증명 없는 주장을 "unproven"으로 분류하는 프로토콜을 AP2 등 6개와 비교했다(§2). 둘 다 LLM 행동은 측정하지 않는다.
- **Safin 외(2609.17648)는 LLM 파이프라인에서 위조 승인 문구가 정상 업무 거부(FPR 49%)를 낳고, 서명 토큰·게이트는 이를 고치지 못하며,
  문구 제거(Observer)가 고친다는 것을 실험으로 보였다**(§2a). 우리 철회 주장 결과와 가장 가까운 선행 실험이다.
- 이번 조사에서 **찾지 못한 것**(= 후보 공백, 본문 확인 필요):
  1. 확인되지 않은 **자연어 철회 주장**이 유효한 승인을 무력화하는 현상(잘못된 거부, 가용성 피해)의 측정.
  2. 검증 가능한 기록을 LLM이 **보고도** 자연어 주장을 따른다는 측정
     → 서명은 LLM이 참고하는 증거가 아니라 **코드가 강제**해야 한다는 근거.
  3. 승인·철회 서명 검사를 **어느 단계(계획/실행/검증)**에 둬야 하는지의 비교
     (우리 E3: 계획 단계가 검증기 전에 작업을 멈춤).

### 연구 안에서의 역할 (2026-11-18 검토 의견 반영, 사용자가 바꿀 수 있음)

- **메인 선행연구: PCM**(§2). 서명된 증거와 proven / unproven / failed 판정. §13.6의 LLM 통합 조언은 시험되지 않음 → SIG P2.
- **보조: Safin 외**(§2a). 자연어 위조 승인 → Validator 오거부, 게이트로는 못 고치고 Observer로 줄어듦 → SIG S3.
- **주장 단위 상태 표시의 기존 측정: Silence Is Endorsement**(§2b). 메시지 안 표시, 승인 방향.
- **Tracekit**: 핵심 실험에 넣지 않음(시연 후보).

## 2. 가장 가까운 연구 (직접 비교 대상)

| 논문 | 무엇을 했나 | 우리와의 차이 |
|---|---|---|
| **Signed but Not Safe: Requirement Integrity in Multi-Agent LLM Handoffs** (Chen 외, arXiv:2611.07483, 2026-11-05, v2 11-17) | 자유 텍스트 / 구조화 JSON / 서명 manifest 전달 비교. Qwen3-8B, gpt-oss-20b, gemma-4-12b. 공격 시 unsafe commit 69.4%(구조화) → 9.0%(서명). 서명은 전송 중 변조는 막지만 **추출 단계 오류·조작은 못 막음**(신뢰 경계). 결정적 검증기 78.7% vs LLM 검사기 59.0% | 요구사항 보존 문제. 승인·철회·권한 주장은 초록에 없음. 소형 공개 모델만 |
| **PCM: A Proof-Carrying Message Protocol for Verifiable Multi-Agent Communication** (Ghosh, arXiv:2610.39109, 2026-10-29; **PDF 전문 확인 2026-11-18**) | 메시지의 각 주장에 증거(에이전트가 쓸 수 없는 append-only Merkle 로그 + 별도 서명자)를 첨부. "에이전트 자기 보고만 있는 주장은 절대 proven이 아님". 권한은 사람 승인에서 시작해 좁아지기만 하는 grant chain. 거짓 712개 중 10개 수용(전부 오래된 증거), 일반 A2A는 712개 전부, AP2 등 6개 프로토콜 모델은 504–712개 수용. 코드 공개(github.com/Cygnux-Labs/PCM-protocol) | **가장 강한 경쟁 연구.** 전문 확인: 권한 거짓 90개 모두 차단, 놓친 10개는 전부 오래된 증거(L10). 비교 대상 6개 프로토콜은 명세 기반 모델이지 SDK 실행이 아님(§12.1). **철회 기능 없음**(grant는 만료까지 유효, 최대 24시간, §7.5·Table 6 #17), 증거의 최신성 미보장(N2), A2A 게이트웨이는 PCM을 검증하지 않음(§11), replay 상태는 프로세스별. **벤치마크는 LLM을 호출하지 않음**(서명 서비스가 만든 메시지를 검증기로 판정). §13.6은 "주장마다 결과(proven / 보낸 쪽의 말)를 표시해 모델이 구조화된 출처로 추론하게 하라"고 제안하지만 시험하지 않음 → SIG 실험의 `signed_claim_unproven` 조건이 이를 시험. 코드: Tracekit 1.5.0(`pip install tracekit-ai==1.5.0`), github.com/Cygnux-Labs/PCM-protocol(MIT, bench/lies, verifier/python, 187 vectors) |
| **Auditable Authorization for LLM Agents: Empirical Evidence Across Model, Harness, and Workflow Layers** (Deng 외, arXiv:2611.19237, 2026-11-14) | 모델·하니스·워크플로 세 경계에서 "승인됐는데 실행 안 됨"과 "거부됐는데 실행됨"을 함께 측정. 모델 3종 패널: 승인 300건 중 7건 미완료, CrewAI 복원 시 672건 중 336건 누락, n8n 59개 중 4개가 Reject 후 실행 | 정상 업무 완료를 측정하는 것 자체는 새롭지 않음. 자연어 권한 주장·서명은 초록에 없음 |
| **Silence Is Endorsement: Verification-Status Laundering in LLM Agent Pipelines** (arXiv:2609.20211) | 핸드오프에서 "미확인" 표시가 사라지면 위험 승인 증가. 검증 상태를 구조화된 상태로 붙여 다닐 것을 권고(구현·검증은 안 함). 상세는 §2b | 우리 선행연구(기록 없음 조건). 서명 실험 아님 |
| **ResidualAuth** (Choi 외, arXiv:2609.08062, 2026-09) | 철회 가능한 위임에서 에이전트가 보존해야 할 권한 상태. 공개 모델 4종: 신뢰 가능한 Allow/Deny 결정 제공 시 15–16/16, 이벤트 발췌만 0–2/16 | 상태 기억 문제. 자연어 철회 주장은 초록에 없음 |
| **MasDrift** (Xu 외, arXiv:2608.07556, 2026-08) | 600개 업무, 중앙집중 계층에서 무단 행동 2.7–19.8%. 원 요청 재고정 방어 vs 정책 전파 방어 | 서명 없음(초록 기준). 권한 보존 벤치마크 |
| **Delegation Without Trust** (Dantuluri·Sundi, arXiv:2609.00267, 2026-08) | 위협 4종(confused deputy, 토큰 탈취·재사용, 프롬프트 주입 권한상승, 침해된 하위 에이전트). 모델 내부 권한 판단은 4종 모두 실패. 권한 브로커: 위조 토큰 0/200,000 수용 | 시스템 논문. 자연어 주장에 대한 LLM 반응 측정 아님 |

## 3. 서명·위임 프로토콜 / 시스템 (해결책 쪽 선행연구)

| 논문·표준 | 핵심 |
|---|---|
| South 외, *Authenticated Delegation and Authorized AI Agents* (arXiv:2501.09674; ICML 2025 position) | OAuth 2.0/OpenID Connect 확장, 서명된 위임 자격증명. 자연어 권한은 보안상 부족하다고 주장 |
| HDP (arXiv:2604.04522, 2026-04) | 사람 승인 → 에이전트 hop마다 Ed25519 서명 체인. IETF Internet-Draft. LLM 실험 없음 |
| AIP (arXiv:2603.24775, 2026-03) | MCP·A2A용 서명 capability 토큰(JWT/Biscuit). 공격 600건 전부 거부. MCP 서버 약 2,000개 중 인증 0 |
| LDP Provenance Paradox (arXiv:2603.18043) | 자기 보고 품질 vs 검증된 신원 라우팅. 자기 보고 기반이 무작위보다 나쁨 |
| Mandato (arXiv:2608.14074) | 서명된 mandate를 프록시가 강제 + 해시 체인 감사 로그. 평가는 계획 단계 |
| KITA (arXiv:2609.05901, NeurIPS WS 2026) | 임계 서명(threshold BLS). LLM은 키를 갖지 않고, 리뷰 정족수 서명 후에만 실행 |
| NCS, *From Neural Intent to Cryptographic Authorization* (arXiv:2607.15596) | 오프라인 서명·해시 체인 명령 스트림과 일치할 때만 실행. AgentDojo 등에서 공격 성공률 거의 0 |
| VERA (arXiv:2608.30091) | 위임 간선 단위의 **서명된 철회** 계약. LLM 반응 실험 없음 |
| Attesting Outputs and Delegation Ancestry (arXiv:2608.30387) | 출력 해시 서명 + 공동 서명 DAG로 위임 경로 증명 |
| AID-Guard (arXiv:2608.21159) | 실행 시점 재검증(stateful). 공격 44/44 차단 |
| SEAgent, *Taming Various Privilege Escalation* (arXiv:2601.11893) | 권한상승·confused deputy를 MAC(ABAC)로 차단. 서명 아님 |
| Consent Integrity (arXiv:2606.02668) | 사람 승인 화면을 에이전트 서술이 아닌 실제 행동에서 생성(WYSIWYS) |

## 2a. 서명 토큰 + LLM 파이프라인 실험 (2026-11-18 추가)

| 논문 | 무엇을 했나 | 우리와의 관계 |
|---|---|---|
| **Trust propagation and structural containment in Multi-agent LLM pipelines** (Safin, Zisad, Shatabda, Hasan, arXiv:2609.17648, 2026-09-15; **PDF 전문 확인**) | LangGraph 4-에이전트(Supervisor·Researcher·Validator·Executor), gemma4:31b-cloud(Ollama, temperature 0), Enron 메일 헤더를 실행 대상 데이터로, 60개 과제(정상 36·위험 24), seed 3개. 방어: **HMAC** 서명·과제 결합·1회용 토큰 + 독립 policy oracle. (1) 메모리 오염: 방어 없으면 UAR 100%, 방어 시 0%, Validator 침해율(JBR)은 100% 그대로. (2) 서명키를 가진 공격자: 토큰만 100%, oracle만 0% (seed 1개, n=60) → "서명은 출처를 보증할 뿐 권한을 보증하지 않음". (3) **검색 문서에 넣은 위조 승인**: UAR 0%이지만 Validator가 의심해 **정상 과제의 49.1–59.3%를 차단**; "구조적 권한 검증은 Validator 오거부를 해결하지 못함"(§V-A). (4) Observer(위조 승인 문구 제거)로 FPR 49.1%→7.4%. corpus policy는 정답 라벨 기반, 독립 정책도 같은 그룹이 작성. 코드 공개는 찾지 못함 | **우리 결과와 가장 직접적인 선행 실험.** 자연어 권한 주장이 정상 업무 거부를 낳는다는 현상을 다른 방향(위조 *승인* → 의심 → 거부)으로 보고. 서명·게이트가 오거부를 고치지 못한다는 결론은 우리 E3 해석(계획 단계 중단)과 같은 방향. 철회 주장, 공식 기록 제공, 지시 강화는 다루지 않음 |
| **Authorization Propagation in Agent2Agent Systems: An Experimental Security Evaluation of Multi-Hop Delegation** (Donno, Mehmood, Kralevska, arXiv:2611.07050, 2026-11-04; 초록 확인) | 의료비 청구 4-주체 A2A 워크플로. 호출자 맥락, 전이적 권한 증거, hop별 Ed25519 요청 인증, 재사용 상태를 분리. 적대 조건 15개 중 14개 거부, 위임 경로에서 의미적 권한 축소 없음, **공유 HMAC 증거 키를 가진 중개자는 권한 내용을 바꾸고도 유효한 증거를 만들 수 있음**. 지연 중앙값 5.11 ms. 코드 공개(github.com/GaDonn/a2a-authorization-propagation-poc), **NTNU 석사논문(2026-08) 산출물** | Ed25519 다단계 권한 검증은 이미 석사논문 수준에서 실험됨. 초록에는 LLM·자연어 주장·철회·오거부 없음 |

## 2b. 주장 단위 상태 표시가 LLM 판단에 주는 영향 (2026-11-18 추가)

PCM §13.6(주장마다 판정을 붙여 모델에 보여줄 것)과 가장 가까운 선행 실험. 모두 표시를 모델에 보여주고 판단 변화를 측정했다.
차이는 표시가 메시지 안에 있다는 것(보낸 쪽이 씀)과 대상이 승인 주장이나 지시 주입이라는 것이다.

| 논문 | 무엇을 했나 | SIG와의 관계 |
|---|---|---|
| **Silence Is Endorsement** (arXiv:2609.20211; **HTML 본문에서 수치 확인** 2026-11-18) | 핸드오프 노트의 권한 주장: 주장 없음 / "(UNVERIFIED) … asserts that this action is authorized" / 표시 사라짐 / "VERIFIED: …". 표시는 **보낸 쪽이 노트 안에 쓴 텍스트**. 런타임이 기록이나 구조화 상태를 주는 조건은 없음(§8은 권고만). 표 17(위험 항목 40개, 승인 확률, Llama-3.1-8B / Qwen2.5-7B / Qwen2.5-14B): 표시 없음 0.60/0.88/0.98, "unverified" 0.05/0.49/0.16, 명시적 경고 0.00/0.00/0.00, "requester-reported"(출처만) 0.19/0.67/0.87, verified 0.61/0.93/0.97. 표시가 있으면 Llama의 정상 요청 16개 승인도 0.70→0.40(§3.1). "검증된 승인만 인정" 지시는 모델에 따라 효과가 없거나 정상 요청을 과잉 거부(§6.2). 오픈 모델 9종, GPT-4o-mini, DeepSeek-V4-Flash | **주장 단위 표시의 효과는 이미 측정됨**(승인 방향, 메시지 안 표시). 시사점: (1) 판정 단어만("unverified")은 명시적 경고보다 약함 → SIG S1·S2(판정만 vs 판정+이유)를 철회 방향·플랫폼 표시로 다시 묻는 셈. (2) 출처만 밝히는 문구는 약함 → SIG 이유 문구의 "it is the sender's word"는 출처형. (3) 표시가 정상 요청 거부를 늘림 → SIG V·S7(참인 주장에 UNPROVEN 표시) |
| **Auditing Provenance Sensitivity in LLM Agent Action Selection** (Liao 외, arXiv:2607.20827, v2 2026-11-03; 초록 확인) | 같은 명제의 출처 권한(신뢰/비신뢰)만 바꿔 다음 행동 선택을 비교. 오픈 모델 여러 계열, 과제 450개. 출처만 바꿨을 때 행동이 달라진 비율: 경쟁 사례 5.4%, 지지 사례 1.7% | 출처 표시 민감도 측정. 승인·철회 상태나 서명 검증 결과는 초록에 없음 |
| **Spotlighting** (Hines 외, arXiv:2403.14720, 2024) | 신뢰하지 않는 입력에 구분자·datamarking·인코딩으로 출처 신호를 줌. GPT 계열에서 간접 주입 성공률 50% 초과 → 2% 미만 | "어느 텍스트를 믿지 말지 모델에 표시"의 고전적 선행. 대상은 지시 주입이고 권한 상태 판단이 아님 |
| **Signed-Prompt** (Suo, arXiv:2401.07612, 2024; 초록·2차 요약만) | 승인된 지시의 민감 키워드를 특수 문자열로 바꾸고 LLM이 표시된 지시에만 반응하게 함(프롬프트 설계, 파인튜닝) | 이름은 "서명"이지만 암호 서명이 아님(2차 요약 기준). 권한 상태 판단 아님 |

**정리:** "주장에 검증 상태를 표시하면 LLM 판단이 바뀐다"는 것 자체는 SIE가 보였다(승인 주장, 메시지 안 표시, 소형 오픈 모델 중심).
이번 검색(2026-11-18, 검색어 4개)에서 찾지 못한 것: (1) **플랫폼이 증거 블록에 넣는** 주장 판정(PCM §13.6 방식),
(2) 그 판정을 **서명·검증된 공식 상태와 함께** 보여주는 조건, (3) **철회 주장**(유효한 승인을 무력화하는 방향)과 참인 주장에 대한 오판.
SIG는 이 세 가지를 시험한다. 검색 4개가 이 분야 전체를 덮는다고 할 수는 없다.

## 3a. IETF 초안 (사용자 제공 PDF 전문 확인, 2026-11-18)

IETF에서 AUDIT(Agent Use of Delegation and Interaction Traceability) 워킹그룹 결성이 논의 중이다(IETF 127 BoF 요청, 2026-10-08, Izmaylov 초안 §13 기준).
아래 두 편은 전문을 읽었고, 그 아래 목록은 두 초안이 인용한 것으로 직접 읽지 않았다.

| 초안 | 핵심 | 우리와의 관계 |
|---|---|---|
| **draft-izmaylov-agent-permission-receipts-02** (2026-10-31, Standards Track 제안) | 사용자가 **패스키로 서명한 permission**(허용 행동, 상대방, 유효기간, 금액·횟수·기간 한도, 상대방 연서명·건별 승인 조건). 에이전트가 행동마다 Ed25519+ML-DSA-87로 서명한 receipt를 체인으로 남기고, 사용자 서명 **cancellation(철회)**과 에이전트의 **acknowledgement**를 정의. 검증기가 사후에 오프라인으로 "각 행동이 permission 안에 있었나"를 판정. 집행이 아닌 증거(§1, §18) | 서명된 승인·철회 상태 자체는 여기서 정의됨. 서명 없는 자연어 철회 주장, LLM 행동, 계획 단계 중단은 다루지 않음. §13에 AP2 mandate와의 비교 있음 |
| **draft-gruszka-audit-decision-receipts-10** (2026-11-17, Informational) | 승인(ALLOW)·거부(DENY/REFUSE)·실행 결과를 **서명된 decision receipt / outcome receipt**로 기록, 오프라인 검증 절차와 615개 테스트 벡터. **승인은 최대 1회 사용**(§4). §2.5: 서버가 서명한 승인 기록은 승인자가 실제로 승인했음을 보여주지 않음, 사람 본인 키 서명이 필요. §2.6: 평가 결과(증거)는 권한이 아님 | 결정 기록과 1회 사용 규칙은 여기서 정의됨. "receipt는 아무것도 집행하지 않는다"(§4). LLM 행동은 다루지 않음 |

| **draft-kroehl-agentic-trust-aae-01** (2026-08-11, Independent Submission, Informational) | Agent Authorization Envelope: W3C VC를 Ed25519 JWS로 서명. MANDATE(허용 행동·목적·주체), CONSTRAINTS(건당 금액 상한·도메인·속도 제한, 모르는 필수 제약은 거부), VALIDITY(기간, **revocation_check: 조회 실패 시 거부(fail-closed)**, single_use). 위임 체인은 좁아지기만 함, nonce 기반 소지 증명. 운영 중 배포(MolTrust, 2026-03~)에서 유래 | 서명된 위임장 형식과 철회 조회 실패 시 처리 규칙이 정의됨. 결정 기록(decision receipt)이나 LLM 행동은 없음 |

두 초안이 인용한 관련 초안(직접 읽지 않음): draft-nelson-agent-delegation-receipts(사용자 서명 위임, 좁아지기만 하는 위임, 철회),
draft-schrock-ep-authorization-receipts(실행 전 승인자 서명, 1회 사용),
draft-schrock-ep-bounded-capability-receipts(예산 한도, 실행 직전 철회 재확인),
draft-gilda-audit-agent-audit-record, draft-sharif-agent-audit-trail, draft-kuehlewind-audit-architecture.

**정리:** "승인·철회를 서명으로 하고, 실행 직전 다시 확인하고, 승인은 1회만 쓴다"는 메커니즘은 표준 초안 수준에서 이미 있다.
확인한 범위에서 이들 중 **LLM이 서명 없는 자연어 권한 주장에 어떻게 반응하는지 측정한 것은 없다.**

## 4. 산업 쪽 (배경용, 핀테크·디지털 월렛)

- **Google AP2 (Agent Payments Protocol):** 사용자가 서명한 mandate(구매 내용·결제)를 검증 가능한 자격증명으로 전달.
  v0.2는 SD-JWT 기반이라는 출처와 W3C VC 기반이라는 출처가 갈림 → 명세(ap2-protocol.org) 직접 확인 필요.
- 결제 업계(Visa 등)의 에이전트 결제 권한·한도·승인 통제 보도.

## 5. 다음에 확인할 것

1. Signed but Not Safe 본문: 위협 5종 목록, 승인·철회 조건이 있는지.
2. ResidualAuth 본문: 에피소드에 자연어 철회 주장이 들어가는지.
3. ~~Silence Is Endorsement 최신판~~ 확인함(2026-11-18): 런타임이 주는 구조화 상태 조건은 없음. 부록 J는 노트 안 구조화 필드가 요약 뒤 살아남는 비율만 봄(§2b).
4. AP2 명세: 철회(revocation) 처리 방식.
5. 2026-11 이후 신규 논문 재검색(분야가 빠르게 움직임).
6. 플랫폼이 붙인 주장 판정(proven/unproven 등)을 LLM에 준 실험: 이번 검색에서 찾지 못함. 제출 전 다시 검색.

## 출처

- https://arxiv.org/abs/2611.07483
- https://arxiv.org/abs/2609.17648
- https://arxiv.org/abs/2611.07050 · https://github.com/GaDonn/a2a-authorization-propagation-poc
- https://datatracker.ietf.org/doc/html/draft-kroehl-agentic-trust-aae-01
- https://arxiv.org/abs/2610.39109
- https://arxiv.org/abs/2611.19237
- https://arxiv.org/abs/2609.20211 · https://arxiv.org/html/2609.20211
- https://arxiv.org/abs/2607.20827
- https://arxiv.org/abs/2403.14720
- https://arxiv.org/abs/2401.07612
- https://arxiv.org/abs/2609.08062
- https://arxiv.org/abs/2608.07556
- https://arxiv.org/abs/2609.00267
- https://arxiv.org/abs/2501.09674 · https://proceedings.mlr.press/v267/south25a.html
- https://arxiv.org/abs/2604.04522
- https://arxiv.org/abs/2603.24775
- https://arxiv.org/abs/2603.18043
- https://arxiv.org/abs/2608.14074
- https://arxiv.org/abs/2609.05901
- https://arxiv.org/abs/2607.15596
- https://arxiv.org/abs/2608.30091
- https://arxiv.org/abs/2608.30387
- https://arxiv.org/abs/2608.21159
- https://arxiv.org/abs/2601.11893
- https://arxiv.org/abs/2606.02668
- AP2: https://docs.affinidi.com/products/affinidi-trust-fabric/agent-gateway/concepts/protocols/ap2/ , https://blockeden.xyz/blog/2025/09/22/google-ap2/
- 결제 업계: https://www.pymnts.com/digital-payments/2026/wallets-move-from-tap-to-pay-to-permission-to-spend/
