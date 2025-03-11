"""
통합된 다이어그램 생성 유틸리티 모듈입니다.

이 모듈은 card_diagram, image_diagram 모듈에 대한
통일된 인터페이스를 제공하며, 일관된 데이터 구조를 사용합니다.
모든 다이어그램은 반응형으로 설계되어 다양한 디바이스에서 적절하게 표시됩니다.
"""
from typing import Dict, List, Tuple, Optional, Any
import os
import logging
import importlib

# 로깅 설정
logger = logging.getLogger(__name__)

# DiagramType은 이제 __init__.py에서 정의됨


def validate_section_data(sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    데이터 섹션을 검증하고 필요한 경우 수정합니다.
    
    Args:
        sections: 검증할 섹션 리스트
        
    Returns:
        List[Dict[str, str]]: 검증된 섹션 리스트
    """
    valid_sections = []
    
    if not sections:
        # 기본 섹션 생성
        return [
            {"title": "섹션 1", "content": "내용이 없습니다."},
            {"title": "섹션 2", "content": "내용이 없습니다."}
        ]
    
    for i, section in enumerate(sections):
        valid_section = {}
        
        # title과 content 키가 있는지 확인
        if "title" not in section:
            valid_section["title"] = f"섹션 {i+1}"
            logger.warning(f"섹션 {i}에 title 키가 없습니다. 기본값으로 대체합니다.")
        else:
            valid_section["title"] = section["title"]
            
        if "content" not in section:
            # content 키가 없는 경우 다른 키에서 내용을 찾음
            content = section.get("description") or section.get("text") or "내용이 없습니다."
            valid_section["content"] = content
            logger.warning(f"섹션 {i}에 content 키가 없습니다. 대체값으로 {content[:20]}... 사용")
        else:
            valid_section["content"] = section["content"]
        
        valid_sections.append(valid_section)
    
    return valid_sections


def generate_diagram(
    diagram_type: str,
    main_title: str,
    sub_title_sections: List[Dict[str, str]],
    output_file: str,
    **kwargs
) -> str:
    """
    지정된 유형의 다이어그램을 생성합니다.
    
    Args:
        diagram_type: 다이어그램 유형 ("card", "image" 중 하나)
        main_title: 메인 타이틀
        sub_title_sections: 서브 타이틀 섹션 리스트
            각 항목은 {'title': '서브 타이틀', 'content': '내용'} 형태
        output_file: 출력 SVG 파일 경로
        **kwargs: 각 다이어그램 유형별 추가 매개변수
        
    Returns:
        str: 생성된 SVG 파일 경로
        
    Raises:
        ValueError: 지원되지 않는 다이어그램 유형이 지정된 경우
    """
    # 데이터 디렉토리 생성
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 데이터 유효성 검사 및 정제
    validated_sections = validate_section_data(sub_title_sections)
    
    # 섹션 수에 따라 다이어그램 유형 결정
    num_sections = len(validated_sections)
    
    # 항상 섹션 수에 따라 다이어그램 유형을 자동으로 결정
    auto_diagram_type = "card" if num_sections > 2 else "image"
    
    # 입력된 diagram_type과 자동 결정된 diagram_type이 다른 경우 로깅
    if diagram_type != auto_diagram_type:
        logger.info(f"입력된 다이어그램 유형({diagram_type})과 자동 결정된 유형({auto_diagram_type})이 다릅니다.")
        logger.info(f"섹션 수({num_sections})에 따라 {auto_diagram_type} 다이어그램으로 자동 변경합니다.")
    
    # 항상 자동 결정된 다이어그램 유형으로 설정
    diagram_type = auto_diagram_type
    
    # 각 다이어그램 모듈 동적 임포트
    try:
        if diagram_type == "card":
            # 모듈 동적 임포트
            from .card_diagram import generate_unified_card_diagram
            
            # 크기 파라미터 처리
            size = kwargs.pop('size', 800)
            width = kwargs.pop('width', size)
            height = kwargs.pop('height', None)
            
            return generate_unified_card_diagram(
                main_title=main_title,
                sub_title_sections=validated_sections,
                output_file=output_file,
                size=size,
                **kwargs
            )
            
        elif diagram_type == "image":
            from .image_diagram import generate_unified_image_diagram
            
            # 크기 파라미터 처리
            width = kwargs.pop('width', 800)
            height = kwargs.pop('height', 1000)
            
            return generate_unified_image_diagram(
                main_title=main_title,
                sub_title_sections=validated_sections,
                output_file=output_file,
                width=width,
                height=height,
                **kwargs
            )
            
    except Exception as e:
        logger.error(f"다이어그램 생성 중 오류 발생: {str(e)}")
        # 오류 발생 시에도 사용자에게 빈 파일보다 기본 다이어그램 제공
        fallback_output = output_file.replace(".svg", "_fallback.svg")
        try:
            # 폴백용 다이어그램 생성
            from .card_diagram import generate_unified_card_diagram
            
            return generate_unified_card_diagram(
                main_title="오류가 발생했습니다",
                sub_title_sections=[
                    {"title": "오류 내용", "content": str(e)},
                    {"title": "원본 타이틀", "content": main_title}
                ],
                output_file=fallback_output,
                background_color="#FFF0F0",  # 오류 표시를 위한 연한 빨간색 배경
            )
        except Exception:
            # 최후의 방법으로 간단한 SVG 파일 생성
            with open(fallback_output, 'w', encoding='utf-8') as f:
                f.write(f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
                    <rect x="0" y="0" width="800" height="600" fill="#FFF0F0"/>
                    <text x="400" y="300" text-anchor="middle" font-family="Arial" font-size="24" fill="#FF0000">
                        다이어그램 생성 중 오류가 발생했습니다
                    </text>
                </svg>''')
            return fallback_output 