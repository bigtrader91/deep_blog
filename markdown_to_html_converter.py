"""
마크다운 문서를 HTML로 변환하는 시스템.
LangChain과 LangGraph를 활용하여 문서 내용을 분석하고 스타일이 적용된 HTML로 변환합니다.
"""

import os
import re
from typing import Dict, List, Optional, Any, Tuple, Union, Type
from enum import Enum
from dotenv import load_dotenv
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END

# 환경 변수 로드
load_dotenv()

# 스타일 테마 정의
class Theme(str, Enum):
    PURPLE = "purple"  # 보라색 미래 테마
    GREEN = "green"    # 초록색 자연 테마
    BLUE = "blue"      # 파란색 전문성 테마
    ORANGE = "orange"  # 주황색 활력 테마

# 문서 컴포넌트 정의
class DocumentComponent(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    QUOTE = "quote"
    FAQ = "faq"
    TOC = "toc"
    IMAGE = "image"

# 문서 분석 결과를 저장할 상태 클래스
class DocumentState:
    """문서 처리 상태 정보를 저장하는 클래스"""
    
    def __init__(self, markdown_text: str, theme: Optional[Theme] = None):
        """
        Args:
            markdown_text: 변환할 마크다운 텍스트
            theme: 적용할 테마 (옵션)
        """
        self.markdown_text = markdown_text
        self.theme = theme if theme else Theme.PURPLE  # 기본값은 보라색 테마
        self.html_output = ""
        self.document_structure = []
        self.sections = []
        self.errors = []
        self.processing_complete = False
    
    def to_dict(self) -> Dict[str, Any]:
        """상태 객체를 딕셔너리로 변환"""
        return {
            "markdown_text": self.markdown_text,
            "theme": self.theme,
            "html_output": self.html_output,
            "document_structure": self.document_structure,
            "sections": self.sections,
            "errors": self.errors,
            "processing_complete": self.processing_complete
        }
    
    @classmethod
    def from_dict(cls, state_dict: Dict[str, Any]) -> 'DocumentState':
        """딕셔너리에서 상태 객체 생성"""
        state = cls(state_dict["markdown_text"], state_dict.get("theme"))
        state.html_output = state_dict.get("html_output", "")
        state.document_structure = state_dict.get("document_structure", [])
        state.sections = state_dict.get("sections", [])
        state.errors = state_dict.get("errors", [])
        state.processing_complete = state_dict.get("processing_complete", False)
        return state

# 테마별 스타일 정의
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
    # 다른 테마도 필요하면 추가할 수 있습니다
}

# LLM 초기화 함수
def get_llm(model_name: str = "gpt-4o", temperature: float = 0.0) -> ChatOpenAI:
    """
    LLM 인스턴스를 생성합니다.
    
    Args:
        model_name: 사용할 모델 이름
        temperature: 온도 파라미터
        
    Returns:
        LLM 인스턴스
    """
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY")
    )

