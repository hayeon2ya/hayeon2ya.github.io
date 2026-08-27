# Hayeon CV 웹페이지 관리 가이드

이 문서는 Windows에서 처음 시작하는 사람이 Codex를 열고, GitHub 계정을 연결하고, 이 웹페이지 repo를 받아서 수정하고, GitHub Pages에 반영하는 전체 흐름을 설명합니다.

현재 웹사이트 프로젝트는 이 repo 자체이고, GitHub Pages용 Jekyll 사이트입니다.

- GitHub repo: `https://github.com/hayeon2ya/hayeon2ya.github.io.git`
- 현재 branch: `master`
- 실제 공개 주소 후보: `https://hayeon2ya.github.io`
- `_config.yml`에 적힌 주소: `https://ihayeon2ya-code.github.io`

위 두 주소가 다르면 GitHub 계정명/repo 이름 기준으로 어떤 주소를 쓸지 먼저 확인해야 합니다. 보통 `계정명.github.io` repo는 `https://계정명.github.io`로 공개됩니다.

## 1. 처음 준비물

Windows PC에 아래 프로그램이 필요합니다.

1. GitHub 계정
2. Git for Windows
3. GitHub CLI, 명령어 이름은 `gh`
4. ChatGPT/Codex 또는 Codex가 연결된 작업 창
5. 선택 사항: VS Code

설치 확인은 Windows Terminal 또는 PowerShell에서 합니다.

```powershell
git --version
gh --version
```

둘 다 버전이 나오면 설치가 된 상태입니다.

설치가 안 되어 있으면:

- Git for Windows: https://git-scm.com/downloads/win
- GitHub CLI: https://cli.github.com/

GitHub CLI는 Windows에서 아래 명령으로 설치할 수도 있습니다.

```powershell
winget install --id GitHub.cli --source winget
```

설치 후에는 Windows Terminal을 완전히 닫았다가 다시 열어야 `gh` 명령이 잡히는 경우가 있습니다.

## 2. GitHub 계정 연결하기

Windows Terminal 또는 PowerShell에서 아래를 실행합니다.

```powershell
gh auth login
```

질문이 나오면 보통 아래처럼 선택하면 됩니다.

- `Where do you use GitHub?`: `GitHub.com`
- `What is your preferred protocol for Git operations?`: `HTTPS`
- `Authenticate Git with your GitHub credentials?`: `Yes`
- `How would you like to authenticate GitHub CLI?`: `Login with a web browser`

브라우저가 열리면 GitHub에 로그인하고 승인합니다.

완료 확인:

```powershell
gh auth status
```

정상이라면 로그인된 GitHub 계정명이 보입니다.

## 3. repo 받아오기

작업할 폴더로 이동합니다. 예를 들어 문서 폴더 아래에 `websites` 폴더를 만든다고 하면:

```powershell
cd Documents
mkdir websites
cd websites
```

repo를 복사합니다.

```powershell
git clone https://github.com/hayeon2ya/hayeon2ya.github.io.git
```

폴더로 들어갑니다.

```powershell
cd hayeon2ya.github.io
```

현재 branch를 확인합니다.

```powershell
git branch
```

이 사이트는 현재 `master` branch 기준으로 관리되고 있습니다.

## 4. Codex에서 폴더 열기

Codex 창에서 작업 폴더를 열 때는 방금 받은 repo 폴더를 선택합니다.

예:

```text
Documents/websites/hayeon2ya.github.io
```

Codex에게 작업을 시킬 때는 가능한 한 구체적으로 말하면 됩니다.

```text
_data/data.yml에서 About 문장을 조금 더 자연스럽게 다듬어줘. 수정 후 변경 파일과 확인 방법도 알려줘.
```

```text
publications에 새 논문 하나 추가해줘. 제목은 ..., 저널은 ..., 연도는 ..., 역할은 ...
```

```text
로컬에서 Jekyll 사이트 실행해서 깨지는 부분 있는지 확인해줘.
```

## 5. 자주 수정하는 파일

대부분의 내용 수정은 아래 파일에서 끝납니다.

### `_data/data.yml`

프로필, 연락처, 소개글, 학력, 수상, 대표 논문, 추천인 등을 수정합니다.

주요 위치:

- `sidebar`: 이름, 직함, 이메일, ORCID, Google Scholar, LinkedIn 등
- `career-profile`: About 문단
- `education`: 학력
- `experiences`: Awards and Honors
- `publications`: 홈페이지에 보여줄 대표 논문
- `recommendations`: Referees

YAML 파일이라 들여쓰기가 중요합니다. 기존 줄의 공백 구조를 최대한 유지하세요.

잘못된 예:

```yaml
education:
- degree: ...
```

권장 예:

```yaml
education:
  title: Education
  info:
  - degree: PhD Candidate ...
    university: Kyung Hee University
    time: Present
```

### `_data/publications.yml`

전체 publication 목록을 관리합니다.

현재 형식은 아래처럼 한 줄 배열입니다.

```yaml
- ["논문 제목", "저널명", 2026, "Corresponding", 55]
```

순서는:

1. 제목
2. 저널명
3. 연도
4. 역할
5. Impact factor

### `_config.yml`

사이트 제목, 공개 URL, 색상 테마 등을 관리합니다.

자주 바꾸는 항목:

```yaml
title: Hayeon Lee CV
url: 'https://hayeon2ya.github.io'
baseurl: ''
theme_skin: blue
```

