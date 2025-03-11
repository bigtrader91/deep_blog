#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
통합된 SVG 다이어그램 생성 인터페이스 사용 예제
"""
import os
import argparse
from typing import Dict, List, Optional

from . import (
    DiagramType, 
    generate_diagram,
    generate_card_diagram,
    generate_image_diagram
)

def generate_example_diagrams(output_dir: str = "./outputs", pixabay_api_key: Optional[str] = None) -> None:
    """
    다양한 유형의 다이어그램 예제를 생성합니다.
    
    Args:
        output_dir: 출력 파일을 저장할 디렉토리
        pixabay_api_key: 픽사베이 API 키 (선택 사항)
    """
    # 출력 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 예제 데이터 - 한국 문화 콘텐츠 관련 정보
    main_title = "한국 문화 콘텐츠의 글로벌 경쟁력"
    sub_title_sections = [
        {
            "title": "한류의 국제적 영향력",
            "content": "K-팝, K-드라마, 영화 등 한국 문화 콘텐츠는 전 세계적으로 인기를 얻고 있으며, 국가 브랜드 가치 상승에 기여하고 있습니다."
        },
        {
            "title": "콘텐츠 산업의 경제적 효과",
            "content": "한국 콘텐츠 산업은 수출 증가와 관광객 유치 등 다양한 경제적 파급효과를 창출하며 국가 경제 성장에 기여합니다."
        },
        {
            "title": "디지털 플랫폼의 역할",
            "content": "넷플릭스, 유튜브 등 글로벌 디지털 플랫폼은 한국 콘텐츠의 국제적 확산을 가속화하는 중요한 채널로 작용합니다."
        },
        {
            "title": "콘텐츠 다양성과 혁신",
            "content": "장르의 다양성과 창의적인 스토리텔링은 한국 콘텐츠의 핵심 경쟁력으로, 국제 시장에서 차별화 요소로 작용합니다."
        }
    ]
    
    # 1. 통합 인터페이스를 사용한 기본 다이어그램 생성
    print("\n=== 기본 다이어그램 생성 ===")
    for diagram_type in ["card", "image"]:
        output_file = os.path.join(output_dir, f"{diagram_type}_diagram_example.svg")
        generate_diagram(
            diagram_type=diagram_type,  # type: ignore
            main_title=main_title,
            sub_title_sections=sub_title_sections,
            output_file=output_file
        )
        print(f"{diagram_type.capitalize()} 다이어그램 생성 완료: {output_file}")
    
    # 2. 개별 인터페이스를 사용한 커스터마이즈 다이어그램 생성
    print("\n=== 커스터마이즈 다이어그램 생성 ===")
    
    # 2-1. 카드 다이어그램 (배경색 및 카드색 변경)
    card_output = os.path.join(output_dir, "card_diagram_custom.svg")
    generate_card_diagram(
        main_title=main_title,
        sub_title_sections=sub_title_sections,
        output_file=card_output,
        background_color="#2C3E50",  # 어두운 배경색
        card_color="#ECF0F1",        # 밝은 카드색
        header_color="#ECF0F1",      # 밝은 헤더 텍스트색
        title_color="#2980B9",       # 파란색 제목
        content_color="#34495E"      # 어두운 회색 내용
    )
    print(f"커스텀 카드 다이어그램 생성 완료: {card_output}")
    
    # 2-2. 이미지 다이어그램 (사이즈 및 색상 변경)
    image_output = os.path.join(output_dir, "image_diagram_custom.svg")
    generate_image_diagram(
        main_title=main_title,
        sub_title_sections=sub_title_sections[:2],  # 이미지 다이어그램은 2개 이하의 섹션만 사용
        output_file=image_output,
        width=1000,
        height=1200,
        background_color="#F8F9FA",
        title_color="#1A237E",
        description_color="#37474F",
        number_bg_color="#3F51B5",
        pixabay_query="korean culture" if pixabay_api_key else None,
        pixabay_api_key=pixabay_api_key
    )
    print(f"커스텀 이미지 다이어그램 생성 완료: {image_output}")
    
    # 3. 섹션 수에 따른 자동 다이어그램 선택 테스트
    print("\n=== 섹션 수에 따른 자동 선택 테스트 ===")
    
    # 3-1. 2개 섹션 (이미지 다이어그램으로 자동 선택)
    auto_select_image = os.path.join(output_dir, "auto_select_image.svg")
    generate_diagram(
        diagram_type="auto",  # type: ignore
        main_title="적은 섹션 예제 (자동으로 이미지 다이어그램 선택)",
        sub_title_sections=sub_title_sections[:2],  # 2개만 사용
        output_file=auto_select_image
    )
    print(f"적은 섹션 (2개) 자동 선택 테스트 완료: {auto_select_image}")
    
    # 3-2. 4개 섹션 (카드 다이어그램으로 자동 선택)
    auto_select_card = os.path.join(output_dir, "auto_select_card.svg")
    generate_diagram(
        diagram_type="auto",  # type: ignore
        main_title="많은 섹션 예제 (자동으로 카드 다이어그램 선택)",
        sub_title_sections=sub_title_sections,  # 4개 모두 사용
        output_file=auto_select_card
    )
    print(f"많은 섹션 (4개) 자동 선택 테스트 완료: {auto_select_card}")
    
    # 4. 오류 처리 테스트
    print("\n=== 오류 처리 테스트 ===")
    
    # 4-1. 누락된 필드가 있는 데이터
    incomplete_data_output = os.path.join(output_dir, "incomplete_data_diagram.svg")
    incomplete_data = [
        {"title": "제목만 있는 섹션"},
        {"description": "content 대신 description 필드가 있는 섹션"},
        {"text": "text 필드만 있는 섹션"}
    ]
    generate_diagram(
        diagram_type="card",
        main_title="누락된 필드 테스트",
        sub_title_sections=incomplete_data,  # type: ignore
        output_file=incomplete_data_output
    )
    print(f"누락 필드 테스트 완료: {incomplete_data_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SVG 다이어그램 생성 예제")
    parser.add_argument('--output-dir', default='./outputs', help='출력 디렉토리 경로')
    parser.add_argument('--pixabay-key', help='픽사베이 API 키(선택 사항)')
    args = parser.parse_args()
    
    generate_example_diagrams(args.output_dir, args.pixabay_key)
    print("\n모든 예제 다이어그램 생성이 완료되었습니다.") 