# 마크다운 문서 분석 함수
def analyze_document_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    마크다운 문서의 구조를 분석합니다.
    
    Args:
        state: 문서 처리 상태
        
    Returns:
        업데이트된 상태
    """
    doc_state = DocumentState.from_dict(state)
    markdown_text = doc_state.markdown_text
    
    # LLM을 사용하여 문서 구조 분석
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 마크다운 문서를 HTML로 변환하는 전문가입니다.
        주어진 마크다운 문서를 분석하여 구조를 파악하세요.
        문서 내의 섹션, 제목, 부제목, 목차, 단락, 리스트, 표, 코드 블록, 인용구 등을 식별하세요.
        자유로운 섹션 갯수와 적절한 태그 변환이 필요합니다.
        
        다음과 같은 컴포넌트를 식별하세요:
        - 제목 (title): 문서의 메인 제목
        - 부제목 (subtitle): 섹션 및 하위 섹션 제목
        - 단락 (paragraph): 일반 텍스트 단락
        - 리스트 (list): 순서가 있는/없는 리스트
        - 표 (table): 데이터 표
        - 코드 (code): 코드 블록
        - 인용구 (quote): 인용문
        - FAQ (faq): 질문과 답변 형식
        - 목차 (toc): 문서 목차
        - 이미지 (image): 이미지
        
        전체 문서를 이해하고 다음 형식의 JSON으로 응답하세요:
        {{
          "document_title": "문서 제목",
          "sections": [
            {{
              "type": "컴포넌트 유형",
              "content": "원본 마크다운 내용",
              "level": 레벨(제목의 경우 1-6),
              "section_id": "섹션 ID(목차 링크용)"
            }}
          ],
          "recommended_theme": "추천 테마(purple, green, blue, orange 중 하나)",
          "has_toc": true/false,
          "has_faq": true/false
        }}
        
        추천 테마는 문서 내용의 성격(기술 문서, 자연 관련, 비즈니스 등)을 고려하여 선택하세요.
        문서에 명시적인 목차가 없어도 목차가 필요한지 판단하세요.
        """),
        ("human", "{markdown_text}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"markdown_text": markdown_text})
    
    # 응답에서 JSON 추출
    result_str = response.content
    # JSON 문자열 추출 (프롬프트에서 JSON 형식으로 응답하도록 요청했으므로)
    json_match = re.search(r'```json\s*(.*?)\s*```', result_str, re.DOTALL)
    if json_match:
        result_str = json_match.group(1)
    else:
        # ```json 블록이 없는 경우 중괄호로 둘러싸인 부분 찾기
        json_match = re.search(r'({.*})', result_str, re.DOTALL)
        if json_match:
            result_str = json_match.group(1)
    
    import json
    try:
        result = json.loads(result_str)
        doc_state.document_structure = result
        
        # 추천 테마가 있으면 설정
        if "recommended_theme" in result:
            recommended_theme = result["recommended_theme"].lower()
            if recommended_theme in [t.value for t in Theme]:
                doc_state.theme = Theme(recommended_theme)
        
        # 섹션 정보 설정
        if "sections" in result:
            doc_state.sections = result["sections"]
    except json.JSONDecodeError as e:
        doc_state.errors.append(f"JSON 파싱 오류: {str(e)}")
        # 분석 실패시 기본 섹션으로 전체 문서 설정
        doc_state.sections = [{
            "type": "paragraph",
            "content": markdown_text,
            "level": 0,
            "section_id": "content"
        }]
    
    return doc_state.to_dict()

# 섹션별 HTML 변환 함수
def convert_section_to_html(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    각 섹션을 HTML로 변환합니다.
    
    Args:
        state: 문서 처리 상태
        
    Returns:
        업데이트된 상태
    """
    doc_state = DocumentState.from_dict(state)
    sections = doc_state.sections
    theme = doc_state.theme
    theme_styles = THEME_STYLES.get(theme, THEME_STYLES[Theme.PURPLE])
    
    llm = get_llm()
    
    # 테마 스타일을 문자열로 변환
    theme_styles_str = "\n".join([f"{k}: {v}" for k, v in theme_styles.items()])
    
    all_html_sections = []
    
    # 각 섹션을 HTML로 변환
    for section in sections:
        section_type = section.get("type", "paragraph")
        content = section.get("content", "")
        level = section.get("level", 0)
        section_id = section.get("section_id", "")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 마크다운을 HTML로 변환하는 전문가입니다.
            주어진 마크다운 섹션을 HTML로 변환하세요. 다음 스타일 정보를 참고하세요:
            
            테마: {theme.value}
            
            스타일 정보:
            {theme_styles_str}
            
            섹션 유형: {section_type}
            레벨(있는 경우): {level}
            섹션 ID(있는 경우): {section_id}
            
            다음 규칙을 따르세요:
            1. 마크다운 텍스트를 완전한 HTML로 변환하세요.
            2. 제목(#)은 적절한 h1-h6 태그와 스타일로 변환하세요.
            3. 단락은 p 태그와 스타일로 변환하세요.
            4. 리스트는 ol/ul/li 태그와 스타일로 변환하세요.
            5. 표는 table/thead/tbody/tr/th/td 태그와 스타일로 변환하세요.
            6. 코드 블록은 pre/code 태그와 스타일로 변환하세요.
            7. 인용구는 blockquote 태그와 스타일로 변환하세요.
            8. 강조는 strong 또는 b 태그와 스타일로 변환하세요.
            9. 이미지는 img 태그와 스타일로 변환하세요.
            10. 링크는 a 태그와 스타일로 변환하세요.
            11. 섹션 ID가 있는 경우 해당 HTML 요소에 id 속성을 추가하세요.
            
            HTML 태그와 스타일 속성만 반환하세요. 설명이나 주석은 필요하지 않습니다.
            """),
            ("human", "{content}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({"content": content})
        
        html_section = response.content.strip()
        # HTML 태그만 추출하기 위해 필요하면 처리
        if html_section.startswith('```html'):
            html_section = re.search(r'```html\s*(.*?)\s*```', html_section, re.DOTALL).group(1)
        elif html_section.startswith('<'):
            # 이미 HTML 태그로 시작하면 그대로 사용
            pass
        else:
            # 기본 단락으로 처리
            html_section = f'<p style="{theme_styles["p"]}">{html_section}</p>'
        
        all_html_sections.append(html_section)
    
    # 모든 섹션 HTML 합치기
    doc_state.html_output = "\n".join(all_html_sections)
    
    return doc_state.to_dict()

# 목차 생성 함수
def generate_toc(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    문서 구조에 기반하여 목차를 생성합니다.
    
    Args:
        state: 문서 처리 상태
        
    Returns:
        업데이트된 상태
    """
    doc_state = DocumentState.from_dict(state)
    document_structure = doc_state.document_structure
    
    # document_structure에 제목 정보가 있는지 확인
    if not document_structure or "sections" not in document_structure:
        return state
    
    # 목차 필요 여부 확인
    has_toc = document_structure.get("has_toc", False)
    if not has_toc:
        return state
    
    # 목차 항목 추출
    toc_items = []
    for section in document_structure["sections"]:
        if section.get("type") in ["title", "subtitle"] and section.get("level", 0) <= 3:
            section_id = section.get("section_id", "")
            if section_id:
                content = section.get("content", "").strip()
                # 마크다운 제목 형식(#) 제거
                content = re.sub(r'^#+\s+', '', content)
                toc_items.append({
                    "title": content,
                    "id": section_id,
                    "level": section.get("level", 1)
                })
    
    # 목차 HTML 생성
    if toc_items:
        theme = doc_state.theme
        theme_styles = THEME_STYLES.get(theme, THEME_STYLES[Theme.PURPLE])
        
        toc_html = f'<div style="{theme_styles["toc"]}">\n'
        toc_html += f'  <div style="margin-bottom: 15px;">\n'
        toc_html += f'    <h3 style="{theme_styles["toc_title"]}">목차</h3>\n'
        toc_html += f'  </div>\n'
        toc_html += f'  <div style="display: flex; flex-direction: column; gap: 10px;">\n'
        
        for item in toc_items:
            indent = "    " * (item["level"] - 1) if item["level"] > 1 else ""
            toc_html += f'{indent}    <a href="#{item["id"]}" style="{theme_styles["toc_link"]}">{item["title"]}</a>\n'
        
        toc_html += f'  </div>\n'
        toc_html += f'</div>\n'
        
        # HTML 출력 시작 부분에 목차 추가
        doc_state.html_output = toc_html + doc_state.html_output
    
    return doc_state.to_dict()

# 최종 검토 및 수정 함수
def final_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 HTML 출력을 검토하고 수정합니다.
    
    Args:
        state: 문서 처리 상태
        
    Returns:
        업데이트된 상태
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
        
        수정한 완전한 HTML 코드만 반환하세요. 설명이나 주석은 필요하지 않습니다.
        """),
        ("human", "{html}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"html": html_output})
    
    # 검토된 HTML로 업데이트
    doc_state.html_output = response.content.strip()
    doc_state.processing_complete = True
    
    return doc_state.to_dict()

# 워크플로우 그래프 설정
def create_markdown_to_html_graph() -> StateGraph:
    """
    마크다운을 HTML로 변환하는 워크플로우 그래프를 생성합니다.
    
    Returns:
        StateGraph: 워크플로우 그래프
    """
    # 상태 스키마 정의
    class WorkflowState(TypedDict):
        markdown_text: str
        theme: Optional[str]
        html_output: str
        document_structure: List[Dict[str, Any]]
        sections: List[Dict[str, Any]]
        errors: List[str]
        processing_complete: bool
    
    workflow = StateGraph(WorkflowState)
    
    # 노드 추가
    workflow.add_node("analyze_document", analyze_document_structure)
    workflow.add_node("convert_section", convert_section_to_html)
    workflow.add_node("generate_toc", generate_toc)
    workflow.add_node("final_review", final_review)
    
    # 엣지 추가
    workflow.set_entry_point("analyze_document")
    workflow.add_edge("analyze_document", "convert_section")
    workflow.add_edge("convert_section", "generate_toc")
    workflow.add_edge("generate_toc", "final_review")
    workflow.add_edge("final_review", END)
    
    return workflow.compile()

# 마크다운을 HTML로 변환하는 메인 함수
def convert_markdown_to_html(markdown_text: str, theme: Optional[Theme] = None) -> str:
    """
    마크다운 텍스트를 HTML로 변환합니다.
    
    Args:
        markdown_text: 변환할 마크다운 텍스트
        theme: 사용할 테마 (없으면 내용 기반으로 선택)
        
    Returns:
        변환된 HTML 코드
    """
    # 초기 상태 설정
    initial_state = DocumentState(markdown_text, theme).to_dict()
    
    # 워크플로우 그래프 생성
    graph = create_markdown_to_html_graph()
    
    # 워크플로우 실행
    final_state = graph.invoke(initial_state)
    
    # 결과 반환
    return final_state["html_output"]

# 실행 예시
if __name__ == "__main__":
    # 예시 마크다운 텍스트
    sample_markdown = """# 파이썬 데이터 분석 기초
    
## 소개
파이썬은 데이터 분석을 위한 강력한 도구입니다. 다양한 라이브러리를 활용하여 데이터를 효과적으로 처리할 수 있습니다.

### 필요한 라이브러리
- pandas: 데이터 처리 및 분석
- numpy: 수치 계산
- matplotlib: 데이터 시각화
- seaborn: 고급 데이터 시각화

## 데이터 불러오기
```python
import pandas as pd
import numpy as np

# CSV 파일 불러오기
df = pd.read_csv('data.csv')
print(df.head())
```

## 데이터 전처리
데이터 전처리는 분석 과정에서 매우 중요한 단계입니다.

### 결측치 처리
결측치는 분석 결과에 영향을 줄 수 있으므로 적절히 처리해야 합니다.

| 방법 | 장점 | 단점 |
|------|------|------|
| 삭제 | 간단함 | 데이터 손실 |
| 평균값 대체 | 데이터 보존 | 분포 변화 |
| 예측값 대체 | 정확도 높음 | 복잡함 |

> 데이터의 특성에 따라 적절한 방법을 선택해야 합니다.

## FAQ

### Q: 파이썬으로 할 수 있는 데이터 분석은 무엇인가요?
A: 파이썬은 데이터 정제, 변환, 시각화, 모델링 등 다양한 데이터 분석 작업을 수행할 수 있습니다.

### Q: 초보자가 배우기 쉬운 라이브러리는 무엇인가요?
A: pandas와 matplotlib이 초보자에게 추천되는 라이브러리입니다. 직관적인 API와 풍부한 문서를 제공합니다.
"""
    
    # 변환 실행
    html_output = convert_markdown_to_html(sample_markdown)
    print(html_output)
    
    # 결과를 파일로 저장
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(html_output) 