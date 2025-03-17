"""
마크다운 파서 및 렌더링 로직.
마크다운 텍스트를 HTML로 변환하는 파서 및 렌더러를 제공합니다.
"""

import mistune
from typing import List, Dict, Any

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
        """
        제목 태그 렌더링
        
        Args:
            text: 제목 텍스트
            level: 제목 레벨 (1-6)
            
        Returns:
            str: 렌더링된 HTML
        """
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
        """
        문단 태그 렌더링
        
        Args:
            text: 문단 텍스트
            
        Returns:
            str: 렌더링된 HTML
        """
        self.section_counter += 1
        section_id = f"section-{self.section_counter}"
        self.sections.append({
            "type": "paragraph",
            "content": text,
            "level": 0,
            "section_id": section_id
        })
        return f'<p id="{section_id}">{text}</p>\n'

    def list(self, text, ordered, level, start=None, **kwargs):
        """
        목록 태그 렌더링
        
        Args:
            text: 목록 텍스트
            ordered: 순서 있는 목록 여부
            level: 목록 레벨
            start: 시작 번호 (순서 있는 목록의 경우)
            **kwargs: 추가 인자 (예: depth)
            
        Returns:
            str: 렌더링된 HTML
        """
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
        """
        테이블 태그 렌더링
        
        Args:
            header: 테이블 헤더 HTML
            body: 테이블 바디 HTML
            
        Returns:
            str: 렌더링된 HTML
        """
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
        """
        인용구 태그 렌더링
        
        Args:
            text: 인용구 텍스트
            
        Returns:
            str: 렌더링된 HTML
        """
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
        """
        코드 블록 태그 렌더링
        
        Args:
            code: 코드 텍스트
            info: 코드 언어 정보
            
        Returns:
            str: 렌더링된 HTML
        """
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
    
    Args:
        markdown_text (str): 파싱할 마크다운 텍스트
        
    Returns:
        List[Dict[str, Any]]: 파싱된 섹션 정보 목록
    """
    renderer = CustomRenderer()
    parser = mistune.create_markdown(renderer=renderer)
    _ = parser(markdown_text)
    return renderer.sections 