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

### 1. 원형 다이어그램 생성

#### 텍스트 입력 방식

```python
from src.diagram_generator import generate_diagram_from_text

text = """Title 1
내용 1

Title 2
내용 2

Title 3
내용 3"""

output_file = "output/circle_diagram.svg"
generate_diagram_from_text(text, output_file, "CENTER TEXT")
```

#### 구조화된 데이터 입력 방식

```python
from src.diagram_generator import generate_diagram_from_data

data = [
    {
        "title": "Title 1",
        "content": "내용 1"
    },
    {
        "title": "Title 2",
        "content": "내용 2"
    },
    {
        "title": "Title 3",
        "content": "내용 3"
    }
]

output_file = "output/circle_diagram.svg"
generate_diagram_from_data(data, output_file, "CENTER TEXT")
```

### 2. 타임라인 다이어그램 생성

#### 텍스트 입력 방식

```python
from src.timeline_generator import generate_timeline_from_text

text = """단계 1 제목
단계 1 설명 내용

단계 2 제목
단계 2 설명 내용

단계 3 제목
단계 3 설명 내용"""

output_file = "output/timeline_diagram.svg"
generate_timeline_from_text(
    text, 
    output_file, 
    title="타임라인 제목",
    colors=["#FECEAB"]
)
```

#### 구조화된 데이터 입력 방식

```python
from src.timeline_generator import generate_timeline_from_data

data = [
    {
        "step": "1",
        "title": "단계 1 제목",
        "content": "단계 1 설명 내용"
    },
    {
        "step": "2",
        "title": "단계 2 제목",
        "content": "단계 2 설명 내용"
    },
    {
        "step": "3",
        "title": "단계 3 제목",
        "content": "단계 3 설명 내용"
    }
]

output_file = "output/timeline_diagram.svg"
generate_timeline_from_data(
    data, 
    output_file, 
    title="타임라인 제목",
    colors=["#FECEAB"],
    background_color="#24292e",
    text_color="#FFFFFF"
)
```

### 3. 카드 스타일 다이어그램 생성

#### 텍스트 입력 방식

```python
from src.card_generator import generate_card_from_text

text = """골밀도의 정의
골밀도는 뼈에 존재하는 미네랄 함량(주로 칼슘)을 의미합니다.

측정 방법
이중 에너지 X선 흡수계측법(DXA)을 통해 T-점수로 측정됩니다.

정기 검사의 중요성
특히 노인의 경우 정기적인 골밀도 검사가 필수적입니다."""

output_file = "output/card_diagram.svg"
generate_card_from_text(
    text,
    output_file,
    title="골밀도란 무엇인가?",
    card_color="#FEEBDC",
    background_color="#111111"
)
```

#### 구조화된 데이터 입력 방식

```python
from src.card_generator import generate_card_from_data

data = [
    {
        "title": "골밀도의 정의",
        "content": "골밀도는 뼈에 존재하는 미네랄 함량(주로 칼슘)을 의미합니다."
    },
    {
        "title": "측정 방법",
        "content": "이중 에너지 X선 흡수계측법(DXA)을 통해 T-점수로 측정됩니다."
    },
    {
        "title": "정기 검사의 중요성",
        "content": "특히 노인의 경우 정기적인 골밀도 검사가 필수적입니다."
    }
]

output_file = "output/card_diagram.svg"
generate_card_from_data(
    data,
    output_file,
    title="골밀도란 무엇인가?",
    card_color="#FEEBDC",
    background_color="#111111"
)
```

#### 상단 이미지가 있는 카드 다이어그램

```python
from src.card_generator import generate_card_from_data

data = [
    {
        "title": "주요 이슈 1",
        "content": "이슈에 대한 설명 내용입니다."
    },
    {
        "title": "주요 이슈 2",
        "content": "이슈에 대한 설명 내용입니다."
    },
    {
        "title": "주요 이슈 3",
        "content": "이슈에 대한 설명 내용입니다."
    }
]

# 이미지 경로 설정
header_image = "path/to/your/image.jpg"  # 실제 이미지 경로로 변경

output_file = "output/header_image_card.svg"
generate_card_from_data(
    data,
    output_file,
    title="주요 이슈 모음",
    card_color="#E8F4F9",
    background_color="#21364b",
    header_image=header_image,
    header_image_height=300,
    header_color="#FFFFFF"
)
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

# SVG 다이어그램 생성기

이 프로젝트는 구조화된 데이터를 시각적인 SVG 다이어그램으로 변환하는 Python 라이브러리입니다. 두 가지 유형의 다이어그램(원형 및 타임라인)을 지원합니다.

## 기능

- 텍스트 또는 구조화된 데이터로부터 다이어그램 생성
- 반응형 SVG 이미지 출력
- 커스터마이징 가능한 색상 및 스타일
- 두 가지 다이어그램 유형 지원:
  - **원형 다이어그램**: 중앙 원을 중심으로 주변에 노드가 배치된 형태
  - **타임라인 다이어그램**: 세로로 나열된 단계별 정보 표시

## 요구사항

- Python 3.9 이상
- svgwrite 라이브러리

## 설치

```bash
pip install svgwrite
```

## 사용 방법

### 1. 원형 다이어그램 생성

#### 텍스트 입력 방식

```python
from src.diagram_generator import generate_diagram_from_text

text = """Title 1
내용 1

Title 2
내용 2

Title 3
내용 3"""

output_file = "output/circle_diagram.svg"
generate_diagram_from_text(text, output_file, "CENTER TEXT")
```

#### 구조화된 데이터 입력 방식

```python
from src.diagram_generator import generate_diagram_from_data

data = [
    {
        "title": "Title 1",
        "content": "내용 1"
    },
    {
        "title": "Title 2",
        "content": "내용 2"
    },
    {
        "title": "Title 3",
        "content": "내용 3"
    }
]

