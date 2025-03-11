# src.generator.svg.image_diagram.py
"""
이미지-텍스트 레이아웃 형태의 SVG 다이어그램 생성기

이 모듈은 상단 40%에 이미지를, 하단 60%에 타이틀과 설명을 배치하는
깔끔한 SVG 다이어그램을 생성합니다.
"""
from typing import Dict, List, Tuple, Optional, Any
import os
import re
import svgwrite
import requests
import textwrap
import logging
from urllib.parse import quote
from svgwrite.container import Group
from svgwrite.text import Text
import random

# responsive_utils.py에 정의된 함수들을 그대로 사용한다고 가정
from .responsive_utils import add_responsive_script, wrap_text

# 공통 유틸 함수 (픽사베이 이미지 검색 등)
from .common_utils import (
    get_pixabay_image,
    get_keywords_from_sections,
    validate_image_url
)

# 로깅 설정
logger = logging.getLogger(__name__)


def add_responsive_attributes(dwg: svgwrite.Drawing) -> None:
    """
    SVG 드로잉 객체에 반응형 속성과 스타일을 추가합니다.
    
    Args:
        dwg: SVG 드로잉 객체
    """
    # 기본 SVG 속성 설정
    dwg.attribs['preserveAspectRatio'] = 'xMidYMid meet'
    dwg.attribs['xmlns'] = 'http://www.w3.org/2000/svg'
    dwg.attribs['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
    
    # 이미지 다이어그램 전용 스타일 추가
    style = dwg.style("""
        .image-diagram-title {
            font-family: 'Noto Sans KR', Arial, sans-serif;
            font-weight: bold;
            font-size: 48px; /* 메인 타이틀용 기본 크기 증가 */
        }
        .image-diagram-section-title {
            font-family: 'Noto Sans KR', Arial, sans-serif;
            font-weight: bold;
            font-size: 32px; /* 섹션 제목용 기본 크기 증가 */
        }
        .image-diagram-content {
            font-family: 'Noto Sans KR', Arial, sans-serif;
            font-size: 24px; /* 섹션 내용용 기본 크기 증가 */
        }
        @media screen and (max-width: 600px) {
            .image-diagram-title { font-size: 36px; }
            .image-diagram-section-title { font-size: 28px; }
            .image-diagram-content { font-size: 20px; }
        }
        @media screen and (max-width: 400px) {
            .image-diagram-title { font-size: 32px; }
            .image-diagram-section-title { font-size: 24px; }
            .image-diagram-content { font-size: 18px; }
        }
    """)
    dwg.add(style)
    
    # 반응형 크기 조절 스크립트 추가
    script = dwg.script(content="""
        (function() {
            var svg = document.currentScript.parentNode;
            
            function resizeImageDiagram() {
                var container = svg.parentNode;
                if (!container) return;
                
                var containerWidth = container.clientWidth;
                if (containerWidth <= 0) return;
                
                // SVG 크기를 컨테이너에 맞게 조절 (1:1 비율 유지)
                svg.setAttribute('width', containerWidth);
                svg.setAttribute('height', containerWidth);
                
                // 화면 크기에 따른 스케일 계산
                var scale = containerWidth < 400 ? 0.7 : 
                           containerWidth < 600 ? 0.85 : 1;
                
                // 폰트 크기 동적 조절
                var titles = svg.getElementsByClassName('image-diagram-title');
                var sectionTitles = svg.getElementsByClassName('image-diagram-section-title');
                var contents = svg.getElementsByClassName('image-diagram-content');
                
                function adjustFontSize(elements, baseSize) {
                    for (var i = 0; i < elements.length; i++) {
                        elements[i].style.fontSize = (baseSize * scale) + 'px';
                    }
                }
                
                adjustFontSize(titles, 48);
                adjustFontSize(sectionTitles, 32);
                adjustFontSize(contents, 24);
            }
            
            window.addEventListener('resize', resizeImageDiagram);
            if (document.readyState === 'complete') {
                resizeImageDiagram();
            } else {
                window.addEventListener('load', resizeImageDiagram);
            }
        })();
    """, type="text/javascript")
    dwg.add(script)


def create_wrapped_text(
    dwg: svgwrite.Drawing, 
    text: str, 
    x: float, 
    y: float, 
    width: float, 
    font_size: str, 
    text_anchor: str = "start", 
    font_family: str = "Arial", 
    font_weight: str = "normal", 
    fill: str = "#555555",
    line_height: float = 1.5,
    css_class: str = "diagram-text"
) -> Tuple[Group, float]:
    """
    자동 줄바꿈이 적용된 텍스트 그룹을 생성합니다.
    
    Args:
        dwg: SVG 드로잉 객체
        text: 표시할 텍스트
        x: 시작 x 좌표
        y: 시작 y 좌표
        width: 텍스트 영역 너비
        font_size: 폰트 크기 (예: "18px")
        text_anchor: 텍스트 정렬 방식
        font_family: 폰트 패밀리
        font_weight: 폰트 두께
        fill: 텍스트 색상
        line_height: 줄 간격 비율
        css_class: CSS 클래스 이름
        
    Returns:
        Tuple[Group, float]: (텍스트 그룹, 총 높이)
    """
    font_size_num = int(re.search(r'\d+', font_size).group())
    lines = wrap_text(text, width, font_size_num, diagram_type='image')
    line_spacing = font_size_num * line_height
    
    text_group = Group()
    for i, line_str in enumerate(lines):
        line_y = y + (i * line_spacing)
        text_element = Text(
            line_str,
            insert=(x, line_y),
            text_anchor=text_anchor,
            font_family=font_family,
            font_weight=font_weight,
            font_size=font_size,
            fill=fill
        )
        text_element.attribs['class'] = css_class
        text_group.add(text_element)
    
    total_height = len(lines) * line_spacing if lines else 0
    return text_group, total_height


def generate_split_layout(
    title: str,
    descriptions: List[Dict[str, Any]],
    output_file: str,
    header_image: Optional[str] = None,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    width: int = 800,
    height: int = 800,
    background_color: str = "#FFFFFF",
    title_color: str = "#333333",
    description_color: str = "#555555",
    add_responsive: bool = True
) -> str:
    """
    이미지와 텍스트를 결합한 SVG 다이어그램을 생성합니다.
    상단 40%는 이미지, 하단 60%는 텍스트로 구성됩니다.
    1-2개의 섹션에 최적화되어 있습니다.
    """
    if len(descriptions) > 2:
        logger.warning("이미지 다이어그램은 1-2개의 섹션에 최적화되어 있습니다.")
    
    # 테마 선택 (랜덤)
    is_dark_theme = random.choice([True, False])
    if is_dark_theme:
        background_color = "#111111"
        title_color = "#FFFFFF"
        description_color = "#EEEEEE"
    else:
        background_color = "#FFFFFF"
        title_color = "#333333"
        description_color = "#555555"
    
    dwg = svgwrite.Drawing(output_file, size=(width, width))
    dwg.attribs['viewBox'] = f"0 0 {width} {width}"
    
    if add_responsive:
        add_responsive_attributes(dwg)
    
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill=background_color))
    
    # 상단 이미지 영역 (40%)
    image_height = int(width * 0.4)
    if not header_image and pixabay_api_key and pixabay_query:
        all_keywords = []
        for desc in descriptions:
            if 'keywords' in desc and isinstance(desc['keywords'], list):
                all_keywords.extend(desc['keywords'][:2])
        search_query = pixabay_query
        if all_keywords:
            unique_keywords = list(set(all_keywords))[:2]
            search_query = f"{pixabay_query}, {', '.join(unique_keywords)}"
            logger.info(f"검색 쿼리: {search_query}")
        header_image = get_pixabay_image(search_query, pixabay_api_key, width, image_height)
    
    if header_image:
        if not validate_image_url(header_image):
            logger.warning(f"유효하지 않은 이미지 URL: {header_image}")
        else:
            header_img = dwg.image(
                href=header_image,
                insert=(0, 0),
                size=(width, image_height)
            )
            header_img['preserveAspectRatio'] = 'xMidYMid slice'
            dwg.add(header_img)
            
            gradient = dwg.linearGradient(
                id='image_overlay',
                start=(0, 0),
                end=(0, 1)
            )
            gradient.add_stop_color(offset='0%', color='#000000', opacity=0.0)
            gradient.add_stop_color(offset='100%', color='#000000', opacity=random.uniform(0.1, 0.3))
            dwg.defs.add(gradient)
            dwg.add(dwg.rect(
                insert=(0, 0),
                size=(width, image_height),
                fill='url(#image_overlay)'
            ))
    
    # 제목 영역 – 제목을 가운데 정렬하도록 text_anchor="middle" 사용
    title_y = image_height + 70
    title_element = dwg.text(
        title,
        insert=(width/2, title_y),
        font_family="'Noto Sans KR', Arial, sans-serif",
        font_size="48px",  # 폰트 크기 증가
        font_weight="bold",
        fill=title_color,
        text_anchor="middle"  # 가운데 정렬
    )
    title_element.attribs['class'] = 'image-diagram-title'
    dwg.add(title_element)
    
    # 본문 영역
    content_start_y = title_y + 60
    y_offset = content_start_y
    padding = 40
    section_width = width - (padding * 2)
    
    # 원형 번호 배지 색상 (테마에 따라)
    mint_green = "#98D8C8" if not is_dark_theme else "#4A9B8C"
    
    for i, item in enumerate(descriptions):
        desc_title = item.get('title', '')
        desc_text = item.get('content', '')
        number = str(i + 1)
        
        circle_radius = 15
        circle_x = padding
        circle_y = y_offset + circle_radius
        dwg.add(dwg.circle(
            center=(circle_x, circle_y),
            r=circle_radius,
            fill=mint_green
        ))
        dwg.add(dwg.text(
            number,
            insert=(circle_x, circle_y + 6),
            font_family="'Noto Sans KR', Arial, sans-serif",
            font_size="20px",  # 폰트 크기 증가
            font_weight="bold",
            fill="white",
            text_anchor="middle"
        ))
        
        title_x = padding + (circle_radius * 2) + 10
        sub_title_font_size = 32  # 폰트 크기 증가
        section_title = dwg.text(
            desc_title,
            insert=(title_x, y_offset + sub_title_font_size),
            font_family="'Noto Sans KR', Arial, sans-serif",
            font_size=f"{sub_title_font_size}px",
            font_weight="bold",
            fill=title_color
        )
        section_title.attribs['class'] = 'image-diagram-section-title'
        dwg.add(section_title)
        
        desc_font_size = 24  # 폰트 크기 증가
        y_offset_content = y_offset + sub_title_font_size + 30
        
        desc_group, desc_height = create_wrapped_text(
            dwg,
            desc_text,
            title_x,
            y_offset_content,
            int(section_width * 0.5),
            f"{desc_font_size}px",
            "start",
            "'Noto Sans KR', Arial, sans-serif",
            "normal",
            description_color,
            line_height=1.5,
            css_class="image-diagram-content"
        )
        dwg.add(desc_group)
        
        y_offset += desc_height + 100
    
    if add_responsive:
        add_responsive_script(dwg)
    
    dwg.save()
    return output_file


