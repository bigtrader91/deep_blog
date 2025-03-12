# src/markdown_to_html_converter.py
"""
마크다운 문서를 HTML로 변환하는 시스템.
LangChain과 LangGraph를 활용하여 문서 내용을 분석하고 스타일이 적용된 HTML로 변환합니다.
(개선 버전)
"""

import os
import re
import json
from typing import Dict, List, Optional, Any
from enum import Enum
from dotenv import load_dotenv
from typing_extensions import TypedDict

# 마크다운 파싱 라이브러리
import mistune

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# pydantic (Function Calling을 위한 모델)
try:
    from pydantic import BaseModel, Field
except ImportError:
    from pydantic.v1 import BaseModel, Field

load_dotenv()

#################################
# 1) 테마, 스타일, DocumentState #
#################################
class Theme(str, Enum):
    PURPLE = "purple"
    GREEN = "green"
    BLUE = "blue"
    ORANGE = "orange"

THEME_STYLES = {
    Theme.PURPLE: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #4a148c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #7b1fa2; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #4a148c; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #9c27b0; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #6a1b9a; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #8e24aa; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #6a1b9a; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #8e24aa; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #9c27b0; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #6a1b9a; background-color: #f9f2ff; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #e1bee7; padding: 0.5em; text-align: left; background-color: #9c27b0; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #e1bee7; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #f5f0ff, #f0e6ff); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(106, 27, 154, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #9c27b0;",
        "toc_title": "font-weight: 700; color: #4a148c; font-size: 18px; margin: 0;",
        "toc_link": "color: #6a1b9a; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #9c27b0; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#9c27b0",
        "accent_bg": "#f5f0ff"
    },
    Theme.GREEN: {
        "h1": "font-size: 2.2rem; font-weight: 700; color: #1b5e20; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-bottom: 3px solid #388e3c; padding-bottom: 0.3em; font-family: 'Noto Sans KR', sans-serif;",
        "h2": "font-size: 1.8rem; font-weight: 700; color: #1b5e20; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; border-left: 5px solid #4caf50; padding-left: 0.8em; font-family: 'Noto Sans KR', sans-serif;",
        "h3": "font-size: 1.5rem; font-weight: 700; color: #ffffff; background-color: #2e7d32; padding: 0.5em 1em; border-radius: 4px; width: 100%; box-sizing: border-box; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-family: 'Noto Sans KR', sans-serif;",
        "h4": "font-size: 1.2rem; font-weight: 700; color: #43a047; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.2; font-style: italic; font-family: 'Noto Sans KR', sans-serif;",
        "p": "font-size: 1rem; line-height: 1.8; margin-bottom: 1.2em; color: #333; font-family: 'Noto Sans KR', sans-serif;",
        "strong": "font-weight: 700; color: #2e7d32; font-family: 'Noto Sans KR', sans-serif;",
        "b": "font-weight: 700; color: #43a047; font-family: 'Noto Sans KR', sans-serif;",
        "blockquote": "border-left: 4px solid #4caf50; padding: 0.5em 1em; margin: 1.5em 0; font-style: italic; color: #2e7d32; background-color: #e8f5e9; font-family: 'Noto Sans KR', sans-serif;",
        "table_header": "border: 1px solid #c8e6c9; padding: 0.5em; text-align: left; background-color: #4caf50; color: white; font-weight: 700;",
        "table_cell": "border: 1px solid #c8e6c9; padding: 0.5em; text-align: left;",
        "toc": "background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(46, 125, 50, 0.08); font-family: 'Noto Sans KR', sans-serif; border-left: 4px solid #4caf50;",
        "toc_title": "font-weight: 700; color: #1b5e20; font-size: 18px; margin: 0;",
        "toc_link": "color: #2e7d32; text-decoration: none; font-weight: 500;",
        "list_marker": "display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #4caf50; margin-right: 10px; position: absolute; left: -20px; top: 8px;",
        "accent_color": "#4caf50",
        "accent_bg": "#e8f5e9"
    },
}

class DocumentState:
    def __init__(self, markdown_text: str, theme: Optional[Theme] = None):
        self.markdown_text = markdown_text
        self.theme = theme if theme else Theme.PURPLE
        self.html_output = ""
        self.document_structure: Dict[str, Any] = {}
        self.sections: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.processing_complete = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "markdown_text": self.markdown_text,
            "theme": self.theme,
            "html_output": self.html_output,
            "document_structure": self.document_structure,
            "sections": self.sections,
            "errors": self.errors,
            "processing_complete": self.processing_complete,
        }

    @classmethod
    def from_dict(cls, state_dict: Dict[str, Any]) -> 'DocumentState':
        obj = cls(state_dict["markdown_text"], state_dict.get("theme"))
        obj.html_output = state_dict.get("html_output", "")
        obj.document_structure = state_dict.get("document_structure", {})
        obj.sections = state_dict.get("sections", [])
        obj.errors = state_dict.get("errors", [])
        obj.processing_complete = state_dict.get("processing_complete", False)
        return obj

