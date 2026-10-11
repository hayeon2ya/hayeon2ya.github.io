# 홈페이지 관리

홈페이지 구조와 빌드·배포 방법은 [README.md](README.md)를 참고하세요.

- 자기소개: `index.md`
- 이름·프로필·SNS: `_config.yml`
- 학력·경력·수상: `_data/education.yml`, `_data/experience.yml`, `_data/honors.yml`
- 논문: `_bibliography/papers.bib` (`selected = {true}`이면 첫 화면에도 표시)
- 메뉴: `_data/nav.yml`
- CV: 별도 `resume-template-anubhav` 저장소에서 기존 LaTeX를 수정하고 PDF를 빌드합니다. 홈페이지가 해당 PDF를 자동으로 동기화합니다. CV 디자인을 홈페이지 템플릿으로 변환하지 않습니다.

가계부와 실험 대시보드는 가져오지 않았습니다. 기존 ICU 앱은 그대로 유지합니다.
