"""
마크다운 변환기 독립 실행 스크립트.
의존성 문제 없이 마크다운 변환 기능만 사용할 수 있습니다.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트 경로를 파이썬 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 직접 필요한 모듈만 임포트
from src.common.config.theme_styles import Theme, THEME_STYLES
from src.workflows.states.document_state import DocumentState

# 마크다운 파서 직접 구현
import mistune
from typing import List, Dict, Any, TypedDict

# LangChain 관련 모듈과 연동하기
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# 환경 변수 설정
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# pydantic 임포트 (function calling 용)
try:
    from pydantic import BaseModel, Field
except ImportError:
    from pydantic.v1 import BaseModel, Field

# 마크다운 파서 직접 구현
class CustomRenderer(mistune.HTMLRenderer):
    """
    마크다운을 HTML로 변환하는 커스텀 렌더러.
    각 섹션에 대한 정보를 수집하고 HTML로 변환합니다.
    """
    def __init__(self):
        """CustomRenderer 초기화"""
        super().__init__()
        self.sections: List[Dict[str, Any]] = []
        self.section_counter = 0

    def heading(self, text, level):
        """제목 태그 렌더링"""
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        self.sections.append({
            "type": "subtitle" if level > 1 else "title",
            "content": text,
            "level": level,
            "section_id": section_id
        })
        return f'<h{level} id="{section_id}">{text}</h{level}>\n'

    def paragraph(self, text):
        """문단 태그 렌더링"""
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        self.sections.append({
            "type": "paragraph",
            "content": text,
            "level": 0,
            "section_id": section_id
        })
        return f'<p id="{section_id}">{text}</p>\n'

    def list(self, body, ordered, **kwargs):
        """
        목록 태그 렌더링 - mistune 최신 버전 호환
        
        Args:
            body: 목록 내용
            ordered: 순서 있는 목록 여부
            **kwargs: 추가 인자 (depth, start 등)
        """
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        list_type = "ol" if ordered else "ul"
        
        # kwargs에서 level 추출 또는 기본값 사용
        level = kwargs.get('level', kwargs.get('depth', 0))
        
        self.sections.append({
            "type": "list",
            "content": body,
            "level": level,
            "section_id": section_id
        })
        return f'<{list_type} id="{section_id}">\n{body}</{list_type}>\n'

    def table(self, header, body):
        """테이블 태그 렌더링"""
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        self.sections.append({
            "type": "table",
            "content": header + body,
            "level": 0,
            "section_id": section_id
        })
        return f'<table id="{section_id}">\n{header}{body}</table>\n'

    def block_quote(self, text):
        """인용구 태그 렌더링"""
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        self.sections.append({
            "type": "quote",
            "content": text,
            "level": 0,
            "section_id": section_id
        })
        return f'<blockquote id="{section_id}">{text}</blockquote>\n'

    def block_code(self, code, info=None):
        """코드 블록 태그 렌더링"""
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        self.sections.append({
            "type": "code",
            "content": code,
            "level": 0,
            "section_id": section_id
        })
        language = info or ""
        return f'<pre id="{section_id}"><code class="language-{language}">{code}</code></pre>\n'

def parse_markdown_locally(markdown_text: str) -> List[Dict[str, Any]]:
    """
    마크다운 텍스트를 로컬에서 파싱하여 섹션 정보를 반환합니다.
    """
    renderer = CustomRenderer()
    parser = mistune.create_markdown(renderer=renderer)
    _ = parser(markdown_text)
    return renderer.sections

class ThemeOutput(BaseModel):
    """테마 추천 출력 모델"""
    recommended_theme: str = Field(..., description="문서에 적합한 테마. purple, green, blue, orange 중 하나")

def get_llm(model_name: str = "gpt-4o-mini", temperature: float = 0.0) -> ChatOpenAI:
    """LLM 모델 초기화"""
    return ChatOpenAI(
        model=model_name,
        temperature=temperature
    )

def analyze_document_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    """문서 구조 분석 및 테마 추천"""
    doc_state = DocumentState.from_dict(state)
    sections = parse_markdown_locally(doc_state.markdown_text)
    doc_state.sections = sections
    
    # LLM으로부터 테마 추천받기
    llm = get_llm()
    theme_prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 마크다운 분석 전문가입니다.
문서 내용(한국어)과 전반적 분위기를 보고, purple/green/blue/orange 중 하나를 추천하세요.

출력 예:
{
  "recommended_theme": "purple"
}

절대 다른 key를 넣지 말고 recommended_theme만 넣으세요.
"""),
        ("human", "{markdown_text}")
    ])
    
    chain = theme_prompt | llm.with_structured_output(ThemeOutput, method="function_calling")
    try:
        result = chain.invoke({"markdown_text": doc_state.markdown_text})
        theme_str = result.recommended_theme.lower().strip()
        if theme_str in [t.value for t in Theme]:
            doc_state.theme = Theme(theme_str)
    except Exception as e:
        doc_state.errors.append(f"테마 분석 실패: {str(e)}")
        doc_state.theme = Theme.PURPLE
    
    return doc_state.to_dict()

