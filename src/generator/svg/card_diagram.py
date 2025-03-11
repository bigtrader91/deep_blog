"""
카드 형태의 다이어그램을 생성하는 모듈입니다.

이 모듈은 구조화된 데이터를 카드 다이어그램으로 변환합니다.
각 카드는 베이지색 배경에 타이틀과 내용을 포함합니다.
픽사베이 API를 사용하여 이미지를 가져오고, CSS 및 JS로 동적 크기 조정을 지원합니다.
"""
import re
import svgwrite
import requests
import json
import os
import base64
import random
from urllib.parse import quote, urlparse
from svgwrite.container import Group
from svgwrite.shapes import Rect
from svgwrite.text import Text
from svgwrite.filters import Filter
import math
import textwrap
import logging
from typing import Optional, Tuple, List, Dict, Any

# responsive_utils.py에서 함수 가져오기
from .responsive_utils import add_responsive_script, wrap_text
# 공통 유틸리티 함수 가져오기
from .common_utils import (
    get_random_keywords, 
    get_pixabay_image, 
    get_keywords_from_sections,
    validate_image_url,
    RANDOM_KEYWORDS
)
logger = logging.getLogger(__name__)

def create_blur_filter(dwg: svgwrite.Drawing, filter_id: str, blur_amount: float = 5.0) -> Filter:
    """
    SVG 블러 필터를 생성합니다.
    
    Args:
        dwg: SVG 드로잉 객체
        filter_id: 필터 ID
        blur_amount: 블러 정도 (기본값: 5)
        
    Returns:
        Filter: 생성된 필터 객체
    """
    blur_filter = Filter(id=filter_id)
    blur_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation=blur_amount)
    
    # 필터를 SVG에 추가
    dwg.defs.add(blur_filter)
    
    return blur_filter

def create_text_with_wrapping(
    dwg: svgwrite.Drawing, 
    text: str, 
    x: float, 
    y: float, 
    width: float, 
    font_size: str, 
    text_anchor: str = "start", 
    font_family: str = "Arial", 
    font_weight: str = "normal", 
    fill: str = "#333333",
    line_height: float = 1.5,
    css_class: str = "diagram-text",
    max_lines: Optional[int] = None
) -> Tuple[Group, float]:
    """
    자동 줄바꿈 텍스트를 SVG에 추가하기 위해 Group을 생성

    Args:
        dwg: svgwrite.Drawing 객체
        text: 표시할 문자열
        x, y: 시작 좌표
        width: 텍스트 박스 최대 너비
        font_size: 폰트 크기 (예: "16px")
        text_anchor: 정렬
        font_family: 폰트
        font_weight: 폰트 두께
        fill: 글자 색상
        line_height: 줄 간격 비율
        css_class: CSS 클래스
        max_lines: 최대 줄 수 (None이면 제한 없음)
    Returns:
        (Group, float): (텍스트를 담은 그룹 객체, 실제로 차지한 높이)
    """
    # 폰트 크기 숫자만 추출
    import re
    font_size_num = int(re.search(r'\d+', font_size).group())

    # textwrap을 이용해 줄바꿈
    lines = wrap_text(text, int(width), font_size_num, max_lines) 

    text_group = dwg.g()
    line_spacing = font_size_num * line_height 
    for i, line_str in enumerate(lines):
        line_y = y + i * line_spacing
        t = dwg.text(
            line_str,
            insert=(x, line_y),
            text_anchor=text_anchor,
            font_family=font_family,
            font_weight=font_weight,
            font_size=font_size,
            fill=fill
        )
        t.attribs['class'] = css_class
        text_group.add(t)
    total_height = len(lines) * line_spacing if lines else 0

    return text_group, total_height