def generate_image_text_layout(
    title: str,
    content_items: List[Dict[str, str]],
    output_file: str,
    image_url: Optional[str] = None,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    width: int = 800,
    height: int = 1200
) -> str:
    background_color = "#FFFFFF"
    title_color = "#333333"
    description_color = "#555555"
    
    return generate_split_layout(
        title=title,
        descriptions=content_items,
        output_file=output_file,
        header_image=image_url,
        pixabay_query=pixabay_query,
        pixabay_api_key=pixabay_api_key,
        width=width,
        height=height,
        background_color=background_color,
        title_color=title_color,
        description_color=description_color
    )


def generate_unified_image_diagram(
    main_title: str,
    sub_title_sections: List[Dict[str, Any]],
    output_file: str,
    header_image: Optional[str] = None,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    width: int = 800,
    height: int = 800,
    background_color: str = "#FFFFFF",
    title_color: str = "#333333",
    description_color: str = "#555555",
    add_responsive: bool = True
) -> str:
    if len(sub_title_sections) > 2:
        logger.warning("이미지 다이어그램은 1-2개의 섹션에 최적화되어 있습니다.")
    logger.info(f"최종 픽사베이 검색어: {pixabay_query}")
    if pixabay_query == 'auto:' and pixabay_api_key:
        keywords_query = get_keywords_from_sections(sub_title_sections)
        pixabay_query = keywords_query
        logger.info(f"섹션 데이터에서 추출한 키워드: {keywords_query}")
    
    descriptions = []
    for section in sub_title_sections:
        desc = {
            'title': section.get('title', ''),
            'content': section.get('content', ''),
            'keywords': section.get('keywords', [])
        }
        descriptions.append(desc)
    
    return generate_split_layout(
        title=main_title,
        descriptions=descriptions,
        output_file=output_file,
        header_image=header_image,
        pixabay_query=pixabay_query,
        pixabay_api_key=pixabay_api_key,
        width=width,
        height=width,  # 1:1 비율 유지
        background_color=background_color,
        title_color=title_color,
        description_color=description_color,
        add_responsive=add_responsive
    )


if __name__ == "__main__":
    test_data = [
        {
            "title": "진실 은폐 의혹",
            "content": "국정조사 중 진실을 덮고 국민을 속이려 했다는 이유로 고발.",
            "keywords": ["진실", "은폐", "국정조사"]
        },
        {
            "title": "거짓 공문서 제출",
            "content": "압수·통신 영장 관련 허위 공문서 제출 및 청문회 위증 주장.",
            "keywords": ["공문서", "위증", "청문회"]
        }
    ]
    
    os.makedirs("./outputs", exist_ok=True)
    
    output_path = generate_unified_image_diagram(
        main_title="여당, 공수처장 검찰 고발! 왜?",
        sub_title_sections=test_data,
        output_file="./outputs/image_diagram_test.svg",
        pixabay_query="business meeting", 
        pixabay_api_key="YOUR_API_KEY_HERE",
        width=800,
        height=800,
        background_color="#FFFFFF",
        add_responsive=True
    )
    
    print(f"이미지 다이어그램 생성 완료: {output_path}")
