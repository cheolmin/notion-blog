---
layout: post
title: "Claude Code + Github Copilot Bridge (windows)"
date: 2026-06-01
tags: ["Tutorial", "Guide", "Claude Code"]
description: "Notion을 활용한 블로그 시스템 테스트를 위한 첫 번째 게시글입니다. 다양한 마크다운 요소를 포함하고 있습니다."
---

GitHub Copilot 구독을 백엔드로 사용해서 ****Claude Code*\*** CLI를 쓰는 Windows용 원클릭 설정입니다.

WSL 없이 **PowerShell 5.1 / 7 모두**에서 동작하며, 버전은 자동으로 감지합니다.

> 📖 원리: `copilot-api`라는 로컬 프록시를 띄워 Copilot을 Anthropic 호환 API처럼 보이게 한 뒤, 
Claude Code가 그 프록시(`http://127.0.0.1:4141`)를 바라보도록 환경변수를 설정합니다.

---

## **가장 빠른 시작 (3단계)**

1. **`1-INSTALL.bat`** 더블클릭 → 필요한 프로그램 설치 + 프로필 등록 (한 번만)
2. **`2-START-COPILOT.bat`** 더블클릭 → Copilot 프록시 켜기 (처음엔 GitHub 로그인)
3. 새 PowerShell 창에서 작업 폴더로 이동 후 **`ccc`** 입력

끝. 이후로는 `2`번(프록시) 켜고 `ccc`만 치면 됩니다.

---

## **폴더 구성**

```javascript
claude-copilot-setup/
├─ 1-INSTALL.bat          ← 설치 (더블클릭)
├─ 2-START-COPILOT.bat    ← 프록시 시작 (더블클릭)
├─ 3-RUN-CLAUDE.bat       ← Claude 실행 (더블클릭)
├─ install.ps1            ← 설치 본체 (버전 자동 감지)
├─ config.ps1             ← ★ 사용자 설정 (모델/포트 여기서 수정)
├─ lib/
│  └─ ccbridge.psm1       ← 핵심 모듈 (수정하지 마세요)
└─ docs/
├─ SETUP.md            ← 상세 설치 안내
└─ TROUBLESHOOTING.md  ← 문제 해결
```

---

## **명령어 요약**

---

## **설정 바꾸기**

`config.ps1` 파일만 메모장으로 열어 수정하고 **새 PowerShell 창**을 열면 적용됩니다.

모델명, 포트, 기본 provider, Ollama 모델 등을 모두 여기서 바꿉니다.

```powershell
$CC.Models["default"] = "claude-opus-4.7"   # ccc 기본 모델 변경
$CC.Port = 4141                             # 프록시 포트 변경
$CC.DefaultProvider = "copilot"             # copilot / direct / ollama
```

---

## **⚠️ 주의**

`copilot-api`는 GitHub Copilot을 **비공식(reverse-engineered)** 방식으로 사용합니다.

GitHub 약관 위반 소지가 있을 수 있으니 **회사 계정·업무용 코드**에서는 내부 정책을 먼저 확인하세요.

문제가 생기면 [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) 를 보세요.


---

## 상세 설치 안내 (SETUP)

Windows를 처음 세팅하는 분도 따라올 수 있도록 단계별로 설명합니다.

---

## 0. 준비물

- Windows 10/11
- 활성화된 **GitHub Copilot 구독** (개인/Business/Enterprise 중 하나)
- 인터넷 연결

PowerShell은 5.1(윈도우 기본) 또는 7 중 **무엇이든 됩니다.** 설치 스크립트가 자동 감지합니다.

---

## 1. 자동 설치 (권장)

1. 이 폴더(`claude-copilot-setup`)를 그대로 둡니다. (바탕 화면이면 됩니다)
2. **`1-INSTALL.bat`** 를 더블클릭합니다.
  - "Windows의 PC 보호" 경고가 뜨면 **추가 정보 → 실행**을 누릅니다.
