# 마크다운-HTML 변환기

LangChain과 LangGraph를 활용한 마크다운 문서를 HTML로 변환하는 시스템입니다. 이 프로젝트는 GPT-4o 모델을 사용하여 마크다운 문서의 내용을 분석하고, 적절한 HTML 태그와 스타일을 적용합니다.

## 주요 특징

- 마크다운 문서의 구조 자동 분석
- 문서 내용에 따른 자동 테마 선택
- 보라색, 초록색 등 다양한 테마 지원
- FAQ, 표, 목차 등 다양한 컴포넌트 자동 인식
- 문서 구조에 기반한 목차 자동 생성
- 스타일링된 HTML 출력

## 설치

1. 프로젝트를 클론합니다:
```bash
git clone https://github.com/yourusername/markdown-to-html.git
cd markdown-to-html
```

2. 가상환경을 생성하고 활성화합니다:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

4. `.env` 파일을 생성하고 OpenAI API 키를 설정합니다:
```
OPENAI_API_KEY=your_api_key_here
```

## 사용 방법

### 기본 사용법

```python
from markdown_to_html_converter import convert_markdown_to_html, Theme

# 파일에서 마크다운 읽기
with open("example_markdown.md", "r", encoding="utf-8") as f:
    markdown_text = f.read()

# HTML로 변환 (테마 자동 선택)
html_output = convert_markdown_to_html(markdown_text)

# 결과를 파일로 저장
with open("output.html", "w", encoding="utf-8") as f:
    f.write(html_output)
```

### 특정 테마 지정

```python
from markdown_to_html_converter import convert_markdown_to_html, Theme

# 파일에서 마크다운 읽기
with open("example_markdown.md", "r", encoding="utf-8") as f:
    markdown_text = f.read()

# HTML로 변환 (특정 테마 지정)
html_output = convert_markdown_to_html(markdown_text, theme=Theme.GREEN)

# 결과를 파일로 저장
with open("output.html", "w", encoding="utf-8") as f:
    f.write(html_output)
```

## 변환 파이프라인

1. **문서 구조 분석**: LLM을 사용하여 마크다운 문서의 구조를 분석합니다.
2. **섹션 변환**: 각 섹션을 HTML로 변환합니다.
3. **목차 생성**: 문서 구조를 기반으로 목차를 생성합니다.
4. **최종 검토**: 생성된 HTML을 검토하고 필요한 경우 수정합니다.

## 지원하는 마크다운 요소

- 제목 (h1~h6)
- 단락
- 목록 (순서 있는/없는)
- 표
- 코드 블록
- 인용구
- 링크
- 이미지
- FAQ 섹션
- 목차

## 프로젝트 구조

```
markdown-to-html/
├── markdown_to_html_converter.py   # 메인 변환 코드
├── requirements.txt                # 의존성 목록
├── example_markdown.md             # 예제 마크다운 파일
├── .env                            # 환경 변수 파일
└── README.md                       # 사용 방법
```

## 라이선스

MIT

## 기여

이슈와 풀 리퀘스트를 환영합니다. 대규모 변경사항은 먼저 이슈를 열어 논의해 주세요.