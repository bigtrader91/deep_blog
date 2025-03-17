"""
[경고] 이 모듈은 구조 재배치로 인해 deprecated 되었습니다.

새 경로: src.core.content.generator.svg

이 모듈은 하위 호환성을 위해 유지되며, 새 코드에서는 새 경로를 사용하세요.
"""

import warnings

warnings.warn(
    "src.generator.svg 모듈은 deprecated되었으며 src.core.content.generator.svg로 이동했습니다. "
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

from src.core.content.generator.svg.responsive_utils import (
    add_responsive_script,
    wrap_text
)

__all__ = [
    # 통합 인터페이스
    'DiagramType',
    'generate_diagram',
    
    # 반응형 유틸리티
    'add_responsive_script',
    'wrap_text',
    
    # 개별 다이어그램 생성 함수
    'generate_card_diagram',
    'generate_image_diagram'
] 