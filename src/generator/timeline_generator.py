"""
타임라인/단계 형태의 다이어그램을 생성하는 모듈입니다.

이 모듈은 단계별 데이터를 구조화된 형태로 변환하고,
구조화된 데이터를 svgwrite를 사용하여 세로 타임라인 다이어그램으로 생성합니다.
"""
from typing import Dict, List, Tuple, Optional, Any
import re
import svgwrite
from svgwrite.container import Group
from svgwrite.shapes import Circle, Rect, Line
from svgwrite.path import Path
from svgwrite.text import Text
from svgwrite.gradients import LinearGradient
import math
import textwrap

def parse_text_to_timeline(text: str) -> List[Dict[str, str]]:
    """
    문단 단위의 텍스트를 타임라인 데이터로 변환합니다.
    
    Args:
        text: 입력 텍스트 (문단 단위로 구분된 텍스트)
        
    Returns:
        List[Dict[str, str]]: 구조화된 데이터 리스트
        각 항목은 {'step': '단계', 'title': '제목', 'content': '내용'} 형태입니다.
    """
    sections = []
    paragraphs = text.strip().split('\n\n')
    
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue
            
        lines = paragraph.split('\n')
        title = lines[0].strip() if lines else f"단계 {i+1}"
        content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        sections.append({
            'step': str(i+1),
            'title': title,
            'content': content
        })
    
    return sections

def generate_timeline_diagram(
    data: List[Dict[str, str]], 
    output_file: str, 
    title: str = "정기적인 골밀도 검사의 중요성",
    colors: Optional[List[str]] = None,
    size_width: int = 800,
    size_height: int = None,
    background_color: str = "#24292e",
    background_image: Optional[str] = None,
    text_color: str = "#FFFFFF"
) -> str:
    """
    구조화된 데이터를 기반으로 세로 타임라인 다이어그램을 생성합니다.
    
    Args:
        data: 구조화된 데이터 리스트 (각 항목은 {'step': '단계', 'title': '제목', 'content': '내용'} 형태)
        output_file: 출력 SVG 파일 경로
        title: 다이어그램 상단에 표시할 제목
        colors: 각 단계별 강조색 (기본값: ["#FECEAB"])
        size_width: SVG 너비
        size_height: SVG 높이 (None인 경우 내용에 따라 자동 계산)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        text_color: 텍스트 색상
        
    Returns:
        str: 생성된 SVG 파일의 경로
    """
    if not colors:
        colors = ["#FECEAB"]  # 기본 베이지 색상
    
    # 데이터 검증
    if not data:
        raise ValueError("데이터가 비어 있습니다.")
    
    # 높이 계산 (지정되지 않은 경우)
    if size_height is None:
        # 타이틀 + 각 단계별 최소 높이 + 여백
        size_height = 120 + (len(data) * 180)
    
    # SVG 캔버스 생성
    dwg = svgwrite.Drawing(output_file, size=(f"{size_width}px", f"{size_height}px"), profile='tiny')
    
    # 반응형 뷰박스 설정
    dwg.viewbox(0, 0, size_width, size_height)
    
    # 배경 추가
    dwg.add(dwg.rect(insert=(0, 0), size=(size_width, size_height), fill=background_color))
    
    # 배경 이미지 추가 (선택 사항)
    if background_image:
        # 이미지를 반투명하게 적용하기 위한 그룹
        bg_group = Group(opacity=0.15)
        bg_image = dwg.image(href=background_image, insert=(0, 0), size=(size_width, size_height))
        bg_group.add(bg_image)
        dwg.add(bg_group)
    
    # 타이틀 추가
    title_text = Text(title, insert=(size_width / 2, 60), 
                    text_anchor="middle", dominant_baseline="middle",
                    font_family="Arial", font_weight="bold", 
                    font_size=f"{int(size_width * 0.03)}px", fill=text_color)
    dwg.add(title_text)
    
    # 왼쪽 세로선 (타임라인)
    line_x = size_width * 0.1
    timeline = Line(start=(line_x, 100), end=(line_x, size_height - 50),
                  stroke="#8E8E8E", stroke_width=2)
    dwg.add(timeline)
    
    # 각 단계 추가
    y_offset = 130
    step_height = 160
    
    for i, step in enumerate(data):
        step_number = step.get('step', str(i+1))
        step_title = step.get('title', f"단계 {step_number}")
        step_content = step.get('content', "")
        
        # 단계별 위치 계산
        step_y = y_offset + (i * step_height)
        
        # 단계 원 및 숫자 (왼쪽에 위치)
        # 베이지색 박스 배경
        step_bg = Rect(
            insert=(line_x - 25, step_y - 25),
            size=(50, 50),
            rx=10, ry=10,  # 둥근 모서리
            fill=colors[i % len(colors)]
        )
        dwg.add(step_bg)
        
        # 단계 숫자
        step_text = Text(step_number, insert=(line_x, step_y + 8), 
                       text_anchor="middle", dominant_baseline="middle",
                       font_family="Arial", font_weight="bold", 
                       font_size=f"{int(size_width * 0.025)}px", fill="#333333")
        dwg.add(step_text)
        
        # 제목 추가 (오른쪽에 위치)
        title_x = line_x + 50
        title_y = step_y
        title_element = Text(step_title, insert=(title_x, title_y), 
                           text_anchor="start", 
                           font_family="Arial", font_weight="bold", 
                           font_size=f"{int(size_width * 0.022)}px", fill=text_color)
        dwg.add(title_element)
        
        # 내용 추가 (여러 줄 텍스트)
        content_x = title_x
        content_y = title_y + 30
        content_width = int(size_width * 0.6)  # 최대 텍스트 너비
        content_lines = textwrap.wrap(step_content, width=int(content_width / 10))
        
        for j, line in enumerate(content_lines):
            line_y = content_y + (j * 22)
            content_line = Text(line, insert=(content_x, line_y), 
                              text_anchor="start", font_family="Arial",
                              font_size=f"{int(size_width * 0.018)}px", fill=text_color)
            dwg.add(content_line)
    
    # SVG 저장
    dwg.save()
    
    return output_file