def add_responsive_scripts(dwg: svgwrite.Drawing) -> None:
    """
    SVG에 반응형 동작을 위한 기본 속성만 추가합니다.
    SVG 반응형 스크립트를 추가합니다.
    
    Args:
        dwg: SVG 드로잉 객체
    """
    # 향상된 반응형 스크립트 추가
    add_responsive_script(dwg)

def generate_card_diagram(
    data,
    output_file: str, 
    title: str = "골밀도란 무엇인가?",
    card_color: str = "#FEEBDC",
    title_color: str = "#333333",
    content_color: str = "#000000",
    size: int = 800,
    background_color: str = "#111111",
    background_image: Optional[str] = None,
    background_image_opacity: float = 0.2,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    header_image: Optional[str] = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 25,
    vertical_spacing: int = 8,
    add_responsive: bool = True,
    enable_card_backgrounds: bool = False,
    card_darkness: float = 0.7,
    card_blur: float = 3.0,
    # ↓↓↓↓↓ 새로 추가된 옵션 ↓↓↓↓↓
    equal_card_heights: bool = False,
    **kwargs
) -> str:
    """
    구조화된 데이터를 기반으로 카드 형태의 다이어그램을 생성합니다.

    Args:
        data: [{'title': '...', 'content': '...'}] 형식의 데이터 리스트
        output_file: 결과 SVG 파일 경로
        title: 다이어그램 상단 제목
        card_color: 카드 배경색
        title_color: 카드 제목 텍스트 색
        content_color: 카드 내용 텍스트 색
        size: SVG 가로/세로 크기 (1:1 비율)
        background_color: 전체 배경색
        background_image: 전체 배경 이미지 경로/URL
        background_image_opacity: 배경 이미지 투명도 (0~1)
        pixabay_query: 픽사베이 검색어
        pixabay_api_key: 픽사베이 API 키
        header_image: 상단 헤더 이미지 경로/URL
        header_image_height: 헤더 이미지 높이
        header_color: 헤더(타이틀) 텍스트 색
        rounded_corners: 카드 모서리 둥글기
        card_padding: 카드 내부 여백
        vertical_spacing: 카드 사이 세로 간격
        add_responsive: 반응형 스크립트 삽입 여부
        enable_card_backgrounds: 카드마다 개별 배경 이미지를 적용할지 여부
        card_darkness: 카드 내부 배경 어두운 오버레이 정도
        card_blur: 카드 배경(또는 전체 배경) 블러 정도
        equal_card_heights: True면 모든 카드 높이를 "가장 긴 카드"에 맞춰 균등하게.
                            False면 각 카드 내용에 맞게 유동적 높이.
    """

    if not data:
        raise ValueError("data가 비어 있습니다.")

    # 상단 헤더 계산
    top_offset = 100
    if header_image and not header_image.startswith("auto:") and header_image is not None:
        top_offset = header_image_height + 50
    else:
        top_offset = 75

    # 픽사베이 API를 통한 이미지 검색 (background_image가 없고 픽사베이 검색어와 API 키가 제공된 경우)
    pixabay_image_for_background = None
    if not background_image and pixabay_query and pixabay_api_key:
        # 섹션 데이터에서 키워드 추출
        if not pixabay_query.startswith("auto:"):
            search_query = pixabay_query
        else:
            # 'auto:' 접두사가 있으면 섹션 데이터에서 자동으로 키워드 추출
            search_query = get_keywords_from_sections(data)
            logging.info(f"섹션 데이터에서 추출한 키워드: {search_query}")
        
        # 픽사베이 이미지 검색
        pixabay_image_url = get_pixabay_image(search_query, pixabay_api_key, size, size)
        if pixabay_image_url:
            background_image = pixabay_image_url
            logging.info(f"픽사베이 이미지를 배경으로 사용합니다: {background_image}")

    import svgwrite
    dwg = svgwrite.Drawing(output_file, profile='full', size=('100%', '100%'))

    # 반응형
    if add_responsive:
        add_responsive_scripts(dwg)

    card_width = size * 0.85
    y_offset = top_offset + 40
    card_heights = []

    # (1) 카드 높이 계산 (임시)
    for card in data:
        card_title = card.get('title', '')
        card_content = card.get('content', '')

        content_width = card_width - (card_padding * 2)
        title_height = 40  # 카드 제목 영역 높이 (고정)

        # 내용 줄바꿈 높이 계산
        font_size_num = int(size * 0.02)
        lines = wrap_text(card_content, int(content_width), font_size_num)
        content_height = len(lines) * 30  # 대략 줄 하나당 30px로 잡음

        card_height = title_height + content_height + (card_padding * 2)
        card_heights.append(card_height)

    # (2) equal_card_heights 옵션 처리
    if equal_card_heights and card_heights:
        max_h = max(card_heights)
        for i in range(len(card_heights)):
            card_heights[i] = max_h

    # (3) 카드 전체 높이 합
    total_cards_height = sum(card_heights) + (vertical_spacing * (len(data) - 1))

    # (4) viewBox 설정 (SVG를 1:1로 유지)
    viewport_height = size
    dwg.attribs['viewBox'] = f"0 0 {size} {viewport_height}"

    # (5) 배경색 렌더링
    dwg.add(dwg.rect(insert=(0, 0), size=(size, viewport_height), fill=background_color))

    # (6) 전체 배경 이미지(옵션)
    if background_image:
        try:
            is_url = bool(urlparse(background_image).scheme)
            if not is_url and not os.path.exists(background_image):
                logging.warning(f"배경 이미지 파일이 존재하지 않습니다: {background_image}")
                background_image = None

            if background_image:
                bg_blur_filter_id = "bg-blur-filter"
                bg_blur_amount = card_blur
                bg_blur_filter = create_blur_filter(dwg, bg_blur_filter_id, bg_blur_amount)

                bg_group = dwg.g(opacity=background_image_opacity)
                if bg_blur_amount > 0:
                    bg_group.attribs["filter"] = f"url(#{bg_blur_filter_id})"

                bg_image = dwg.image(href=background_image, insert=(0, 0), size=(size, size))
                bg_group.add(bg_image)

                # 어두움 오버레이
                darkness_overlay = dwg.rect(
                    insert=(0, 0),
                    size=(size, viewport_height),
                    fill=background_color,
                    opacity=card_darkness
                )
                bg_group.add(darkness_overlay)

                dwg.add(bg_group)

        except Exception as e:
            logging.error(f"배경 이미지 적용 오류: {str(e)}")

    # (7) 헤더 이미지
    if header_image and not header_image.startswith("auto:") and header_image is not None:
        header_img = dwg.image(
            href=header_image,
            insert=(0, 0),
            size=(size, header_image_height)
        )
        dwg.add(header_img)
        overlay = dwg.rect(
            insert=(0, 0),
            size=(size, header_image_height),
            fill=background_color,
            opacity=0.3
        )
        dwg.add(overlay)

    # (8) 메인 타이틀
    title_y = 60 if not header_image else (header_image_height - 20)
    title_bg = dwg.rect(
        insert=(0, title_y - 50),  # 배경 상단 위치 조정 (텍스트보다 약간 위)
        size=(size, 120),          # 높이를 100px로 증가
        fill=background_color,
        opacity=0.5
    )
    dwg.add(title_bg)

    title_text = dwg.text(
        title,
        insert=(size/2, title_y), 
        text_anchor="middle",
        dominant_baseline="middle",
        font_family="Arial",
        font_weight="bold",
        font_size=f"{int(size*0.2)}px",  # 폰트 크기를 1.5배로 증가 (0.2 -> 0.3)
        fill=header_color
    )
    # title_text.attribs['class'] = 'diagram-title'
    title_text.attribs['class'] = 'diagram-main-title'  # <- 변경
    dwg.add(title_text)

    # (9) 카드 순차 렌더링
    for i, card in enumerate(data):
        card_title = card.get('title', f"카드 {i+1}")
        card_content = card.get('content', "")

        card_height = card_heights[i]
        card_x = (size - card_width) / 2

        # 그림자
        shadow = dwg.rect(
            insert=(card_x + 3, y_offset + 3),
            size=(card_width, card_height),
            rx=rounded_corners, ry=rounded_corners,
            fill="#000000",
            opacity=0.3
        )
        dwg.add(shadow)

        # 카드 본체
        card_group = dwg.g()
        card_rect = dwg.rect(
            insert=(card_x, y_offset),
            size=(card_width, card_height),
            rx=rounded_corners, ry=rounded_corners,
            fill=card_color,
            opacity=0.95
        )
        card_group.add(card_rect)

        # 카드별 배경 이미지 (옵션)
        if enable_card_backgrounds and pixabay_api_key:
            try:
                # 카드 제목이나 키워드 기반으로 이미지 검색
                search_terms = []
                
                # 먼저 키워드 확인
                if 'keywords' in card and isinstance(card['keywords'], list) and card['keywords']:
                    search_term = " ".join(card['keywords'][:3])  # 최대 3개 키워드만 사용
                else:
                    # 키워드가 없으면 제목 기반으로 랜덤 키워드 생성
                    search_term = get_random_keywords(card_title if i < 2 else None)
                
                card_bg_image_url = get_pixabay_image(search_term, pixabay_api_key, 
                                                    int(card_width), int(card_height), True)
                if card_bg_image_url:
                    card_clip_id = f"card-clip-{i}"
                    clip_path = dwg.defs.add(dwg.clipPath(id=card_clip_id))
                    clip_rect = dwg.rect(
                        insert=(card_x, y_offset),
                        size=(card_width, card_height),
                        rx=rounded_corners, ry=rounded_corners
                    )
                    clip_path.add(clip_rect)

                    bg_image_group = dwg.g(clip_path=f"url(#{card_clip_id})")
                    if card_blur > 0:
                        bg_image_group.attribs["filter"] = f"url(#blur-filter)"

                    card_bg_img = dwg.image(
                        href=card_bg_image_url,
                        insert=(card_x, y_offset),
                        size=(card_width, card_height)
                    )
                    bg_image_group.add(card_bg_img)

                    overlay = dwg.rect(
                        insert=(card_x, y_offset),
                        size=(card_width, card_height),
                        rx=rounded_corners, ry=rounded_corners,
                        fill=background_color,
                        opacity=card_darkness
                    )
                    bg_image_group.add(overlay)

                    card_group.add(bg_image_group)
            except Exception as e:
                logging.error(f"카드별 배경 이미지 오류: {str(e)}")

        dwg.add(card_group)

        # 카드 제목
        title_x = card_x + card_padding
        title_y_in_card = y_offset + card_padding + 20
        title_element = dwg.text(
            card_title,
            insert=(title_x, title_y_in_card),
            text_anchor="start",
            font_family="Arial",
            font_weight="bold",
            font_size=f"{int(size * 0.13)}px",  # 1.3배 증가 (0.1 * 1.3 = 0.13)
            fill=title_color
        )
        # title_element.attribs['class'] = 'diagram-title'
        title_element.attribs['class'] = 'diagram-card-title'  # <- 변경
        dwg.add(title_element)

        # 카드 내용 (줄바꿈)
        content_x = title_x
        content_y = title_y_in_card + 30
        content_width = card_width - (card_padding * 2)
        font_size = f"{int(size * 0.03)}px"  # 1.3배 증가 (0.022 * 1.3 = 0.0286)
        line_height = 1.2

        content_group, _ = create_text_with_wrapping(
            dwg=dwg,
            text=card_content,
            x=content_x,
            y=content_y,
            width=content_width,
            font_size=font_size,
            text_anchor="start",
            font_family="Arial",
            fill=content_color,
            css_class="diagram-text card-content",
            line_height=line_height,
            max_lines=None
        )
        dwg.add(content_group)

        # 다음 카드로 위치 이동
        y_offset += card_height + vertical_spacing

    dwg.save()
    return output_file

