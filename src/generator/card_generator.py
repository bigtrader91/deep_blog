"""
카드 형태의 다이어그램을 생성하는 모듈입니다.

이 모듈은 제목과 설명 텍스트를 구조화된 형태로 카드 다이어그램으로 변환합니다.
각 카드는 베이지색 배경에 타이틀과 내용을 포함합니다.
"""
from typing import Dict, List, Tuple, Optional, Any
import re
import svgwrite
from svgwrite.container import Group
from svgwrite.shapes import Circle, Rect, Line
from svgwrite.path import Path
from svgwrite.text import Text
from svgwrite.filters import Filter
import math
import textwrap

def parse_text_to_cards(text: str) -> List[Dict[str, str]]:
    """
    문단 단위의 텍스트를 카드 데이터로 변환합니다.
    
    Args:
        text: 입력 텍스트 (문단 단위로 구분된 텍스트)
        
    Returns:
        List[Dict[str, str]]: 구조화된 데이터 리스트
        각 항목은 {'title': '제목', 'content': '내용'} 형태입니다.
    """
    cards = []
    paragraphs = text.strip().split('\n\n')
    
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue
            
        lines = paragraph.split('\n')
        title = lines[0].strip() if lines else f"카드 {i+1}"
        content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        cards.append({
            'title': title,
            'content': content
        })
    
    return cards

def generate_card_diagram(
    data: List[Dict[str, str]], 
    output_file: str, 
    title: str = "골밀도란 무엇인가?",
    card_color: str = "#FEEBDC",
    title_color: str = "#333333",
    content_color: str = "#333333",
    size_width: int = 800,
    size_height: int = None,
    background_color: str = "#111111",
    background_image: Optional[str] = None,
    header_image: Optional[str] = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 30,
    vertical_spacing: int = 20
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
        size_width: SVG 너비
        size_height: SVG 높이 (None인 경우 내용에 따라 자동 계산)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        header_image: 상단 이미지 경로 (선택 사항)
        header_image_height: 상단 이미지 높이 (기본값: 300px)
        header_color: 헤더 텍스트 색상
        rounded_corners: 카드 모서리 둥글기 정도
        card_padding: 카드 내부 여백
        vertical_spacing: 카드 사이 세로 간격
        
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
        lines = len(textwrap.wrap(content, width=int(size_width * 0.8 / 10)))  # 대략적인 줄 수 추정
        card_height = 60 + (lines * 24) + (card_padding * 2)  # 제목 + 내용 + 상하 패딩
        card_heights.append(card_height)
    
    # 상단 이미지가 있는 경우 추가 높이 계산
    top_offset = 100  # 기본 타이틀 영역 높이
    if header_image:
        top_offset = header_image_height + 50  # 이미지 높이 + 여백
    
    # 높이 계산 (지정되지 않은 경우)
    if size_height is None:
        # 타이틀/이미지 + 각 카드 높이 합계 + 카드 간 간격 + 여백
        size_height = top_offset + sum(card_heights) + (vertical_spacing * (len(data) - 1)) + 50
    
    # SVG 캔버스 생성
    dwg = svgwrite.Drawing(output_file, size=(f"{size_width}px", f"{size_height}px"), profile='tiny')
    
    # 반응형 뷰박스 설정
    dwg.viewbox(0, 0, size_width, size_height)
    
    # 배경 추가
    dwg.add(dwg.rect(insert=(0, 0), size=(size_width, size_height), fill=background_color))
    
    # 배경 이미지 추가 (선택 사항)
    if background_image:
        # 이미지를 반투명하게 적용하기 위한 그룹
        bg_group = Group(opacity=0.2)
        bg_image = dwg.image(href=background_image, insert=(0, 0), size=(size_width, size_height))
        bg_group.add(bg_image)
        dwg.add(bg_group)
    
    # 상단 이미지 추가 (선택 사항)
    if header_image:
        header_img = dwg.image(
            href=header_image,
            insert=(0, 0),
            size=(size_width, header_image_height)
        )
        dwg.add(header_img)
        
        # 이미지 위에 반투명 오버레이 추가 (텍스트 가독성 향상)
        overlay = dwg.rect(
            insert=(0, 0),
            size=(size_width, header_image_height),
            fill=background_color,
            opacity=0.3
        )
        dwg.add(overlay)
    
    # 타이틀 추가
    title_y = 60 if not header_image else header_image_height - 40
    title_text = Text(title, insert=(size_width / 2, title_y), 
                    text_anchor="middle", dominant_baseline="middle",
                    font_family="Arial", font_weight="bold", 
                    font_size=f"{int(size_width * 0.04)}px", fill=header_color)
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
        card_width = size_width * 0.85
        card_x = (size_width - card_width) / 2
        
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
                          font_size=f"{int(size_width * 0.025)}px", fill=title_color)
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
                              font_size=f"{int(size_width * 0.02)}px", fill=content_color)
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
    size_width: int = 800,
    size_height: int = None,
    background_color: str = "#111111",
    background_image: Optional[str] = None,
    header_image: Optional[str] = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 30,
    vertical_spacing: int = 20
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
        size_width: SVG 너비
        size_height: SVG 높이 (None인 경우 내용에 따라 자동 계산)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        header_image: 상단 이미지 경로 (선택 사항)
        header_image_height: 상단 이미지 높이 (기본값: 300px)
        header_color: 헤더 텍스트 색상
        rounded_corners: 카드 모서리 둥글기 정도
        card_padding: 카드 내부 여백
        vertical_spacing: 카드 사이 세로 간격
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 텍스트를 구조화된 데이터로 변환
    card_data = parse_text_to_cards(text)
    
    # 카드 다이어그램 생성
    return generate_card_diagram(
        card_data, output_file, title, 
        card_color, title_color, content_color,
        size_width, size_height, background_color, 
        background_image, header_image, header_image_height,
        header_color, rounded_corners, card_padding, vertical_spacing
    )

def generate_card_from_data(
    data: List[Dict[str, str]], 
    output_file: str, 
    title: str = "골밀도란 무엇인가?",
    card_color: str = "#FEEBDC",
    title_color: str = "#333333",
    content_color: str = "#333333",
    size_width: int = 800,
    size_height: int = None,
    background_color: str = "#111111",
    background_image: Optional[str] = None,
    header_image: Optional[str] = None,
    header_image_height: int = 300,
    header_color: str = "#FFFFFF",
    rounded_corners: int = 10,
    card_padding: int = 30,
    vertical_spacing: int = 20
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
        size_width: SVG 너비
        size_height: SVG 높이 (None인 경우 내용에 따라 자동 계산)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        header_image: 상단 이미지 경로 (선택 사항)
        header_image_height: 상단 이미지 높이 (기본값: 300px)
        header_color: 헤더 텍스트 색상
        rounded_corners: 카드 모서리 둥글기 정도
        card_padding: 카드 내부 여백
        vertical_spacing: 카드 사이 세로 간격
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 카드 다이어그램 생성
    return generate_card_diagram(
        data, output_file, title, 
        card_color, title_color, content_color,
        size_width, size_height, background_color, 
        background_image, header_image, header_image_height,
        header_color, rounded_corners, card_padding, vertical_spacing
    ) 