#########################################
# 2) LLM 초기화 + ThemeOutput (구조화 모델)#
#########################################
def get_llm(model_name: str = "gpt-4o-mini", temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )

class ThemeOutput(BaseModel):
    recommended_theme: str = Field(..., description="문서에 적합한 테마. purple, green, blue, orange 중 하나")

##################################
# 3) 로컬 파싱 (mistune) Renderer #
##################################
class CustomRenderer(mistune.HTMLRenderer):
    def __init__(self):
        super().__init__()
        self.sections: List[Dict[str, Any]] = []
        self.section_counter = 0

    def heading(self, text, level):
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
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        self.sections.append({
            "type": "paragraph",
            "content": text,
            "level": 0,
            "section_id": section_id
        })
        return f'<p id="{section_id}">{text}</p>\n'

    def list(self, text, ordered, level, start=None):
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        list_type = "ul" if not ordered else "ol"
        self.sections.append({
            "type": "list",
            "content": text,
            "level": level,
            "section_id": section_id
        })
        return f'<{list_type} id="{section_id}">\n{text}</{list_type}>\n'

    def table(self, header, body):
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
    renderer = CustomRenderer()
    parser = mistune.create_markdown(renderer=renderer)
    _ = parser(markdown_text)
    return renderer.sections

##########################################
# 4) analyze_document_structure (수정됨) #
##########################################
def analyze_document_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    1) 로컬 파싱으로 섹션 생성
    2) LLM으로부터 recommended_theme만 안전하게 받아온다 (structured output)
    3) 파싱 실패하면 theme=purple로 fallback
    """
    doc_state = DocumentState.from_dict(state)

    # (1) 로컬 파싱
    sections = parse_markdown_locally(doc_state.markdown_text)
    doc_state.sections = sections

    # (2) LLM으로부터 recommended_theme만 받아오기
    llm = get_llm()
    
    # structured output을 지원하는 chain 생성
    #   method="function_calling" 반드시 지정
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
    
    # with_structured_output(ThemeOutput)으로 안전 파싱
    chain = theme_prompt | llm.with_structured_output(ThemeOutput, method="function_calling")
    try:
        result = chain.invoke({"markdown_text": doc_state.markdown_text})
        theme_str = result.recommended_theme.lower().strip()
        if theme_str in [t.value for t in Theme]:
            doc_state.theme = Theme(theme_str)
    except Exception as e:
        doc_state.errors.append(f"테마 분석 실패: {str(e)}")
        # fallback
        doc_state.theme = Theme.PURPLE

    return doc_state.to_dict()

#############################
# 5) 섹션별 HTML 변환 함수 #
#############################
def convert_section_to_html(state: Dict[str, Any]) -> Dict[str, Any]:
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

##########################
# 6) 목차(Toc) 항상 생성 #
##########################
def generate_toc(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    FAQ, TOC는 항상 사용한다고 가정 -> has_toc가 없어도 무조건 TOC 생성
    """
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

###########################################
# 7) 최종 검토(Conclusion 중복 등) 항상 FAQ #
###########################################
def final_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 HTML 코드 검토 (결론 중복 제거 등)
    FAQ도 무조건 포함된다고 가정 -> 별도 로직 없음
    """
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

##########################
# 8) 워크플로우 구성/실행 #
##########################
def create_markdown_to_html_graph() -> StateGraph:
    class WorkflowState(TypedDict):
        markdown_text: str
        theme: Optional[Theme]
        html_output: str
        document_structure: Dict[str, Any]
        sections: List[Dict[str, Any]]
        errors: List[str]
        processing_complete: bool

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

def convert_markdown_to_html(markdown_text: str, theme: Optional[Theme] = None) -> str:
    doc_state = DocumentState(markdown_text, theme)
    initial_state = doc_state.to_dict()

    graph = create_markdown_to_html_graph()
    final_state = graph.invoke(initial_state)

    return final_state["html_output"]

#######################
# 9) 실행 예시 (테스트)#
#######################
if __name__ == "__main__":
    sample_markdown = """# 예시 문서 타이틀

## 소개
이 문서는 LangChain과 Python 라이브러리를 활용해
마크다운을 HTML로 변환하는 예시입니다.

## 결론
이건 첫 번째 결론

## 결론
이건 두 번째 결론 (중복)

"""
    html_result = convert_markdown_to_html(sample_markdown)
    print(html_result)
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(html_result)
