#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from urllib.parse import quote
from svgwrite.container import Group
from svgwrite.text import Text

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

def add_responsive_attributes(dwg: svgwrite.Drawing) -> None:
    """
    SVG에 반응형 속성을 추가합니다.
    
    Args:
        dwg: SVG 드로잉 객체
    """
    # 향상된 반응형 스크립트 추가
    add_responsive_script(dwg)

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
        Tuple[Group, float]: 텍스트 그룹과 총 높이
    """
    # 폰트 크기에서 숫자만 추출
    font_size_num = int(re.search(r'\d+', font_size).group())
    
    # 향상된 wrap_text 함수를 사용
    lines = wrap_text(text, width, font_size_num)
    
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
    
def generate_split_layout(
    title: str,
    descriptions: List[Dict[str, str]],
    output_file: str,
    header_image: Optional[str] = None,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    width: int = 800,
    height: int = 1000,
    background_color: str = "#FFFFFF",
    title_color: str = "#333333",
    description_color: str = "#555555",
    number_color: str = "#FFFFFF",
    number_bg_color: str = "#4A90E2",
    add_responsive: bool = True
) -> str:
    """
    40:60 비율로 이미지와 텍스트를 배치한 SVG 다이어그램을 생성합니다.
    
    Args:
        title: 메인 제목
        descriptions: 설명 리스트 (각 항목은 {'number': '숫자', 'title': '제목', 'description': '설명'} 형태)
        output_file: 출력 SVG 파일 경로
        header_image: 상단 이미지 경로 (선택 사항)
        pixabay_query: 픽사베이 이미지 검색어 (선택 사항)
        pixabay_api_key: 픽사베이 API 키 (선택 사항)
        width: SVG 너비 (기본값: 800px)
        height: SVG 높이 (기본값: 1000px)
        background_color: 배경색 (기본값: 흰색)
        title_color: 제목 색상 (기본값: 진한 회색)
        description_color: 설명 텍스트 색상 (기본값: 회색)
        number_color: 번호 텍스트 색상 (기본값: 흰색)
        number_bg_color: 번호 배경 색상 (기본값: 파란색)
        add_responsive: 반응형 속성 추가 여부 (기본값: True)
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 이미지 영역 높이 계산 (전체 높이의 40%)
    image_height = int(height * 0.4)
    
    # 텍스트 영역 시작 위치 및 높이
    text_area_y = image_height
    text_area_height = height - image_height
    
    # SVG 캔버스 생성
    dwg = svgwrite.Drawing(output_file, profile='full', size=(f"{width}px", f"{height}px"))
    
    # 반응형 속성 추가
    if add_responsive:
        add_responsive_attributes(dwg)
    
    # viewBox 설정
    dwg.attribs['viewBox'] = f"0 0 {width} {height}"
    
    # 배경 추가
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill=background_color))
    
    # 픽사베이 API를 통한 이미지 검색
    if not header_image and pixabay_query and pixabay_api_key:
        pixabay_image_url = get_pixabay_image(pixabay_query, pixabay_api_key, width, image_height)
        if pixabay_image_url:
            header_image = pixabay_image_url
    
    # 헤더 이미지 추가
    if header_image:
        header_img = dwg.image(
            href=header_image,
            insert=(0, 0),
            size=(width, image_height)
        )
        dwg.add(header_img)
    else:
        # 이미지가 없는 경우 기본 색상 배경
        dwg.add(dwg.rect(insert=(0, 0), size=(width, image_height), fill="#E0E0E0"))
    
    # 메인 제목 추가
    title_y = text_area_y + 60
    title_text = dwg.text(
        title, 
        insert=(width/2, title_y),
        text_anchor="middle",
        font_family="Arial", 
        font_weight="bold",
        font_size="32px",
        fill=title_color
    )
    title_text.attribs['class'] = 'diagram-title'
    dwg.add(title_text)
    
    # 설명 텍스트 추가
    description_y = title_y + 80
    line_height = 30
    
    for i, item in enumerate(descriptions):
        item_y = description_y + (i * 100)
        
        # 번호 원형 배경
        if 'number' in item:
            circle_radius = 20
            circle_x = 50
            circle_y = item_y - 10
            
            # 원형 배경
            dwg.add(dwg.circle(
                center=(circle_x, circle_y),
                r=circle_radius,
                fill=number_bg_color
            ))
            
            # 번호 텍스트
            number_text = dwg.text(
                item['number'],
                insert=(circle_x, circle_y + 7),
                text_anchor="middle",
                font_family="Arial",
                font_weight="bold",
                font_size="20px",
                fill=number_color
            )
            number_text.attribs['class'] = 'diagram-text'
            dwg.add(number_text)
            
            # 제목 및 설명 위치 조정
            text_x = circle_x + circle_radius + 30
        else:
            text_x = 50
        
        # 항목 제목
        if 'title' in item:
            title_element = dwg.text(
                item['title'],
                insert=(text_x, item_y),
                font_family="Arial",
                font_weight="bold",
                font_size="22px",
                fill=title_color
            )
            title_element.attribs['class'] = 'diagram-title'
            dwg.add(title_element)
        
        # 항목 설명 (자동 줄바꿈 적용)
        if 'description' in item:
            desc_text = item.get('description', '')
            desc_width = width - text_x - 50  # 여백 고려
            
            # 향상된 텍스트 줄바꿈 함수 사용
            desc_group, desc_height = create_wrapped_text(
                dwg=dwg,
                text=desc_text,
                x=text_x,
                y=item_y + 30,
                width=desc_width,
                font_size="18px",
                text_anchor="start",
                font_family="Arial",
                fill=description_color,
                css_class="diagram-text"
            )
            dwg.add(desc_group)
    
    # SVG 저장
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
    """
    40:60 비율의 이미지와 텍스트 레이아웃의 SVG 생성 함수의 간소화된 버전
    
    Args:
        title: 메인 제목
        content_items: 내용 항목 리스트 (각 항목은 {'number': '번호', 'title': '제목', 'description': '설명'} 형태)
        output_file: 출력 파일 경로
        image_url: 이미지 URL (선택 사항)
        pixabay_query: 픽사베이 이미지 검색어 (선택 사항)
        pixabay_api_key: 픽사베이 API 키 (선택 사항)
        width: 너비 (기본값: 800px)
        height: 높이 (기본값: 1200px)
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 기본 색상 설정
    background_color = "#FFFFFF"  # 흰색 배경
    title_color = "#333333"      # 어두운 회색 제목
    description_color = "#555555"  # 중간 회색 설명
    number_color = "#FFFFFF"     # 흰색 번호 텍스트
    number_bg_color = "#4A90E2"  # 파란색 번호 배경
    
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
        description_color=description_color,
        number_color=number_color,
        number_bg_color=number_bg_color
    )

def generate_unified_image_diagram(
    main_title: str,
    sub_title_sections: List[Dict[str, str]],
    output_file: str,
    header_image: Optional[str] = None,
    pixabay_query: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    width: int = 800,
    height: int = 1000,
    background_color: str = "#FFFFFF",
    title_color: str = "#333333",
    description_color: str = "#555555",
    number_color: str = "#FFFFFF",
    number_bg_color: str = "#4A90E2",
    add_responsive: bool = True
) -> str:
    """
    통일된 인터페이스를 사용하여 이미지-텍스트 다이어그램을 생성합니다.
    
    Args:
        main_title: 메인 제목
        sub_title_sections: 서브 타이틀과 컨텐츠로 구성된 섹션들
            각 항목은 {'title': '서브 타이틀', 'content': '내용'} 형태
        output_file: 출력 SVG 파일 경로
        header_image: 상단 이미지 경로 (선택 사항)
        pixabay_query: 픽사베이 이미지 검색어 (선택 사항)
        pixabay_api_key: 픽사베이 API 키 (선택 사항)
        width: SVG 너비 (기본값: 800px)
        height: SVG 높이 (기본값: 1000px)
        background_color: 배경색 (기본값: 흰색)
        title_color: 제목 색상 (기본값: 진한 회색)
        description_color: 설명 텍스트 색상 (기본값: 회색)
        number_color: 번호 텍스트 색상 (기본값: 흰색)
        number_bg_color: 번호 배경 색상 (기본값: 파란색)
        add_responsive: 반응형 속성 추가 여부 (기본값: True)
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 데이터 구조 변환 (sub_title_sections의 각 항목은 {'title': '제목', 'content': '내용'} 형식)
    # 이를 descriptions 형식 {'number': '번호', 'title': '제목', 'description': '설명'}으로 변환
    descriptions = []
    for i, section in enumerate(sub_title_sections):
        descriptions.append({
            'number': str(i+1),
            'title': section.get('title', f'섹션 {i+1}'),
            'description': section.get('content', '')
        })
    
    return generate_split_layout(
        title=main_title,
        descriptions=descriptions,
        output_file=output_file,
        header_image=header_image,
        pixabay_query=pixabay_query,
        pixabay_api_key=pixabay_api_key,
        width=width,
        height=height,
        background_color=background_color,
        title_color=title_color,
        description_color=description_color,
        number_color=number_color,
        number_bg_color=number_bg_color,
        add_responsive=add_responsive
    )

