# 선행연구 조사: 에이전트 간 디지털 서명 기반 권한 승인

조사일: 2026-11-18 (지도교수 미팅 후속). 범위: arXiv 초록 페이지와 공개 문서.
**모든 항목은 초록 수준에서만 확인했다. 본문은 아직 읽지 않았다.** 수치는 초록에 적힌 값이다.

## 1. 결론 요약

- "에이전트 간 서명 위임"은 **이미 활발한 분야**다. 2025–2026년에 프로토콜·시스템 논문이 다수 나왔다.
  따라서 "서명으로 위임하자"는 제안만으로는 공백이 아니다.
- **자연어 전달 vs 서명 전달을 LLM으로 직접 비교한 실험도 이미 1편 있다**(Signed but Not Safe, 2026-11).
  다만 대상은 *요구사항 전달*이고, 승인·철회 같은 *권한 상태 결정*은 다루지 않는다(초록 기준).
- 이번 조사에서 **찾지 못한 것**(= 후보 공백, 본문 확인 필요):
  1. 확인되지 않은 **자연어 철회 주장**이 유효한 승인을 무력화하는 현상(잘못된 거부, 가용성 피해)의 측정.
  2. 검증 가능한 기록을 LLM이 **보고도** 자연어 주장을 따른다는 측정
     → 서명은 LLM이 참고하는 증거가 아니라 **코드가 강제**해야 한다는 근거.
  3. 승인·철회 서명 검사를 **어느 단계(계획/실행/검증)**에 둬야 하는지의 비교
     (우리 E3: 계획 단계가 검증기 전에 작업을 멈춤).

## 2. 가장 가까운 연구 (직접 비교 대상)

| 논문 | 무엇을 했나 | 우리와의 차이 |
|---|---|---|
| **Signed but Not Safe: Requirement Integrity in Multi-Agent LLM Handoffs** (Chen 외, arXiv:2611.07483, 2026-11-05, v2 11-17) | 자유 텍스트 / 구조화 JSON / 서명 manifest 전달 비교. Qwen3-8B, gpt-oss-20b, gemma-4-12b. 공격 시 unsafe commit 69.4%(구조화) → 9.0%(서명). 서명은 전송 중 변조는 막지만 **추출 단계 오류·조작은 못 막음**(신뢰 경계). 결정적 검증기 78.7% vs LLM 검사기 59.0% | 요구사항 보존 문제. 승인·철회·권한 주장은 초록에 없음. 소형 공개 모델만 |
| **Silence Is Endorsement: Verification-Status Laundering in LLM Agent Pipelines** (arXiv:2609.20211) | 핸드오프에서 "미확인" 표시가 사라지면 위험 승인 증가. 검증 상태를 구조화된 상태로 붙여 다닐 것을 권고 | 우리 선행연구(기록 없음 조건). 서명 실험 아님 |
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

## 4. 산업 쪽 (배경용, 핀테크·디지털 월렛)

- **Google AP2 (Agent Payments Protocol):** 사용자가 서명한 mandate(구매 내용·결제)를 검증 가능한 자격증명으로 전달.
  v0.2는 SD-JWT 기반이라는 출처와 W3C VC 기반이라는 출처가 갈림 → 명세(ap2-protocol.org) 직접 확인 필요.
- 결제 업계(Visa 등)의 에이전트 결제 권한·한도·승인 통제 보도.
- **삼성 월렛의 에이전트 서명:** 이번 검색으로는 공식 자료를 찾지 못함. 교수님께 출처를 여쭤볼 것.

## 5. 다음에 확인할 것

1. Signed but Not Safe 본문: 위협 5종 목록, 승인·철회 조건이 있는지.
2. ResidualAuth 본문: 에피소드에 자연어 철회 주장이 들어가는지.
3. Silence Is Endorsement 최신판: 서명 또는 구조화 상태 실험이 추가됐는지.
4. AP2 명세: 철회(revocation) 처리 방식.
5. 2026-11 이후 신규 논문 재검색(분야가 빠르게 움직임).

## 출처

- https://arxiv.org/abs/2611.07483
- https://arxiv.org/abs/2609.20211
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
