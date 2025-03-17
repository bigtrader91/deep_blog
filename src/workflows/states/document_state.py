"""
마크다운 문서의 상태를 표현하는 클래스.
변환 과정에서의 상태 정보를 유지하고 관리합니다.
"""

from typing import Dict, List, Optional, Any
from src.common.config.theme_styles import Theme

class DocumentState:
    """
    마크다운 문서의 상태를 표현하는 클래스.
    
    Attributes:
        markdown_text (str): 원본 마크다운 텍스트
        theme (Theme): 문서에 적용된 테마
        html_output (str): 변환된 HTML 출력물
        document_structure (Dict[str, Any]): 문서의 구조 정보
        sections (List[Dict[str, Any]]): 문서의 섹션 리스트
        errors (List[str]): 처리 과정에서 발생한 오류 메시지
        processing_complete (bool): 처리 완료 여부
    """
    def __init__(self, markdown_text: str, theme: Optional[Theme] = None):
        """
        DocumentState 초기화
        
        Args:
            markdown_text (str): 원본 마크다운 텍스트
            theme (Optional[Theme], optional): 문서 테마. 기본값은 None
        """
        self.markdown_text = markdown_text
        self.theme = theme if theme else Theme.PURPLE
        self.html_output = ""
        self.document_structure: Dict[str, Any] = {}
        self.sections: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.processing_complete = False

    def to_dict(self) -> Dict[str, Any]:
        """
        상태 객체를 사전 형태로 변환
        
        Returns:
            Dict[str, Any]: 상태 정보를 담은 사전
        """
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
        """
        사전으로부터 상태 객체 생성
        
        Args:
            state_dict (Dict[str, Any]): 상태 정보가 담긴 사전
            
        Returns:
            DocumentState: 생성된 상태 객체
        """
        obj = cls(state_dict["markdown_text"], state_dict.get("theme"))
        obj.html_output = state_dict.get("html_output", "")
        obj.document_structure = state_dict.get("document_structure", {})
        obj.sections = state_dict.get("sections", [])
        obj.errors = state_dict.get("errors", [])
        obj.processing_complete = state_dict.get("processing_complete", False)
        return obj 