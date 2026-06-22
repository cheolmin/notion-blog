---
layout: post
title: "Claude Code + LiteLLM Proxy (using github copilot api)"
date: 2026-06-20
tags: ["Claude Code", "Guide", "Tutorial"]
description: "Claude code 사용 시 liteLLM proxy를 활용하여 github copilot을 model provider로 사용하는 방법"
---

# Claude Code + LiteLLM Proxy (GitHub Copilot 백엔드)

Claude Code 를 **LiteLLM 프록시**에 연결하고, LiteLLM 이 **GitHub Copilot** 으로
요청을 중계하도록 만드는 설치 가이드입니다. 기존 `copilot-api` 방식을 대체합니다.

![]({{ '/assets/images/cc with github copilot/852d207ac112.png' | relative_url }})

- 대상 셸: **PowerShell 7** (`pwsh`). Windows PowerShell **5.1 은 건드리지 않습니다.**
  - PS7 프로파일: `…\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
  - PS5.1 프로파일: `…\Documents\WindowsPowerShell\…` ← 그대로 둠 (기존 copilot-api 유지)
- `ccc`, `ccc-opus`, `ccc-gpt`, `ccc-codex`, `ccc-gemini` … 명령은 그대로 사용합니다.

---

## 0. 사전 준비물 (이미 있으면 건너뛰기)

> 아래 모든 명령은 **PowerShell 7 창**에서 실행합니다.
(시작 메뉴 → "PowerShell 7" 또는 Windows Terminal 의 `pwsh` 탭)

---

## 1. LiteLLM 설치

```powershell
uv tool install "litellm[proxy]"
```

설치 확인:

```powershell
litellm --version
```

> `litellm.exe` 는 `%USERPROFILE%\.local\bin` 에 설치되며 이 경로는 보통 PATH 에 이미 포함됩니다.
`litellm : command not found` 가 나오면 PowerShell 7 을 새로 열고 다시 시도하세요.

---

## 2. LiteLLM config 배치

이 폴더의 `assets\config.yaml` 을 `%USERPROFILE%\.config\litellm\config.yaml` 로 복사합니다.
아래 블록을 **이 README 가 있는 폴더에서 연 PowerShell 7** 에 그대로 붙여넣으세요.

```powershell
# config + 토큰 폴더 생성
$dst = Join-Path $env:USERPROFILE ".config\litellm"
New-Item -ItemType Directory -Path $dst -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $dst "github_copilot") -Force | Out-Null

# assets\config.yaml -> ~/.config/litellm/config.yaml
Copy-Item ".\assets\config.yaml" (Join-Path $dst "config.yaml") -Force

