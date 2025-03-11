"""
카드 형태의 다이어그램을 생성하는 모듈입니다.

이 모듈은 구조화된 데이터를 카드 다이어그램으로 변환합니다.
각 카드는 베이지색 배경에 타이틀과 내용을 포함합니다.
픽사베이 API를 사용하여 이미지를 가져오고, CSS 및 JS로 동적 크기 조정을 지원합니다.
"""
from typing import Dict, List, Tuple, Optional, Any
import re
import svgwrite
import requests
import json
import os
import base64
from urllib.parse import quote
from svgwrite.container import Group
from svgwrite.shapes import Circle, Rect, Line
from svgwrite.path import Path
from svgwrite.text import Text
from svgwrite.filters import Filter
import math
import textwrap

from .responsive_utils import add_responsive_script, wrap_text

def get_pixabay_image(query: str, api_key: str, width: int = 800, height: int = 400) -> Optional[str]:
    """
    픽사베이 API를 사용하여 이미지를 검색하고 URL을 반환합니다.
    
    Args:
        query: 검색어
        api_key: 픽사베이 API 키
        width: 요청할 이미지 너비
        height: 요청할 이미지 높이
        
    Returns:
        Optional[str]: 이미지 URL 또는 실패 시 None
    """
    try:
        # URL 인코딩
        encoded_query = quote(query)
        url = f"https://pixabay.com/api/?key={api_key}&q={encoded_query}&image_type=photo&orientation=horizontal&per_page=3"
        
        response = requests.get(url)
        data = response.json()
        
        if data['totalHits'] > 0:
            # 첫 번째 이미지 URL 반환
            return data['hits'][0]['largeImageURL']
        else:
            return None
    except Exception as e:
        print(f"픽사베이 API 오류: {str(e)}")
        return None

