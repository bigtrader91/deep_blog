# src.generator.svg.responsive_utils.py

"""
SVG 다이어그램의 반응형 기능을 제공하는 유틸리티 모듈

이 모듈은 SVG 다이어그램이 다양한 디바이스와 화면 크기에서 
적절하게 표시되도록 하는 반응형 스타일을 제공합니다.
"""
import re
from typing import Tuple, Dict, List, Optional


def add_responsive_script(dwg: 'svgwrite.Drawing') -> None:
    """
    SVG에 반응형 동작을 위한 CSS 스타일을 추가합니다.
    
    이 함수는 SVG가 다양한 화면 크기와 기기에서 적절하게 표시되도록 CSS를 활용합니다.
    JavaScript 대신 CSS와 SVG 속성을 사용하여 반응형 기능을 제공합니다.
    
    Args:
        dwg: SVG 드로잉 객체
    """
    # 기본 반응형 속성 설정
    dwg.attribs['preserveAspectRatio'] = 'xMidYMid meet'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'
    dwg.attribs['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
    
    # SVG 크기가 명시적으로 설정되지 않은 경우 viewBox 확인 및 설정
    if 'viewBox' not in dwg.attribs:
        # 기본 크기 정보 가져오기
        size = dwg.attribs.get('size', '800 800').split()
        width = size[0] if len(size) > 0 else 800
        height = size[1] if len(size) > 1 else width
        dwg.attribs['viewBox'] = f"0 0 {width} {height}"
    
    # SVG를 100% 크기로 설정하여 컨테이너에 맞추도록 함
    dwg.attribs['width'] = '100%'
    # height를 'auto'가 아닌 '100%'로 설정 (SVG 속성은 'auto'를 허용하지 않음)
    dwg.attribs['height'] = '100%'
    
    # 향상된 CSS로 반응형 스타일 추가
    style = dwg.style("""
        :root {
            --base-font-size: 16px;
        }
        
        svg {
            max-width: 100%;
            height: auto; /* CSS에서는 auto 사용 가능 */
            display: block; /* 불필요한 여백 방지 */
        }
        
        .diagram-main-title {
            font-family: Arial, sans-serif;
            font-weight: bold;
            font-size: 42px;
        }

        .diagram-card-title {
            font-family: Arial, sans-serif;
            font-weight: bold;
            font-size: 32px;
        }

        .card-content {
            font-family: Arial, sans-serif;
            font-size: 24px;
        }
        
        .diagram-text {
            font-size: 16px;
        }
        
        .diagram-title {
            font-size: 24px;
        }
        
        /* 반응형 폰트 크기 */
        @media screen and (max-width: 800px) {
            .diagram-main-title { font-size: 36px; }
            .diagram-card-title { font-size: 28px; }
            .diagram-text { font-size: 14px; }
            .diagram-title { font-size: 22px; }
            .card-content { font-size: 20px; }
        }
        
        @media screen and (max-width: 600px) {
            .diagram-main-title { font-size: 30px; }
            .diagram-card-title { font-size: 24px; }
            .diagram-text { font-size: 12px; }
            .diagram-title { font-size: 20px; }
            .card-content { font-size: 16px; }
        }
        
        @media screen and (max-width: 400px) {
            .diagram-main-title { font-size: 24px; }
            .diagram-card-title { font-size: 20px; }
            .diagram-text { font-size: 10px; }
            .diagram-title { font-size: 18px; }
            .card-content { font-size: 14px; }
        }
    """)
    dwg.add(style)
    
    # JavaScript 사용하지 않음 - CSS와 SVG의 기본 속성만 활용


def create_simple_svg_fallback(output_file: str, error_message: str, main_title: str = "오류 발생") -> str:
    """
    오류 발생 시 간단한 SVG 파일을 생성합니다.
    
    Args:
        output_file: 출력 파일 경로
        error_message: 오류 메시지
        main_title: 메인 타이틀
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 출력 디렉토리 생성
    import os
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 간단한 SVG 파일 생성
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="800" height="600" viewBox="0 0 800 600">
    <rect x="0" y="0" width="800" height="600" fill="#FFF0F0"/>
    <text x="400" y="100" text-anchor="middle" font-family="Arial" font-size="24" fill="#FF0000">{main_title}</text>
    <text x="400" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#000000">{error_message}</text>
</svg>''')
    
    return output_file


def wrap_text(
    text: str, 
    width: int, 
    font_size: int = 16, 
    max_lines: Optional[int] = None,
    diagram_type: str = 'card'  # 'card' 또는 'image'
) -> List[str]:
    """
    텍스트를 주어진 너비에 맞게 줄바꿈합니다.
    CSS 기반 반응형에서도 적절하게 작동하도록 개선됨.
    
    Args:
        text: 줄바꿈할 텍스트
        width: 최대 너비 (픽셀)
        font_size: 폰트 크기 (픽셀)
        max_lines: 최대 줄 수 (None이면 제한 없음)
        diagram_type: 다이어그램 타입 ('card' 또는 'image')
        
    Returns:
        List[str]: 줄바꿈된 텍스트 라인 목록
    """
    # 다이어그램 타입에 따른 기본 계수 설정
    base_width_factor = 0.25 if diagram_type == 'card' else 0.25
    
    # 화면 크기에 따른 조정 계수 시뮬레이션 (CSS의 미디어 쿼리와 유사한 효과)
    # 이 부분은 SVG 생성 시점에 화면 크기를 알 수 없기 때문에 가정에 기반함
    if width <= 400:
        # 모바일 화면용 (작은 화면에서는 더 짧은 줄로 분리)
        width_factor = base_width_factor * 1.2
    elif width <= 600:
        # 태블릿 화면용
        width_factor = base_width_factor * 1.1
    else:
        # 데스크톱 화면용
        width_factor = base_width_factor
    
    # 더 정확한 줄바꿈을 위해 폰트 크기 고려
    # 폰트 크기가 작을수록 한 줄에 더 많은 글자가 들어감
    font_adjust = 16 / max(font_size, 1)  # 기준 폰트 사이즈가 16일 때
    
    # 최종 문자 수 계산 (폰트 크기와 다이어그램 타입에 따라 조정)
    chars_per_line = int(width / (font_size * width_factor) * font_adjust)
    
    # 최소값 보장 (너무 짧은 줄은 방지)
    chars_per_line = max(chars_per_line, 15)
    
    # 텍스트 줄바꿈
    import textwrap
    lines = textwrap.wrap(text, width=chars_per_line)
    
    # 최대 줄 수 제한
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines-1]
        # 생략 표시 추가
        if lines:
            lines[-1] = lines[-1].rstrip() + "..."
    
    return lines 