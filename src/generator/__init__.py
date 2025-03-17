"""
[경고] 이 모듈은 구조 재배치로 인해 deprecated 되었습니다.

새 경로: src.core.content.generator

이 모듈은 하위 호환성을 위해 유지되며, 새 코드에서는 새 경로를 사용하세요.
"""

import warnings

warnings.warn(
    "src.generator 모듈은 deprecated되었으며 src.core.content.generator로 이동했습니다. "
    "새 코드에서는 새 경로를 사용하세요.",
    DeprecationWarning,
    stacklevel=2
)

# 하위 호환성을 위해 새 위치에서 모듈 가져오기
from src.core.content.generator.svg import (
    DiagramType,
    generate_diagram,
    generate_card_diagram,
    generate_image_diagram
)

from src.core.content.generator.text.title_generator import generate_title
from src.core.content.generator.text.diagram_generator import (
    generate_diagram_from_text,
    parse_and_render_diagram
)
from src.core.content.generator.text.select_diagram import (
    select_diagram,
    select_appropriate_diagram,
    DiagramResult,
    DiagramContent
)

__all__ = [
    # 다이어그램 타입
    'DiagramType',
    'DiagramResult',
    'DiagramContent',
    
    # 다이어그램 생성
    'generate_diagram',
    'generate_card_diagram',
    'generate_image_diagram',
    
    # 다이어그램 텍스트 생성
    'generate_diagram_from_text',
    'parse_and_render_diagram',
    'select_diagram',
    'select_appropriate_diagram',
    
    # 타이틀 생성
    'generate_title'
] 