# 확인
Get-Content (Join-Path $dst "config.yaml") -TotalCount 14
```

> `config.yaml` 의 모델 목록은 `ccc` 별칭과 1:1 로 맞춰져 있고, 맨 아래 `"*"` 와일드카드가
그 외 모든 Copilot 모델을 그대로 통과시킵니다. 모델명을 바꾸려면 이 파일만 수정하면 됩니다.

---

## 3. PowerShell 7 프로파일에 셸 추가

### 3-1. 프로파일 열기

```powershell
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
notepad $PROFILE
```

> **반드시 PowerShell 7 (****`pwsh`****) 안에서** 실행해야 PS7 프로파일이 열립니다.
Windows PowerShell 5.1 에서 열면 엉뚱한(5.1용) 프로파일이 열립니다.

### 3-2. starship 프롬프트 (선택) — 프로파일 **맨 위**에 붙여넣기

`assets\starship-init.ps1` 내용을 복사해 프로파일 **최상단**에 붙여넣습니다.
(starship 을 안 쓰면 이 단계는 건너뜁니다.)

### 3-3. LiteLLM 브리지 — 프로파일 **맨 아래**에 붙여넣기

`assets\litellm-bridge.ps1` **전체 내용**을 복사해 프로파일 **가장 아래**에 붙여넣고 저장합니다.

> 클립보드로 한 번에 복사하고 싶다면:

```powershell
Get-Content ".\assets\litellm-bridge.ps1" -Raw | Set-Clipboard
```

  그런 다음 메모장에서 `Ctrl+End` → `Ctrl+V` → 저장.

### 3-4. 프로파일 다시 로드

```powershell
. $PROFILE
```

오류 없이 로드되면 성공입니다. 확인:

```powershell
Show-CopilotModels
```

별칭 목록(`ccc -> claude-sonnet-4.6` 등)이 출력되면 셸이 정상 로드된 것입니다.

---

## 4. 최초 1회 GitHub Copilot 로그인

LiteLLM 의 GitHub Copilot 연동은 **최초 1회 device 로그인**이 필요합니다.
그냥 아무 `ccc` 명령이나 실행하면 자동으로 로그인 창이 뜹니다.

```powershell
ccc
```

그러면:

1. **새 PowerShell 7 창**이 (보이게) 뜨고, 그 안에 아래 같은 안내가 나옵니다:
```plain text
Please visit <https://github.com/login/device> and enter code XXXX-XXXX
```

2. 브라우저에서 `https://github.com/login/device` 열기 → **그 코드 입력** → GitHub 계정으로 승인.
3. 승인되면 LiteLLM 이 포트 4000 을 열고, 원래 창의 `ccc` 가 자동으로 Claude Code 를 띄웁니다.

> 로그인 토큰은 `%USERPROFILE%\.config\litellm\github_copilot\access-token` 에 저장됩니다.
**다음부터는 로그인 없이** `ccc` 한 번으로 프록시가 백그라운드(최소화)로 자동 기동됩니다.

---

## 5. 사용법

```powershell
ccc                      # 기본 모델 (claude-sonnet-4.6)
ccc-sonnet               # claude-sonnet-4.6
ccc-opus                 # claude-opus-4.8
ccc-opus-skip            # opus + --dangerously-skip-permissions
ccc-haiku                # claude-haiku-4.5
ccc-gpt                  # gpt-5.5
ccc-gpt-fast             # gpt-5.4-mini
ccc-mini                 # gpt-5-mini
ccc-codex                # gpt-5.3-codex
ccc-gpt-skip             # gpt + --dangerously-skip-permissions
ccc-gemini               # gemini-3.5-flash
ccc-gemini-pro           # gemini-3.1-pro-preview
ccc-model <모델명>       # config.yaml 의 임의 model_name 직접 지정
ccc-model gpt-4o "버그 고쳐줘"   # 모델 뒤에 인자/프롬프트 전달 가능
```

프록시 관리:

```powershell
Show-CopilotModels       # 별칭 ↔ 실제 모델 매핑 보기
Start-LiteLLM            # 프록시 수동 기동 (보통 ccc 가 알아서 함)
Stop-LiteLLM             # 프록시 종료
Set-CopilotModel <모델>  # ccc 의 기본 모델을 세션 동안 변경
```

---

## 6. 동작 원리 (요약)

- `ccc*` 명령 → `Invoke-ClaudeLiteLLM` → 포트 4000 확인.
  - 꺼져 있으면 `Start-LiteLLM` 으로 자동 기동:
    - **최초(미인증)**: 창을 **보이게** 띄워 device 코드를 노출, 최대 5분 대기.
    - **이후(인증됨)**: **최소화** 창으로 조용히 기동, 최대 60초 대기.
- Claude Code 에는 다음 환경변수가 (해당 명령 실행 동안만) 주입됩니다:
  - `ANTHROPIC_BASE_URL = http://localhost:4000`
  - `ANTHROPIC_AUTH_TOKEN = sk-litellm-local` ← `config.yaml` 의 `master_key` 와 동일해야 함
  - `ANTHROPIC_MODEL = <선택한 모델>`

---

## 7. 트러블슈팅

---

## 8. 첨부 파일

---


수정일 : 2026-06-20