def convert_section_to_html(state: Dict[str, Any]) -> Dict[str, Any]:
    """섹션별 HTML 변환"""
    doc_state = DocumentState.from_dict(state)
    sections = doc_state.sections
    theme = doc_state.theme
    theme_styles = THEME_STYLES.get(theme, THEME_STYLES[Theme.PURPLE])

    html_output_list = []
    for sec in sections:
        s_type = sec.get("type", "paragraph")
        s_content = sec.get("content", "")
        level = sec.get("level", 0)
        s_id = sec.get("section_id", "")

        if s_type in ["title", "subtitle"]:
            tag = f"h{level}" if 1 <= level <= 6 else "h2"
            style_key = f"h{level}" if f"h{level}" in theme_styles else "h2"
            html_piece = f'<{tag} id="{s_id}" style="{theme_styles[style_key]}">{s_content}</{tag}>'
        elif s_type == "paragraph":
            html_piece = f'<p id="{s_id}" style="{theme_styles["p"]}">{s_content}</p>'
        elif s_type == "list":
            html_piece = f'<ul id="{s_id}">{s_content}</ul>'
        elif s_type == "code":
            html_piece = f'''
<pre id="{s_id}" style="background: #f5f2ff; padding: 1em;">
<code>{s_content}</code>
</pre>
'''
        elif s_type == "table":
            html_piece = f'<table id="{s_id}" style="border-collapse: collapse; margin-bottom: 1em;">{s_content}</table>'
        elif s_type == "quote":
            html_piece = f'<blockquote id="{s_id}" style="{theme_styles["blockquote"]}">{s_content}</blockquote>'
        else:
            html_piece = f'<p id="{s_id}" style="{theme_styles["p"]}">{s_content}</p>'

        html_output_list.append(html_piece)

    doc_state.html_output = "\n".join(html_output_list)
    return doc_state.to_dict()

def generate_toc(state: Dict[str, Any]) -> Dict[str, Any]:
    """목차 생성"""
    doc_state = DocumentState.from_dict(state)
    theme_styles = THEME_STYLES.get(doc_state.theme, THEME_STYLES[Theme.PURPLE])
    sections = doc_state.sections

    # h1~h3만 목차 수집
    toc_items = []
    seen_titles = set()
    for sec in sections:
        if sec["type"] in ["title", "subtitle"]:
            lvl = sec["level"] if sec["level"] else 1
            if lvl > 3:
                continue
            text = sec["content"].strip()
            if text not in seen_titles:
                toc_items.append({
                    "title": text,
                    "id": sec["section_id"],
                    "level": lvl
                })
                seen_titles.add(text)

    if not toc_items:
        return doc_state.to_dict()

    toc_html = f'<div style="{theme_styles["toc"]}">\n'
    toc_html += f'  <div style="margin-bottom: 15px;">\n'
    toc_html += f'    <h3 style="{theme_styles["toc_title"]}">목차</h3>\n'
    toc_html += f'  </div>\n'
    toc_html += f'  <div style="display: flex; flex-direction: column; gap: 10px;">\n'
    for item in toc_items:
        indent = "  " * (item["level"] - 1) if item["level"] > 1 else ""
        toc_html += f'{indent}<a href="#{item["id"]}" style="{theme_styles["toc_link"]}">{item["title"]}</a>\n'
    toc_html += f'  </div>\n'
    toc_html += f'</div>\n'

    # h1 뒤, 또는 문서 맨 앞
    html_output = doc_state.html_output
    pos_h1_end = html_output.find("</h1>")
    if pos_h1_end != -1:
        pos_h2 = html_output.find("<h2", pos_h1_end)
        if pos_h2 != -1:
            new_html = html_output[:pos_h2] + toc_html + html_output[pos_h2:]
        else:
            new_html = html_output[:pos_h1_end+5] + toc_html + html_output[pos_h1_end+5:]
        doc_state.html_output = new_html
    else:
        doc_state.html_output = toc_html + "\n" + html_output

    return doc_state.to_dict()

def final_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """최종 HTML 코드 검토"""
    doc_state = DocumentState.from_dict(state)
    html_output = doc_state.html_output

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HTML 코드 검토 전문가입니다.
다음 HTML 코드를 검토하고 필요한 경우 수정하세요.

확인해야 할 사항:
1. 모든 HTML 태그가 올바르게 닫혔는지
2. 모든 style 속성이 올바른 형식인지
3. id 속성이 적절하게 사용되었는지
4. 전체적인 구조가 일관되고 가독성이 좋은지
5. 'Conclusion', '결론', '마무리' 등 결론이 중복이면 하나만 남기세요.

