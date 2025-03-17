"""
다양한 SVG 다이어그램 생성 모듈을 제공하는 패키지입니다.

이 패키지는 다음과 같은 다이어그램 유형을 지원합니다:
- 카드 다이어그램: 카드 형태의 정보 표시 다이어그램 (3개 이상의 섹션에 적합)
- 이미지 다이어그램: 상단 이미지와 하단 텍스트로 구성된 다이어그램 (2개 이하의 섹션에 적합)

모든 다이어그램은 통일된 인터페이스를 제공하며, 메인 타이틀과 서브 섹션으로 구성됩니다.
모든 다이어그램은 반응형으로 설계되어 다양한 화면 크기와 기기에서 적절하게 표시됩니다.
"""

# 먼저 타입 정의 가져오기
from typing import Literal

# DiagramType 정의
DiagramType = Literal["card", "image"]

# 반응형 유틸리티
from .responsive_utils import add_responsive_script, wrap_text

# 다이어그램 생성 코어 함수
from .diagram_utils import generate_diagram

# 개별 다이어그램 생성 함수
from .card_diagram import generate_unified_card_diagram as generate_card_diagram
from .image_diagram import generate_unified_image_diagram as generate_image_diagram

__all__ = [
    # 통합 인터페이스
    'DiagramType',
    'generate_diagram',
    
    # 반응형 유틸리티
    'add_responsive_script',
    'wrap_text',
    
    # 개별 다이어그램 생성 함수 (직관적인 이름으로 제공)
    'generate_card_diagram',
    'generate_image_diagram'
] 