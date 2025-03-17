"""
섹션 형식화를 위한 유틸리티 클래스

이 모듈은 블로그 또는 문서의 섹션을 형식화하는 기능을 제공합니다.
"""
from typing import List, Dict, Any, Optional


class SectionFormatter:
    """섹션을 형식화하는 유틸리티 클래스
    
    이 클래스는 다양한 섹션을 일관된 형식으로 변환하고 표시하는 기능을 제공합니다.
    """
    
    @classmethod
    def format_sections(cls, sections: List[Any]) -> str:
        """섹션 목록을 문자열로 형식화합니다.
        
        Args:
            sections (List[Any]): 형식화할 섹션 목록
            
        Returns:
            str: 형식화된 섹션 문자열
        """
        formatted_str = ""
        for idx, section in enumerate(sections, 1):
            formatted_str += f"""
{'='*60}
섹션 {idx}: {section.name}
{'='*60}
설명:
{section.description}
조사 필요: 
{section.research}

내용:
{section.content if section.content else '[아직 작성되지 않음]'}

"""
        return formatted_str
    
    @classmethod
    def format_sections_as_markdown(cls, sections: List[Any]) -> str:
        """섹션 목록을 마크다운 형식으로 변환합니다.
        
        Args:
            sections (List[Any]): 형식화할 섹션 목록
            
        Returns:
            str: 마크다운 형식의 섹션 문자열
        """
        markdown_str = "# 문서 개요\n\n"
        
        # 목차 생성
        markdown_str += "## 목차\n\n"
        for idx, section in enumerate(sections, 1):
            markdown_str += f"{idx}. [{section.name}](#섹션-{idx})\n"
        
        markdown_str += "\n---\n\n"
        
        # 각 섹션 포맷팅
        for idx, section in enumerate(sections, 1):
            markdown_str += f"## 섹션 {idx}: {section.name}\n\n"
            
            markdown_str += f"**설명**: {section.description}\n\n"
            
            if section.research:
                markdown_str += f"**조사 필요**: {section.research}\n\n"
            
            if section.content:
                markdown_str += f"### 내용\n\n{section.content}\n\n"
            else:
                markdown_str += "### 내용\n\n*아직 작성되지 않음*\n\n"
            
            markdown_str += "---\n\n"
        
        return markdown_str
    
    @classmethod
    def summarize_sections(cls, sections: List[Any]) -> Dict[str, Any]:
        """섹션의 요약 정보를 추출합니다.
        
        Args:
            sections (List[Any]): 요약할 섹션 목록
            
        Returns:
            Dict[str, Any]: 섹션 요약 정보
        """
        if not sections:
            return {"total_sections": 0, "completed_sections": 0, "sections": []}
        
        completed_sections = sum(1 for section in sections if section.content)
        section_summaries = [
            {
                "name": section.name,
                "is_completed": bool(section.content),
                "needs_research": bool(section.research)
            }
            for section in sections
        ]
        
        return {
            "total_sections": len(sections),
            "completed_sections": completed_sections,
            "completion_percentage": int((completed_sections / len(sections)) * 100),
            "sections": section_summaries
        }
