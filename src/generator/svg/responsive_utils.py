"""
SVG 다이어그램의 반응형 기능을 제공하는 유틸리티 모듈

이 모듈은 SVG 다이어그램이 다양한 디바이스와 화면 크기에서 
적절하게 표시되도록 하는 반응형 스크립트 및 스타일을 제공합니다.
"""
import re
from typing import Tuple, Dict, List, Optional


def add_responsive_script(dwg: 'svgwrite.Drawing') -> None:
    """
    SVG에 반응형 동작을 위한 스크립트와 스타일을 추가합니다.
    
    이 함수는 SVG가 다양한 화면 크기와 기기에서 적절하게 표시되도록 합니다.
    
    Args:
        dwg: SVG 드로잉 객체
    """
    # 기본 반응형 속성 설정
    dwg.attribs['preserveAspectRatio'] = 'xMidYMid meet'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'
    dwg.attribs['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
    
    # 스타일 추가 방식 변경 - 객체 생성 없이 직접 추가
    style = dwg.style("""
        .diagram-text { 
            font-family: Arial, sans-serif; 
            font-size: 16px;
        }
        .diagram-title { 
            font-family: Arial, sans-serif; 
            font-weight: bold;
            font-size: 24px;
        }
        .card-content { 
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        @media screen and (max-width: 600px) {
            .diagram-text { font-size: 12px; }
            .diagram-title { font-size: 20px; }
            .card-content { font-size: 11px; }
        }
        @media screen and (max-width: 400px) {
            .diagram-text { font-size: 10px; }
            .diagram-title { font-size: 18px; }
            .card-content { font-size: 9px; }
        }
    """)
    dwg.add(style)
    
    # 스크립트 요소 추가 (SVG 크기 자동 조절)
    script = dwg.script(content="""
        (function() {
            // SVG 요소 참조
            var svg = document.currentScript.parentNode;
            
            // 반응형 크기 조절 함수
            function resizeSVG() {
                var container = svg.parentNode;
                if (container) {
                    var containerWidth = container.clientWidth;
                    if (containerWidth > 0) {
                        // 컨테이너 너비에 맞게 SVG 크기 조절
                        svg.setAttribute('width', containerWidth);
                        var viewBox = svg.getAttribute('viewBox').split(' ');
                        var aspectRatio = viewBox[2] / viewBox[3];
                        svg.setAttribute('height', containerWidth / aspectRatio);
                        
                        // 화면 크기에 따른 폰트 크기 조절
                        var scale = containerWidth < 400 ? 0.7 : 
                                  containerWidth < 600 ? 0.8 : 1;
                        
                        // 텍스트 요소들의 폰트 크기 고정 비율로 조절
                        var texts = svg.getElementsByClassName('diagram-text');
                        for (var i = 0; i < texts.length; i++) {
                            // 기본 클래스별 크기 사용
                            var baseSize = 16; // diagram-text 기본 크기
                            texts[i].setAttribute('font-size', (baseSize * scale) + 'px');
                        }
                        
                        var titles = svg.getElementsByClassName('diagram-title');
                        for (var i = 0; i < titles.length; i++) {
                            var baseSize = 24; // diagram-title 기본 크기
                            titles[i].setAttribute('font-size', (baseSize * scale) + 'px');
                        }
                        
                        var cardTexts = svg.getElementsByClassName('card-content');
                        for (var i = 0; i < cardTexts.length; i++) {
                            var baseSize = 14; // card-content 기본 크기
                            cardTexts[i].setAttribute('font-size', (baseSize * scale) + 'px');
                        }
                    }
                }
            }
            
            // 초기 로드 및 창 크기 변경 시 크기 조절
            window.addEventListener('resize', resizeSVG);
            if (document.readyState === 'complete') {
                resizeSVG();
            } else {
                window.addEventListener('load', resizeSVG);
            }
        })();
    """, type="text/javascript")
    dwg.add(script)


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
    max_lines: Optional[int] = None
) -> List[str]:
    """
    텍스트를 주어진 너비에 맞게 줄바꿈합니다.
    
    Args:
        text: 줄바꿈할 텍스트
        width: 최대 너비 (픽셀)
        font_size: 폰트 크기 (픽셀)
        max_lines: 최대 줄 수 (None이면 제한 없음)
        
    Returns:
        List[str]: 줄바꿈된 텍스트 라인 목록
    """
    # 대략적인 문자 수 계산 (폰트 크기에 따라 조정)
    # 한글은 영문보다 더 많은 공간을 차지하므로 계수를 0.8로 증가
    chars_per_line = int(width / (font_size * 1.2))
    
    # 텍스트 줄바꿈
    import textwrap
    lines = textwrap.wrap(text, width=chars_per_line)
    
    # 최대 줄 수 제한
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines-1]
        # 생략 표시 추가
        if lines:
            lines.append(lines[-1] + "...")
    
    return lines 