def add_responsive_scripts(dwg: svgwrite.Drawing) -> None:
    """
    SVG에 반응형 동작을 위한 기본 속성만 추가합니다.
    SVG 반응형 스크립트를 추가합니다.
    
    Args:
        dwg: SVG 드로잉 객체
    """
    # 향상된 반응형 스크립트 추가
    add_responsive_script(dwg)

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
    자동 줄바꿈이 적용된 텍스트 그룹을 생성합니다.
    
    Args:
        dwg: SVG 드로잉 객체
        text: 표시할 텍스트
        x: 시작 x 좌표
        y: 시작 y 좌표
        width: 텍스트 영역 너비
        font_size: 폰트 크기 (예: "16px")
        text_anchor: 텍스트 정렬 방식
        font_family: 폰트 패밀리
        font_weight: 폰트 두께
        fill: 텍스트 색상
        line_height: 줄 간격 비율
        css_class: CSS 클래스 이름
        max_lines: 최대 줄 수 (None이면 제한 없음)
        
    Returns:
        Tuple[Group, float]: 텍스트 그룹과 총 높이
    """
    # 폰트 크기에서 숫자만 추출
    font_size_num = int(re.search(r'\d+', font_size).group())
    
    # wrap_text 함수를 사용하여 텍스트 줄바꿈
    lines = wrap_text(text, width, font_size_num, max_lines)
    
    # 줄 높이 계산
    line_spacing = font_size_num * line_height
    
    # 텍스트 그룹 생성
    text_group = Group()
    
    # 각 줄을 개별 텍스트 요소로 추가
    for i, line in enumerate(lines):
        line_y = y + (i * line_spacing)
        text_element = Text(
            line, 
            insert=(x, line_y),
            text_anchor=text_anchor,
            font_family=font_family,
            font_weight=font_weight,
            font_size=font_size,
            fill=fill
        )
        text_element.attribs['class'] = css_class
        text_group.add(text_element)
    
    # 총 높이 계산 (마지막 줄 포함)
    total_height = len(lines) * line_spacing if lines else 0
    
    return text_group, total_height

def generate_card_diagram(
    data: List[Dict[str, str]], 
    output_file: str, 
    title: str = "골밀도란 무엇인가?",
    card_color: str = "#FEEBDC",
    title_color: str = "#333333",
    content_color: str = "#333333",
    size: int = 800,  # 정사각형 사이즈 (1:1 비율)
    background_color: str = "#111111",
    background_image: Optional[str] = None,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    header_image: Optional[str] = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 30,
    vertical_spacing: int = 20,
    add_responsive: bool = True
) -> str:
    """
    구조화된 데이터를 기반으로 카드 형태의 다이어그램을 생성합니다.
    
    Args:
        data: 구조화된 데이터 리스트 (각 항목은 {'title': '제목', 'content': '내용'} 형태)
        output_file: 출력 SVG 파일 경로
        title: 다이어그램 상단에 표시할 제목
        card_color: 카드 배경색 (기본값: 베이지색)
        title_color: 카드 제목 색상
        content_color: 카드 내용 색상
        size: SVG 크기 (정사각형: width=height=size, 1:1 비율)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        pixabay_query: 픽사베이 이미지 검색어 (선택 사항)
        pixabay_api_key: 픽사베이 API 키 (선택 사항)
        header_image: 상단 이미지 경로 (선택 사항)
        header_image_height: 상단 이미지 높이 (기본값: 300px)
        header_color: 헤더 텍스트 색상
        rounded_corners: 카드 모서리 둥글기 정도
        card_padding: 카드 내부 여백
        vertical_spacing: 카드 사이 세로 간격
        add_responsive: 반응형 스크립트 추가 여부
        
    Returns:
        str: 생성된 SVG 파일의 경로
    """
    # 데이터 검증
    if not data:
        raise ValueError("데이터가 비어 있습니다.")
    
    # 상단 이미지가 있는 경우 추가 높이 계산
    top_offset = 100  # 기본 타이틀 영역 높이
    if header_image:
        top_offset = header_image_height + 50  # 이미지 높이 + 여백
    
    # 픽사베이 API를 통한 이미지 검색 (header_image가 없고 픽사베이 검색어와 API 키가 제공된 경우)
    if not header_image and pixabay_query and pixabay_api_key:
        pixabay_image_url = get_pixabay_image(pixabay_query, pixabay_api_key, size, header_image_height)
        if pixabay_image_url:
            header_image = pixabay_image_url
            top_offset = header_image_height + 50
    
    # SVG 캔버스 생성 - size를 명시적으로 지정하되 반응형으로 작동하도록 %로 설정 
    dwg = svgwrite.Drawing(output_file, profile='full', size=('100%', '100%'))
    
    # 카드 너비 계산
    card_width = size * 0.85
    
    # 각 카드의 높이 계산 및 카드 생성
    y_offset = top_offset
    card_heights = []
    
    # 반응형 속성 추가
    if add_responsive:
        add_responsive_scripts(dwg)
    
    # 임시로 총 높이 계산을 위한 처리
    for card in data:
        card_title = card.get('title', '')
        card_content = card.get('content', '')
        
        # 카드 내용 영역 너비 계산
        content_width = card_width - (card_padding * 2)
        
        # 제목 높이 (고정)
        title_height = 40
        
        # 내용 줄바꿈 및 높이 계산
        font_size_num = int(size * 0.02)
        lines = wrap_text(card_content, int(content_width), font_size_num)
        content_height = len(lines) * 30  # 줄 간격 24px에서 30px로 증가
        
        # 카드 총 높이 계산
        card_height = title_height + content_height + (card_padding * 2)
        card_heights.append(card_height)
    
    # 총 콘텐츠 높이 계산
    content_height = top_offset + sum(card_heights) + (vertical_spacing * (len(data) - 1)) + 50
    
    # SVG는 1:1 비율이어야 하므로 size를 기준으로 함
    # 콘텐츠 높이가 size보다 크면 스크롤 가능한 내부 영역으로 처리
    viewport_height = max(size, content_height)
    
    # viewBox 설정 (반응형 레이아웃을 위해 중요)
    dwg.attribs['viewBox'] = f"0 0 {size} {viewport_height}"
    
    # 배경 추가
    dwg.add(dwg.rect(insert=(0, 0), size=(size, viewport_height), fill=background_color))
    
    # 배경 이미지 추가 (선택 사항)
    if background_image:
        # 이미지를 반투명하게 적용하기 위한 그룹
        bg_group = Group(opacity=0.2)
        bg_image = dwg.image(href=background_image, insert=(0, 0), size=(size, viewport_height))
        bg_group.add(bg_image)
        dwg.add(bg_group)
    
    # 상단 이미지 추가 (선택 사항)
    if header_image:
        header_img = dwg.image(
            href=header_image,
            insert=(0, 0),
            size=(size, header_image_height)
        )
        dwg.add(header_img)
        
        # 이미지 위에 반투명 오버레이 추가 (텍스트 가독성 향상)
        overlay = dwg.rect(
            insert=(0, 0),
            size=(size, header_image_height),
            fill=background_color,
            opacity=0.3
        )
        dwg.add(overlay)
    
    # 타이틀 추가
    title_y = 60 if not header_image else header_image_height - 40
    title_text = Text(title, insert=(size / 2, title_y), 
                    text_anchor="middle", dominant_baseline="middle",
                    font_family="Arial", font_weight="bold", 
                    font_size=f"{int(size * 0.04)}px", fill=header_color)
    title_text.attribs['class'] = 'diagram-title'
    dwg.add(title_text)
    
    # 카드 위치 계산을 위한 시작 y좌표
    y_offset = top_offset
    
    # 각 카드 추가
    for i, card in enumerate(data):
        card_title = card.get('title', f"카드 {i+1}")
        card_content = card.get('content', "")
        
        # 카드 높이
        card_height = card_heights[i]
        
        # 카드 배경
        card_x = (size - card_width) / 2
        
        # 카드 그림자 효과 (간단한 방식으로 구현)
        shadow = Rect(
            insert=(card_x + 3, y_offset + 3),
            size=(card_width, card_height),
            rx=rounded_corners, ry=rounded_corners,
            fill="#000000", opacity=0.2
        )
        dwg.add(shadow)
        
        # 카드 본체
        card_rect = Rect(
            insert=(card_x, y_offset),
            size=(card_width, card_height),
            rx=rounded_corners, ry=rounded_corners,
            fill=card_color
        )
        dwg.add(card_rect)
        
        # 카드 제목
        title_x = card_x + card_padding
        title_y = y_offset + card_padding + 20
        title_element = Text(card_title, insert=(title_x, title_y), 
                          text_anchor="start", 
                          font_family="Arial", font_weight="bold", 
                          font_size=f"{int(size * 0.025)}px", fill=title_color)
        title_element.attribs['class'] = 'diagram-title'
        dwg.add(title_element)
        
        # 카드 내용 (자동 줄바꿈 적용)
        content_x = title_x
        content_y = title_y + 30
        content_width = card_width - (card_padding * 2)
        
        # 카드 크기에 맞게 자동 줄바꿈과 높이 계산을 위한 개선된 함수 사용
        # 폰트 크기는 SVG 크기에 비례하도록 설정
        font_size = f"{int(size * 0.02)}px"
        font_size_num = int(size * 0.02)
        
        # 카드 높이에 맞게 텍스트 줄 수 제한 계산
        max_card_content_height = card_height - (card_padding * 2) - 40  # 제목 영역 높이 제외
        line_height = 1.5  # 줄 간격 비율 1.5 적용 (일관성을 위해 명시적으로 선언)
        max_lines = max(1, int(max_card_content_height / (font_size_num * line_height)))  # 줄 간격 비율 적용
        
        content_group, content_height = create_text_with_wrapping(
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
            line_height=line_height,  # 줄 간격 명시적으로 전달
            max_lines=max_lines
        )
        dwg.add(content_group)
        
        # 다음 카드의 y좌표 갱신
        y_offset += card_height + vertical_spacing
    
    # SVG 저장
    dwg.save()
    
    return output_file

def generate_unified_card_diagram(
    main_title: str,
    sub_title_sections: List[Dict[str, str]],
    output_file: str,
    card_color: str = "#FEEBDC",
    title_color: str = "#333333",
    content_color: str = "#333333",
    size: int = 800,
    background_color: str = "#111111",
    background_image: Optional[str] = None,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    header_image: Optional[str] = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 30,
    vertical_spacing: int = 20,
    add_responsive: bool = True
) -> str:
    """
    통일된 인터페이스를 사용하여 카드 다이어그램을 생성합니다.
    
    Args:
        main_title: 다이어그램 상단에 표시될 메인 타이틀
        sub_title_sections: 서브 타이틀과 컨텐츠로 구성된 섹션들
            각 항목은 {'title': '서브 타이틀', 'content': '내용'} 형태
        output_file: 출력 SVG 파일 경로
        card_color: 카드 배경색 (기본값: 베이지색)
        title_color: 카드 제목 색상
        content_color: 카드 내용 색상
        size: SVG 크기 (정사각형: 1:1 비율)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        pixabay_query: 픽사베이 이미지 검색어 (선택 사항)
        pixabay_api_key: 픽사베이 API 키 (선택 사항)
        header_image: 상단 이미지 경로 (선택 사항)
        header_image_height: 상단 이미지 높이 (기본값: 300px)
        header_color: 헤더 텍스트 색상
        rounded_corners: 카드 모서리 둥글기 정도
        card_padding: 카드 내부 여백
        vertical_spacing: 카드 사이 세로 간격
        add_responsive: 반응형 스크립트 추가 여부
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    return generate_card_diagram(
        sub_title_sections, output_file, main_title,
        card_color, title_color, content_color,
        size, background_color, background_image,
        pixabay_query, pixabay_api_key,
        header_image, header_image_height, header_color,
        rounded_corners, card_padding, vertical_spacing,
        add_responsive
    )

