#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
40:60 비율의 이미지-텍스트 레이아웃을 가진 SVG 다이어그램 생성기

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
    # 반응형 속성 추가
    dwg.attribs['preserveAspectRatio'] = 'xMidYMid meet'
    
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
    dwg = svgwrite.Drawing(output_file, profile='tiny', size=(f"{width}px", f"{height}px"))
    
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
            dwg.add(dwg.text(
                item['number'],
                insert=(circle_x, circle_y + 7),
                text_anchor="middle",
                font_family="Arial",
                font_weight="bold",
                font_size="20px",
                fill=number_color
            ))
            
            # 제목 및 설명 위치 조정
            text_x = circle_x + circle_radius + 30
        else:
            text_x = 50
        
        # 항목 제목
        if 'title' in item:
            dwg.add(dwg.text(
                item['title'],
                insert=(text_x, item_y),
                font_family="Arial",
                font_weight="bold",
                font_size="22px",
                fill=title_color
            ))
        
        # 항목 설명
        if 'description' in item:
            desc_text = item.get('description', '')
            # 텍스트 줄바꿈 (최대 너비 기준)
            max_chars = int((width - text_x - 50) / 10)  # 대략적인 글자 수 계산
            wrapped_lines = textwrap.wrap(desc_text, width=max_chars)
            
            for j, line in enumerate(wrapped_lines):
                dwg.add(dwg.text(
                    line,
                    insert=(text_x, item_y + 30 + (j * line_height)),
                    font_family="Arial",
                    font_size="18px",
                    fill=description_color
                ))
    
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
        number_bg_color=number_bg_color,
        add_responsive=True
    ) 