수정한 완전한 HTML 코드만 반환하세요. 다른 설명이나 주석은 넣지 마세요.
        """),
        ("human", "{html}")
    ])
    chain = prompt | llm
    response = chain.invoke({"html": html_output})

    doc_state.html_output = response.content.strip()
    doc_state.processing_complete = True
    return doc_state.to_dict()

class WorkflowState(TypedDict):
    """워크플로우 상태 타입"""
    markdown_text: str
    theme: Optional[Theme]
    html_output: str
    document_structure: Dict[str, Any]
    sections: List[Dict[str, Any]]
    errors: List[str]
    processing_complete: bool

def create_markdown_to_html_graph() -> StateGraph:
    """워크플로우 그래프 생성"""
    workflow = StateGraph(WorkflowState)
    workflow.add_node("analyze_document", analyze_document_structure)
    workflow.add_node("convert_section", convert_section_to_html)
    workflow.add_node("generate_toc", generate_toc)
    workflow.add_node("final_review", final_review)

    workflow.set_entry_point("analyze_document")
    workflow.add_edge("analyze_document", "convert_section")
    workflow.add_edge("convert_section", "generate_toc")
    workflow.add_edge("generate_toc", "final_review")
    workflow.add_edge("final_review", END)
    return workflow.compile()

def markdown_to_html(markdown_text: str, theme_name: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    마크다운 텍스트를 HTML로 변환합니다.
    
    Args:
        markdown_text (str): 변환할 마크다운 텍스트
        theme_name (Optional[str], optional): 테마 이름 ('purple', 'green', 'blue', 'orange')
        output_path (Optional[str], optional): 결과를 저장할 파일 경로
        
    Returns:
        str: 변환된 HTML 코드
    """
    # 테마 설정
    theme = None
    if theme_name:
        try:
            theme = Theme(theme_name.lower())
        except ValueError:
            print(f"지원하지 않는 테마입니다: {theme_name}. 'purple', 'green', 'blue', 'orange' 중 하나를 사용하세요.")
            theme = Theme.PURPLE

    # 마크다운 변환 실행
    doc_state = DocumentState(markdown_text, theme)
    initial_state = doc_state.to_dict()
    
    graph = create_markdown_to_html_graph()
    final_state = graph.invoke(initial_state)
    
    html_result = final_state["html_output"]
    
    # 마크다운 코드 블록 형식 제거
    html_result = html_result.replace("```html", "").replace("```", "").strip()
    
    # 결과 저장
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_result)
        print(f"HTML이 저장되었습니다: {output_path}")
    
    return html_result

# 예제 마크다운 텍스트
SAMPLE_MARKDOWN = """# 예시 문서 타이틀

## 소개
이 문서는 LangChain과 Python 라이브러리를 활용해
마크다운을 HTML로 변환하는 예시입니다.

## 특징
- LangChain 워크플로우 활용
- LLM을 통한 테마 추천
- 자동 목차 생성
- 스타일링 적용

## 코드 예시
```python
def hello_world():
    print("안녕하세요!")
```

## 결론
이 예제는 마크다운 변환기의 기능을 보여줍니다.

## 결론
이건 두 번째 결론 (중복)
"""

if __name__ == "__main__":
    # 명령행 인자 파싱
    import argparse
    
    parser = argparse.ArgumentParser(description="마크다운을 HTML로 변환합니다.")
    parser.add_argument("-i", "--input", help="입력 마크다운 파일 경로")
    parser.add_argument("-o", "--output", help="출력 HTML 파일 경로", default="output.html")
    parser.add_argument("-t", "--theme", help="HTML 테마 (purple, green, blue, orange)", default="purple")
    parser.add_argument("-s", "--sample", help="샘플 마크다운 사용", action="store_true")
    
    args = parser.parse_args()
    
    print("마크다운 변환기 시작...")
    
    if args.sample:
        # 샘플 마크다운 사용
        md_text = SAMPLE_MARKDOWN
        print("샘플 마크다운 사용 중...")
    elif args.input:
        # 파일에서 마크다운 읽기
        with open(args.input, "r", encoding="utf-8") as f:
            md_text = f.read()
        print(f"파일에서 마크다운을 읽었습니다: {args.input}")
    else:
        # 대화형으로 마크다운 입력 받기
        print("마크다운을 입력하세요 (입력 종료: Ctrl+D 또는 Ctrl+Z 후 Enter):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        md_text = "\n".join(lines)
    
    # 마크다운 -> HTML 변환
    html_result = markdown_to_html(
        md_text,
        theme_name=args.theme,
        output_path=args.output
    )
    
    print(f"\n변환 완료! HTML 길이: {len(html_result)} 문자")
    print(f"HTML 저장 경로: {args.output}")
    print("변환기 종료.") 