if __name__ == "__main__":
    # 테스트 데이터
    test_data = [
        {
            "title": "골밀도 검사 필요성",
            "content": "골밀도 검사는 뼈의 건강 상태를 평가하고 골다공증 위험을 조기에 발견하기 위한 중요한 검사입니다. 특히 50세 이상의 여성이나 고위험군에 속하는 사람들에게 정기적인 검사가 권장됩니다."
        },
        {
            "title": "검사 방법",
            "content": "가장 일반적인 방법은 이중 에너지 X선 흡수계측법(DEXA)입니다. 이 방법은 방사선 노출이 적고 정확도가 높아 표준 검사법으로 사용됩니다. 주로 척추와 고관절 부위의 골밀도를 측정합니다."
        },
        {
            "title": "결과 해석",
            "content": "T-점수가 -1.0 이상이면 정상, -1.0에서 -2.5 사이면 골감소증, -2.5 이하면 골다공증으로 진단됩니다. Z-점수는 같은 연령대와 비교한 값으로 특정 질환 가능성을 평가합니다."
        }
    ]
    
    # 출력 디렉토리 생성
    os.makedirs("./outputs", exist_ok=True)
    
    # 테스트 실행
    output_file = generate_unified_card_diagram(
        main_title="골밀도 검사의 중요성",
        sub_title_sections=test_data,
        output_file="./outputs/card_diagram_test.svg"
    )
    
    print(f"카드 다이어그램 생성 완료: {output_file}") 