if __name__ == "__main__":
    # 테스트 데이터
    test_data = [
        {
            "title": "골밀도 검사란",
            "content": "골밀도 검사는 뼈의 밀도를 측정하여 골다공증 위험을 평가하는 중요한 검사입니다."
        },
        {
            "title": "검사가 필요한 사람",
            "content": "50세 이상 여성, 저체중, 골절 경험이 있는 사람, 특정 약물 복용자 등이 우선 대상입니다."
        },
        {
            "title": "검사 방법",
            "content": "DEXA 스캔은 가장 정확한 골밀도 측정 방법으로, 이중 에너지 X선 흡수계측법을 사용합니다."
        },
        {
            "title": "결과 해석",
            "content": "T-점수는 젊은 성인과 비교한 값으로, -1.0 이상은 정상, -1.0~-2.5는 골감소증, -2.5 이하는 골다공증으로 진단합니다."
        }
    ]
    
    # 출력 디렉토리 생성
    os.makedirs("./outputs", exist_ok=True)
    
    # 테스트 실행
    output_file = generate_unified_image_diagram(
        main_title="골밀도 검사 가이드",
        sub_title_sections=test_data,
        output_file="./outputs/image_diagram_test.svg",
        pixabay_query="bone health", 
        pixabay_api_key="YOUR_API_KEY_HERE"  # 실제 사용 시 유효한 API 키로 변경
    )
    
    print(f"이미지 다이어그램 생성 완료: {output_file}") 