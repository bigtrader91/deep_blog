"""
카드 형태의 다이어그램을 생성하는 모듈입니다.

이 모듈은 제목과 설명 텍스트를 구조화된 형태로 카드 다이어그램으로 변환합니다.
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
    SVGTiny 1.2 프로필은 많은 제약사항이 있어 매우 기본적인 속성만 사용합니다.
    
    Args:
        dwg: SVG 드로잉 객체
    """
    # SVG 속성 직접 추가 (가장 기본적인 반응형 속성만 추가)
    dwg.attribs['preserveAspectRatio'] = 'xMidYMid meet'
    # width와 height는 SVG 생성 시 직접 설정

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
    
    # 각 카드의 높이 계산 (제목 높이 + 내용 줄 수에 따른 높이 + 패딩)
    card_heights = []
    for card in data:
        content = card.get('content', '')
        lines = len(textwrap.wrap(content, width=int(size * 0.8 / 10)))  # 대략적인 줄 수 추정
        card_height = 60 + (lines * 24) + (card_padding * 2)  # 제목 + 내용 + 상하 패딩
        card_heights.append(card_height)
    
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
    
    # 총 콘텐츠 높이 계산
    content_height = top_offset + sum(card_heights) + (vertical_spacing * (len(data) - 1)) + 50
    
    # SVG는 1:1 비율이어야 하므로 size를 기준으로 함
    # 콘텐츠 높이가 size보다 크면 스크롤 가능한 내부 영역으로 처리
    viewport_height = max(size, content_height)
    
    # SVG 캔버스 생성 - size를 명시적으로 지정하되 반응형으로 작동하도록 %로 설정 
    dwg = svgwrite.Drawing(output_file, profile='tiny', size=('100%', '100%'))
    
    # 반응형 속성 추가
    if add_responsive:
        add_responsive_scripts(dwg)
    
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
        card_width = size * 0.85
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
        card = Rect(
            insert=(card_x, y_offset),
            size=(card_width, card_height),
            rx=rounded_corners, ry=rounded_corners,
            fill=card_color
        )
        dwg.add(card)
        
        # 카드 제목
        title_x = card_x + card_padding
        title_y = y_offset + card_padding + 20
        title_element = Text(card_title, insert=(title_x, title_y), 
                          text_anchor="start", 
                          font_family="Arial", font_weight="bold", 
                          font_size=f"{int(size * 0.025)}px", fill=title_color)
        dwg.add(title_element)
        
        # 카드 내용
        content_x = title_x
        content_y = title_y + 30
        content_width = card_width - (card_padding * 2)
        content_lines = textwrap.wrap(card_content, width=int(content_width / 10))
        
        for j, line in enumerate(content_lines):
            line_y = content_y + (j * 24)
            content_line = Text(line, insert=(content_x, line_y), 
                              text_anchor="start", font_family="Arial",
                              font_size=f"{int(size * 0.02)}px", fill=content_color)
            dwg.add(content_line)
        
        # 다음 카드의 y좌표 갱신
        y_offset += card_height + vertical_spacing
    
    # SVG 저장
    dwg.save()
    
    return output_file

def generate_card_from_text(
    text: str, 
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
    문단 단위의 텍스트를 카드 다이어그램으로 변환합니다.
    
    Args:
        text: 입력 텍스트 (문단 단위로 구분된 텍스트)
        output_file: 출력 SVG 파일 경로
        title: 다이어그램 상단에 표시할 제목
        card_color: 카드 배경색
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
    # 텍스트를 구조화된 데이터로 변환
    card_data = parse_text_to_cards(text)
    
    # 카드 다이어그램 생성
    return generate_card_diagram(
        card_data, output_file, title, 
        card_color, title_color, content_color,
        size, background_color, background_image,
        pixabay_query, pixabay_api_key,
        header_image, header_image_height, header_color,
        rounded_corners, card_padding, vertical_spacing,
        add_responsive
    )

def generate_card_from_data(
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
    구조화된 데이터를 직접 입력 받아 카드 다이어그램으로 변환합니다.
    
    Args:
        data: 구조화된 데이터 리스트 (각 항목은 {'title': '제목', 'content': '내용'} 형태)
        output_file: 출력 SVG 파일 경로
        title: 다이어그램 상단에 표시할 제목
        card_color: 카드 배경색
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
    # 카드 다이어그램 생성
    return generate_card_diagram(
        data, output_file, title, 
        card_color, title_color, content_color,
        size, background_color, background_image,
        pixabay_query, pixabay_api_key,
        header_image, header_image_height, header_color,
        rounded_corners, card_padding, vertical_spacing,
        add_responsive
    ) 