def generate_unified_card_diagram(
    main_title: str,
    sub_title_sections: List[Dict[str, Any]],
    output_file: str,
    card_color: str = "#FEEBDC",
    title_color: str = "#333333",
    content_color: str = "#000000",
    size: int = 800,
    background_color: str = "#111111",
    background_image: str = None,
    background_image_opacity: float = 0.2,
    pixabay_query: str = None,
    pixabay_api_key: str = None,
    header_image: str = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 25,
    vertical_spacing: int = 8,
    add_responsive: bool = True,
    enable_card_backgrounds: bool = False,
    card_darkness: float = 0.7,
    card_blur: float = 3.0,
    # ↓↓↓↓↓ 새로 추가된 옵션 ↓↓↓↓↓
    equal_card_heights: bool = False
) -> str:
    """
    통합된 인터페이스로 카드 다이어그램을 생성합니다.
    (generate_card_diagram 함수를 내부에서 호출)

    Args:
        main_title: 다이어그램 메인 타이틀
        sub_title_sections: [{'title': '...', 'content': '...', 'keywords': [...]}] 형식의 섹션들
        output_file: 결과 SVG 파일 경로
        ...
        equal_card_heights: True면 모든 카드 높이를 균일화
    """
    # 키워드 처리
    data = []
    for section in sub_title_sections:
        section_data = {
            'title': section.get('title', ''),
            'content': section.get('content', ''),
        }
        # keywords 필드가 있으면 추가
        if 'keywords' in section:
            section_data['keywords'] = section['keywords']
        data.append(section_data)
        
    logger.info(f"최종 픽사베이 검색어: {pixabay_query}")

    # 픽사베이 검색어가 'auto:'로 시작하면 섹션에서 키워드를 추출
    if pixabay_query == 'auto:' and pixabay_api_key:
        # 섹션 데이터에서 키워드 추출
        keywords_query = get_keywords_from_sections(sub_title_sections)
        pixabay_query = keywords_query
        print(f"섹션 데이터에서 추출한 키워드: {keywords_query}")

    return generate_card_diagram(
        data=data,
        output_file=output_file,
        title=main_title,
        card_color=card_color,
        title_color=title_color,
        content_color=content_color,
        size=size,
        background_color=background_color,
        background_image=background_image,
        background_image_opacity=background_image_opacity,
        pixabay_query=pixabay_query,
        pixabay_api_key=pixabay_api_key,
        header_image=header_image,
        header_image_height=header_image_height,
        header_color=header_color,
        rounded_corners=rounded_corners,
        card_padding=card_padding,
        vertical_spacing=vertical_spacing,
        add_responsive=add_responsive,
        enable_card_backgrounds=enable_card_backgrounds,
        card_darkness=card_darkness,
        card_blur=card_blur,
        equal_card_heights=equal_card_heights
    )

if __name__ == "__main__":
    # 테스트 예시
    test_data = [
        {"title": "골밀도 검사 필요성", "content": "골밀도 검사는 ..."},
        {"title": "검사 방법", "content": "DEXA(이중 에너지 X선 ..."},
        {"title": "결과 해석", "content": "T-점수가 -1.0 이상이면 정상 ..."}
    ]
    os.makedirs("./outputs", exist_ok=True)
    result_path = generate_unified_card_diagram(
        main_title="골밀도 검사의 중요성",
        sub_title_sections=test_data,
        output_file="./outputs/card_diagram_test.svg",
        equal_card_heights=True  # True로 하면 모든 카드가 '가장 긴 카드' 높이에 맞춰집니다
    )
    print(f"카드 다이어그램 생성 완료: {result_path}")