def generate_timeline_from_text(
    text: str, 
    output_file: str, 
    title: str = "정기적인 골밀도 검사의 중요성",
    colors: Optional[List[str]] = None,
    size_width: int = 800,
    size_height: int = None,
    background_color: str = "#24292e",
    background_image: Optional[str] = None,
    text_color: str = "#FFFFFF"
) -> str:
    """
    문단 단위의 텍스트를 타임라인 다이어그램으로 변환합니다.
    
    Args:
        text: 입력 텍스트 (문단 단위로 구분된 텍스트)
        output_file: 출력 SVG 파일 경로
        title: 다이어그램 상단에 표시할 제목
        colors: 각 단계별 강조색
        size_width: SVG 너비
        size_height: SVG 높이 (None인 경우 내용에 따라 자동 계산)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        text_color: 텍스트 색상
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 텍스트를 구조화된 데이터로 변환
    timeline_data = parse_text_to_timeline(text)
    
    # 타임라인 다이어그램 생성
    return generate_timeline_diagram(
        timeline_data, output_file, title, colors, 
        size_width, size_height, background_color, 
        background_image, text_color
    )

def generate_timeline_from_data(
    data: List[Dict[str, str]], 
    output_file: str, 
    title: str = "정기적인 골밀도 검사의 중요성",
    colors: Optional[List[str]] = None,
    size_width: int = 800,
    size_height: int = None,
    background_color: str = "#24292e",
    background_image: Optional[str] = None,
    text_color: str = "#FFFFFF"
) -> str:
    """
    구조화된 데이터를 직접 입력 받아 타임라인 다이어그램으로 변환합니다.
    
    Args:
        data: 구조화된 데이터 리스트 (각 항목은 {'step': '단계', 'title': '제목', 'content': '내용'} 형태)
        output_file: 출력 SVG 파일 경로
        title: 다이어그램 상단에 표시할 제목
        colors: 각 단계별 강조색
        size_width: SVG 너비
        size_height: SVG 높이 (None인 경우 내용에 따라 자동 계산)
        background_color: 배경색
        background_image: 배경 이미지 경로 (선택 사항)
        text_color: 텍스트 색상
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 타임라인 다이어그램 생성
    return generate_timeline_diagram(
        data, output_file, title, colors, 
        size_width, size_height, background_color, 
        background_image, text_color
    ) 