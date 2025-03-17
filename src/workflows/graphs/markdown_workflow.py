"""
마크다운 변환 워크플로우 정의 모듈.
LangGraph를 사용하여 마크다운을 HTML로 변환하는 워크플로우를 정의합니다.
"""

import os
import re
import json
from typing import Dict, List, Optional, Any, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# pydantic (Function Calling을 위한 모델)
try:
    from pydantic import BaseModel, Field
except ImportError:
    from pydantic.v1 import BaseModel, Field

# 로컬 임포트
from src.common.config.theme_styles import Theme, THEME_STYLES
from src.workflows.states.document_state import DocumentState
from src.core.content.formatters.markdown_formatter import parse_markdown_locally

# 환경 변수 로드
load_dotenv()

class ThemeOutput(BaseModel):
    """테마 추천 출력 모델"""
    recommended_theme: str = Field(..., description="문서에 적합한 테마. purple, green, blue, orange 중 하나")

def get_llm(model_name: str = "gpt-4o-mini", temperature: float = 0.0) -> ChatOpenAI:
    """
    LLM 모델을 초기화합니다.
    
    Args:
        model_name (str, optional): 모델 이름. 기본값은 "gpt-4o-mini"
        temperature (float, optional): 샘플링 온도. 기본값은 0.0
        
    Returns:
        ChatOpenAI: 초기화된 LLM 모델
    """
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )

def analyze_document_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    문서 구조를 분석하고 테마를 추천합니다.
    
    Args:
        state (Dict[str, Any]): 현재 문서 상태
        
    Returns:
        Dict[str, Any]: 업데이트된 문서 상태
    """
    doc_state = DocumentState.from_dict(state)

    # (1) 로컬 파싱
    sections = parse_markdown_locally(doc_state.markdown_text)
    doc_state.sections = sections

    # (2) LLM으로부터 recommended_theme만 받아오기
    llm = get_llm()
    
    # structured output을 지원하는 chain 생성
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

def convert_section_to_html(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    각 섹션을 HTML로 변환합니다.
    
    Args:
        state (Dict[str, Any]): 현재 문서 상태
        
    Returns:
        Dict[str, Any]: 업데이트된 문서 상태
    """
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
    """
    문서에 목차를 생성합니다.
    
    Args:
        state (Dict[str, Any]): 현재 문서 상태
        
    Returns:
        Dict[str, Any]: 업데이트된 문서 상태
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

def final_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 HTML 코드를 검토하고 수정합니다.
    
    Args:
        state (Dict[str, Any]): 현재 문서 상태
        
    Returns:
        Dict[str, Any]: 최종 문서 상태
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

class WorkflowState(TypedDict):
    """워크플로우 상태를 표현하는 타입"""
    markdown_text: str
    theme: Optional[Theme]
    html_output: str
    document_structure: Dict[str, Any]
    sections: List[Dict[str, Any]]
    errors: List[str]
    processing_complete: bool

def create_markdown_to_html_graph() -> StateGraph:
    """
    마크다운 변환 워크플로우 그래프를 생성합니다.
    
    Returns:
        StateGraph: 컴파일된 워크플로우 그래프
    """
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
    """
    마크다운 텍스트를 HTML로 변환합니다.
    
    Args:
        markdown_text (str): 변환할 마크다운 텍스트
        theme (Optional[Theme], optional): 사용할 테마. 지정하지 않으면 자동 추천됨
        
    Returns:
        str: 변환된 HTML 코드
    """
    doc_state = DocumentState(markdown_text, theme)
    initial_state = doc_state.to_dict()

    graph = create_markdown_to_html_graph()
    final_state = graph.invoke(initial_state)

    return final_state["html_output"] 