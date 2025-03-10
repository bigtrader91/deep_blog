"""
텍스트를 구조화된 데이터로 변환하고 원형 다이어그램을 생성하는 모듈입니다.

이 모듈은 문단 단위 텍스트를 구조화된 형태로 변환하고,
구조화된 데이터를 svgwrite를 사용하여 반응형 다이어그램으로 생성합니다.
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

def parse_text_to_structure(text: str) -> List[Dict[str, str]]:
    """
    문단 단위의 텍스트를 구조화된 데이터로 변환합니다.
    
    Args:
        text: 입력 텍스트 (문단 단위로 구분된 텍스트)
        
    Returns:
        List[Dict[str, str]]: 구조화된 데이터 리스트
        각 항목은 {'title': '제목', 'content': '내용'} 형태입니다.
    """
    sections = []
    paragraphs = text.strip().split('\n\n')
    
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue
            
        lines = paragraph.split('\n')
        title = lines[0].strip() if lines else f"Title {i+1}"
        content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        sections.append({
            'title': title,
            'content': content
        })
    
    # 최대 5개 섹션으로 제한 (중앙 원의 텍스트가 별도로 있음)
    return sections[:5]

def generate_circular_diagram(
    data: List[Dict[str, str]], 
    output_file: str, 
    center_text: str = "TEXT HERE",
    colors: Optional[List[str]] = None,
    size: int = 500,
    background_color: str = "#FFFFFF"
) -> str:
    """
    구조화된 데이터를 기반으로 원형 다이어그램을 생성합니다.
    
    Args:
        data: 구조화된 데이터 리스트 (최대 5개 항목)
        output_file: 출력 SVG 파일 경로
        center_text: 중앙 원에 표시할 텍스트
        colors: 다이어그램에 사용할 색상 리스트
        size: SVG 크기 (정사각형: width=height=size)
        background_color: 배경색
        
    Returns:
        str: 생성된 SVG 파일의 경로
    """
    if not colors:
        colors = ["#555555", "#4CAF50", "#FFC107", "#FF9800", "#F44336"]
    
    # 데이터 검증 및 제한
    if not data:
        raise ValueError("데이터가 비어 있습니다.")
    if len(data) > 5:
        data = data[:5]
    
    # 필요한 색상 수만큼 색상 리스트 조정
    colors = colors[:len(data)]
    if len(colors) < len(data):
        # 색상이 부족한 경우 기본 색상으로 채움
        colors.extend(["#555555", "#4CAF50", "#FFC107", "#FF9800", "#F44336"][:len(data) - len(colors)])
    
    # SVG 캔버스 생성 (정사각형: 1:1 비율)
    dwg = svgwrite.Drawing(output_file, size=(f"{size}px", f"{size}px"), profile='tiny')
    
    # 반응형 뷰박스 설정
    dwg.viewbox(0, 0, size, size)
    
    # 배경 추가 (색상 또는 투명)
    if background_color:
        dwg.add(dwg.rect(insert=(0, 0), size=(size, size), fill=background_color))
    
    # 중심점
    center_x = size / 2
    center_y = size / 2
    
    # 원의 반지름 설정
    center_radius = size * 0.10  # 중앙 원 반지름
    orbit_radius = size * 0.2   # 주변 원들의 궤도 반지름
    node_radius = size * 0.07   # 주변 원들의 반지름
    
    # 중앙 원 추가
    center_circle = Circle(center=(center_x, center_y), r=center_radius, 
                          fill="#333333", stroke="none")
    dwg.add(center_circle)
    
    # 중앙 원 텍스트 추가
    center_text_element = Text(center_text, insert=(center_x, center_y + size * 0.007), 
                             text_anchor="middle", dominant_baseline="middle",
                             font_family="Arial", font_weight="bold", 
                             font_size=f"{int(size * 0.025)}px", fill="#FFFFFF")
    dwg.add(center_text_element)
    
    # 바깥 테두리 원 추가 (연한 회색)
    outer_circle = Circle(center=(center_x, center_y), r=orbit_radius * 1.05, 
                         fill="none", stroke="#DDDDDD", stroke_width=1)
    dwg.add(outer_circle)
    
    # 각 노드의 각도 계산 (360도를 섹션 수로 나눔)
    num_nodes = len(data)
    angle_per_node = 360 / num_nodes
    
    # 시작 각도 (첫 번째 노드를 상단에 배치)
    start_angle = 270
    
    # 각 노드에 대해 원과 텍스트 추가
    for i, section in enumerate(data):
        # 노드 위치 계산
        angle = math.radians(start_angle + (i * angle_per_node))
        node_x = center_x + orbit_radius * math.cos(angle)
        node_y = center_y + orbit_radius * math.sin(angle)
        
        # 노드 원 추가
        node_color = colors[i % len(colors)]
        node_circle = Circle(center=(node_x, node_y), r=node_radius, 
                           fill="#FFFFFF", stroke=node_color, stroke_width=2)
        dwg.add(node_circle)
        
        # 중앙 원과 노드 원 사이의 연결선 추가
        # 직선에서 시작하는 점과 끝점 계산
        line_start_distance = center_radius * 1.02  # 중앙 원에서 약간 떨어진 지점
        line_end_distance = orbit_radius - node_radius * 1.02  # 노드 원에서 약간 떨어진 지점
        
        line_start_x = center_x + line_start_distance * math.cos(angle)
        line_start_y = center_y + line_start_distance * math.sin(angle)
        
        line_end_x = center_x + line_end_distance * math.cos(angle)
        line_end_y = center_y + line_end_distance * math.sin(angle)
        
        # 연결선 추가 (점선)
        connector = Line(start=(line_start_x, line_start_y), end=(line_end_x, line_end_y),
                        stroke="#DDDDDD", stroke_width=1, stroke_dasharray="4,2")
        dwg.add(connector)
        
        # 노드 제목 추가
        title = section['title']
        title_element = Text(title, insert=(node_x, node_y + size * 0.003), 
                           text_anchor="middle", dominant_baseline="middle",
                           font_family="Arial", font_weight="normal", 
                           font_size=f"{int(size * 0.018)}px", fill="#333333")
        dwg.add(title_element)
        
        # 내용 텍스트 위치 계산 (노드 바깥쪽)
        # 텍스트 정렬 방식 결정 (노드 위치에 따라)
        angle_deg = (start_angle + (i * angle_per_node)) % 360
        
        if 45 <= angle_deg < 135:  # 아래
            text_anchor = "middle"
            text_x = node_x
            text_y = node_y + node_radius * 3
            text_offset_y = size * 0.018  # 줄 간격
        elif 135 <= angle_deg < 225:  # 왼쪽
            text_anchor = "end"
            text_x = node_x - node_radius * 2.2
            text_y = node_y
            text_offset_y = size * 0.018  # 줄 간격
        elif 225 <= angle_deg < 315:  # 위
            text_anchor = "middle"
            text_x = node_x
            text_y = node_y - node_radius * 3
            text_offset_y = size * 0.018  # 줄 간격
        else:  # 오른쪽
            text_anchor = "start"
            text_x = node_x + node_radius * 2.2
            text_y = node_y
            text_offset_y = size * 0.018  # 줄 간격
        
        # 내용 추가 (여러 줄 텍스트)
        content_text = section['content']
        content_lines = textwrap.wrap(content_text, width=25) if content_text else []
        
        for j, line in enumerate(content_lines[:3]):  # 최대 3줄로 제한
            if 45 <= angle_deg < 135 or 225 <= angle_deg < 315:  # 위나 아래
                content_y = text_y + (j * text_offset_y)
            else:  # 왼쪽이나 오른쪽
                if j == 0:
                    # 첫 번째 줄은 중앙에 위치
                    content_y = text_y
                else:
                    # 두 번째, 세 번째 줄은 위아래로 배치
                    offset = j - 1 + 0.5  # 0.5, 1.5
                    content_y = text_y + (offset * text_offset_y)
            
            content = Text(line, insert=(text_x, content_y), 
                          text_anchor=text_anchor, font_family="Arial",
                          font_size=f"{int(size * 0.014)}px", fill="#666666")
            dwg.add(content)
    
    # SVG 저장
    dwg.save()
    
    return output_file

def generate_diagram_from_text(
    text: str, 
    output_file: str, 
    center_text: str = "TEXT HERE",
    colors: Optional[List[str]] = None,
    size: int = 500
) -> str:
    """
    문단 단위의 텍스트를 구조화하고 원형 다이어그램으로 변환합니다.
    
    Args:
        text: 입력 텍스트
        output_file: 출력 SVG 파일 경로
        center_text: 중앙 원에 표시할 텍스트
        colors: 색상 리스트
        size: SVG 크기
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 텍스트를 구조화된 데이터로 변환
    structured_data = parse_text_to_structure(text)
    
    # 다이어그램 생성
    return generate_circular_diagram(structured_data, output_file, center_text, colors, size)

def generate_diagram_from_data(
    data: List[Dict[str, str]], 
    output_file: str, 
    center_text: str = "TEXT HERE",
    colors: Optional[List[str]] = None,
    size: int = 500
) -> str:
    """
    구조화된 데이터를 직접 입력 받아 원형 다이어그램으로 변환합니다.
    
    Args:
        data: 구조화된 데이터 리스트 (각 항목은 {'title': '제목', 'content': '내용'} 형태)
        output_file: 출력 SVG 파일 경로
        center_text: 중앙 원에 표시할 텍스트
        colors: 색상 리스트
        size: SVG 크기
        
    Returns:
        str: 생성된 SVG 파일 경로
    """
    # 최대 5개 항목으로 제한
    limited_data = data[:5] if len(data) > 5 else data
    
    # 다이어그램 생성
    return generate_circular_diagram(limited_data, output_file, center_text, colors, size) 