output_file = "output/circle_diagram.svg"
generate_diagram_from_data(data, output_file, "CENTER TEXT")
```

### 2. 타임라인 다이어그램 생성

#### 텍스트 입력 방식

```python
from src.timeline_generator import generate_timeline_from_text

text = """단계 1 제목
단계 1 설명 내용

단계 2 제목
단계 2 설명 내용

단계 3 제목
단계 3 설명 내용"""

output_file = "output/timeline_diagram.svg"
generate_timeline_from_text(
    text, 
    output_file, 
    title="타임라인 제목",
    colors=["#FECEAB"]
)
```

#### 구조화된 데이터 입력 방식

```python
from src.timeline_generator import generate_timeline_from_data

data = [
    {
        "step": "1",
        "title": "단계 1 제목",
        "content": "단계 1 설명 내용"
    },
    {
        "step": "2",
        "title": "단계 2 제목",
        "content": "단계 2 설명 내용"
    },
    {
        "step": "3",
        "title": "단계 3 제목",
        "content": "단계 3 설명 내용"
    }
]

output_file = "output/timeline_diagram.svg"
generate_timeline_from_data(
    data, 
    output_file, 
    title="타임라인 제목",
    colors=["#FECEAB"],
    background_color="#24292e",
    text_color="#FFFFFF"
)
```

### 3. 카드 스타일 다이어그램 생성

#### 텍스트 입력 방식

```python
from src.card_generator import generate_card_from_text

text = """골밀도의 정의
골밀도는 뼈에 존재하는 미네랄 함량(주로 칼슘)을 의미합니다.

측정 방법
이중 에너지 X선 흡수계측법(DXA)을 통해 T-점수로 측정됩니다.

정기 검사의 중요성
특히 노인의 경우 정기적인 골밀도 검사가 필수적입니다."""

output_file = "output/card_diagram.svg"
generate_card_from_text(
    text,
    output_file,
    title="골밀도란 무엇인가?",
    card_color="#FEEBDC",
    background_color="#111111"
)
```

#### 구조화된 데이터 입력 방식

```python
from src.card_generator import generate_card_from_data

data = [
    {
        "title": "골밀도의 정의",
        "content": "골밀도는 뼈에 존재하는 미네랄 함량(주로 칼슘)을 의미합니다."
    },
    {
        "title": "측정 방법",
        "content": "이중 에너지 X선 흡수계측법(DXA)을 통해 T-점수로 측정됩니다."
    },
    {
        "title": "정기 검사의 중요성",
        "content": "특히 노인의 경우 정기적인 골밀도 검사가 필수적입니다."
    }
]

output_file = "output/card_diagram.svg"
generate_card_from_data(
    data,
    output_file,
    title="골밀도란 무엇인가?",
    card_color="#FEEBDC",
    background_color="#111111"
)
```

#### 상단 이미지가 있는 카드 다이어그램

```python
from src.card_generator import generate_card_from_data

data = [
    {
        "title": "주요 이슈 1",
        "content": "이슈에 대한 설명 내용입니다."
    },
    {
        "title": "주요 이슈 2",
        "content": "이슈에 대한 설명 내용입니다."
    },
    {
        "title": "주요 이슈 3",
        "content": "이슈에 대한 설명 내용입니다."
    }
]

# 이미지 경로 설정
header_image = "path/to/your/image.jpg"  # 실제 이미지 경로로 변경

output_file = "output/header_image_card.svg"
generate_card_from_data(
    data,
    output_file,
    title="주요 이슈 모음",
    card_color="#E8F4F9",
    background_color="#21364b",
    header_image=header_image,
    header_image_height=300,
    header_color="#FFFFFF"
)
```

## 커스터마이징 옵션

### 원형 다이어그램

- `center_text`: 중앙 원에 표시할 텍스트
- `colors`: 노드 색상 리스트
- `size`: 이미지 크기 (정사각형)
- `background_color`: 배경색

### 타임라인 다이어그램

- `title`: 다이어그램 상단 제목
- `colors`: 각 단계 박스 색상
- `size_width`: 이미지 너비
- `size_height`: 이미지 높이 (null인 경우 자동 계산)
- `background_color`: 배경색
- `background_image`: 배경 이미지 경로 (선택 사항)
- `text_color`: 텍스트 색상

### 카드 스타일 다이어그램

- `title`: 다이어그램 상단 제목
- `card_color`: 카드 배경색 (기본값: "#FEEBDC" 베이지색)
- `title_color`: 카드 제목 색상
- `content_color`: 카드 내용 색상
- `size_width`: 이미지 너비
- `size_height`: 이미지 높이 (null인 경우 내용에 따라 자동 계산)
- `background_color`: 배경색 (기본값: "#111111" 어두운 배경)
- `background_image`: 배경 이미지 경로 (선택 사항)
- `header_image`: 상단 이미지 경로 (선택 사항)
- `header_image_height`: 상단 이미지 높이 (기본값: 300px)
- `header_color`: 헤더 텍스트 색상
- `rounded_corners`: 카드 모서리 둥글기 정도
- `card_padding`: 카드 내부 여백
- `vertical_spacing`: 카드 사이 세로 간격

## 예제

프로젝트에는 세 가지 유형의 다이어그램을 생성하는 테스트 스크립트가 포함되어 있습니다.

```bash
python src/test_circular_diagram.py  # 원형 다이어그램 예제
python src/test_timeline.py          # 타임라인 다이어그램 예제
python src/test_cards.py             # 카드 스타일 다이어그램 예제
python src/test_header_image.py      # 상단 이미지가 있는 카드 다이어그램 예제
```

## 라이선스

MIT