3. 스크립트가 다음을 자동으로 처리합니다.
  - PowerShell 버전 감지 (5.1 / 7)
  - 실행 정책을 `RemoteSigned`(CurrentUser)로 완화
  - **Git**, **Node.js(LTS)** 설치 (winget 사용)
  - **Claude Code** 설치 (`irm https://claude.ai/install.ps1 | iex`)
  - **copilot-api** 전역 설치 (`npm install -g copilot-api`)
  - PowerShell 프로필(`$PROFILE`)에 브릿지 자동 등록

> **중요:** Node.js가 이번에 새로 설치됐다면, 그 창에서는 `node`가 아직 안 잡힐 수 있습니다.
그럴 땐 **새 PowerShell 창**을 열고 `1-INSTALL.bat`(또는 `install.ps1`)을 **한 번 더** 실행하세요.
같은 작업을 반복 실행해도 안전합니다(멱등).

---

## 2. 수동 설치 (winget이 없거나 자동이 막힐 때)

PowerShell 창에서 순서대로:

```powershell
# (1) 실행 정책
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
# (2) Git, Node.js
# - winget이 있으면
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
# - winget이 없으면 직접 다운로드:
#   Git  : https://git-scm.com/download/win
#   Node : https://nodejs.org  (LTS)
# (3) Claude Code
irm https://claude.ai/install.ps1 | iex
# (4) copilot-api
npm install -g copilot-api
# (5) 브릿지 등록 (이 폴더에서 실행)
.\install.ps1
```

---

## 3. 프록시 시작 + 첫 GitHub 로그인

1. **`2-START-COPILOT.bat`** 더블클릭 (또는 새 창에서 `Start-CopilotApi`)
2. 새 창에 **device code**(예: `ABCD-1234`)와 URL이 나옵니다.
3. 브라우저에서 그 URL(`https://github.com/login/device`)에 접속해 코드를 입력하고 승인합니다.
4. "Server running on [http://localhost:4141](http://localhost:4141/)" 비슷한 메시지가 보이면 성공입니다.

한 번 로그인하면 토큰이 저장되어 다음부터는 바로 켜집니다.

---

## 4. Claude Code 실행

**작업할 프로젝트 폴더**에서 실행해야 합니다.

```powershell
cd C:\Users\cheolminki\source\my-project
ccc
```

또는 모델을 골라서:

```powershell
ccc-opus       # 깊은 설계/리팩터링
ccc-codex      # 코드 특화
ccc-gpt        # GPT 최신
ccc-gemini     # Gemini
ccmodel gpt-5.4  # 임의 모델
```

`3-RUN-CLAUDE.bat`을 작업 폴더에 복사해 두고 더블클릭해도 됩니다.

---

## 5. 매일 쓰는 흐름

```javascript
1) 2-START-COPILOT.bat  (프록시 켜기 - 이미 켜져 있으면 생략)
2) PowerShell 에서 프로젝트 폴더로 cd
3) ccc
```

상태가 궁금하면 `ccs`, 명령이 기억 안 나면 `cchelp`.

---

## 6. 설정 커스터마이징

`config.ps1`을 메모장으로 열어 수정 → 새 PowerShell 창에서 적용.

- 기본 모델: `$CC.Models["default"]`
- 포트 변경: `$CC.Port`
- 기본 provider: `$CC.DefaultProvider` (`copilot` / `direct` / `ollama`)
- Anthropic 직접 호출 키: `$CC.AnthropicApiKey`
- Ollama 모델: `$CC.OllamaModel`

모델명을 바꿨는데 안 먹으면 `docs/TROUBLESHOOTING.md`의 "모델명 확인"을 보세요.


![]({{ '/assets/images/first-post/cce1686be5df.png' | relative_url }})

![]({{ '/assets/images/first-post/ebc2fd1715ea.png' | relative_url }})