색상은 아래 중 하나를 쓸 수 있습니다.

```text
blue, turquoise, green, berry, orange, ceramic, teal, oceanstale
```

## 6. 로컬에서 웹사이트 미리보기

이 사이트는 Jekyll 사이트입니다. Ruby와 Bundler가 필요합니다.

처음 한 번:

```powershell
bundle install
```

사이트 실행:

```powershell
bundle exec jekyll serve
```

브라우저에서 엽니다.

```text
http://localhost:4000
```

만약 Windows에서 Ruby/Jekyll 설치가 어렵다면 Codex에게 이렇게 요청해도 됩니다.

```text
이 repo를 로컬에서 실행하는 데 필요한 Ruby/Jekyll 환경을 확인하고, 가능한 방식으로 서버를 띄워줘.
```

## 7. 수정 후 GitHub에 올리는 방법

수정 상태 확인:

```powershell
git status
```

변경된 파일 확인:

```powershell
git diff
```

변경 파일 저장 준비:

```powershell
git add _data/data.yml
git add _data/publications.yml
git add _config.yml
```

전체 변경 파일을 한 번에 추가하려면:

```powershell
git add .
```

커밋 만들기:

```powershell
git commit -m "Update CV website"
```

GitHub에 올리기:

```powershell
git push
```

올린 뒤 GitHub Pages가 자동으로 다시 빌드됩니다. 보통 몇 초에서 몇 분 걸립니다.

## 8. GitHub Pages 설정 확인

GitHub 웹사이트에서 확인합니다.

1. repo 페이지로 이동: `https://github.com/hayeon2ya/hayeon2ya.github.io`
2. `Settings` 클릭
3. 왼쪽 메뉴에서 `Pages` 클릭
4. Source가 branch 배포로 되어 있으면:
   - Branch: `master`
   - Folder: `/root`

`hayeon2ya.github.io` 같은 사용자 사이트는 repo 이름이 GitHub 계정명과 정확히 맞아야 합니다.

예:

```text
GitHub 계정명: hayeon2ya
repo 이름: hayeon2ya.github.io
공개 주소: https://hayeon2ya.github.io
```

## 9. 기본 작업 루틴

평소에는 이 순서만 기억하면 됩니다.

```powershell
git pull
```

파일 수정

```powershell
bundle exec jekyll serve
```

브라우저에서 확인

```powershell
git status
git diff
git add .
git commit -m "Update CV content"
git push
```

## 10. Codex에게 맡기기 좋은 요청 예시

내용 추가:

```text
_data/publications.yml에 아래 논문을 추가해줘. 기존 형식과 정렬 기준을 유지해줘.
제목:
저널:
연도:
역할:
Impact factor:
```

문장 다듬기:

```text
_data/data.yml의 About 문단을 academic CV 톤으로 더 자연스럽게 다듬어줘. 의미는 바꾸지 말아줘.
```

오류 확인:

```text
Jekyll 빌드가 실패하는지 확인하고, 실패하면 원인 파일과 수정안을 알려줘.
```

배포:

```text
변경사항 확인하고 commit/push까지 해줘. 커밋 메시지는 "Update CV publications"로 해줘.
```

주의: Codex에게 push를 맡길 때는 반드시 변경 내용을 먼저 확인하는 습관을 가지세요.

## 11. 문제 해결

### `gh` 명령어를 찾을 수 없다고 나올 때

GitHub CLI가 설치되지 않았거나 PATH가 아직 갱신되지 않은 상태입니다.

1. GitHub CLI 설치
2. Windows Terminal 완전히 종료
3. 새 Windows Terminal 열기
4. `gh --version` 재확인

### `git push`에서 로그인하라고 나올 때

아래를 다시 실행합니다.

```powershell
gh auth login
gh auth status
```

### GitHub 비밀번호를 입력했는데 실패할 때

GitHub는 command line git 작업에서 일반 비밀번호 로그인을 쓰지 않습니다. GitHub CLI 로그인 또는 personal access token을 써야 합니다. 초심자에게는 `gh auth login` 브라우저 로그인이 가장 쉽습니다.

### 웹사이트가 바로 안 바뀔 때

GitHub Pages 반영에는 시간이 조금 걸립니다.

확인 순서:

1. `git push`가 성공했는지 확인
2. GitHub repo의 `Actions` 또는 `Settings > Pages` 확인
3. 1-5분 기다린 뒤 새로고침
4. 브라우저 캐시 문제면 강력 새로고침: `Ctrl + F5`

### 사이트 주소가 이상할 때

`_config.yml`의 `url`과 GitHub repo 이름을 확인합니다.

현재 repo remote는:

```text
https://github.com/hayeon2ya/hayeon2ya.github.io.git
```

따라서 일반적인 공개 주소는:

```text
https://hayeon2ya.github.io
```

그런데 `_config.yml`에는 현재 아래처럼 되어 있습니다.

```yaml
url: 'https://ihayeon2ya-code.github.io'
```

실제 GitHub 계정이 `hayeon2ya`라면 `_config.yml`의 `url`을 `https://hayeon2ya.github.io`로 바꾸는 것이 맞습니다.

## 12. 참고 링크

- OpenAI Codex 소개: https://learn.chatgpt.com/
- GitHub CLI 인증: https://cli.github.com/manual/gh_auth_login
- GitHub 인증 개요: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github
- GitHub Pages: https://pages.github.com/
- Jekyll GitHub Pages 설명: https://jekyllrb.com/docs/github-pages/
