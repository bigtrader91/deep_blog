#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
텍스트에서 다이어그램을 생성하는 통합 모듈입니다.

이 모듈은 텍스트를 분석하여 적절한 다이어그램 유형을 선택하고,
선택된 유형에 따라 SVG 다이어그램을 생성합니다.
"""
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Tuple, Any

# 상대 경로 임포트를 위한 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 이제 상대 경로 임포트
from src.generator.text.select_diagram import select_diagram, DiagramResult
from src.generator.svg import generate_diagram
from src.generator.svg.responsive_utils import create_simple_svg_fallback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_diagram_from_text(
    text: str,
    output_file: str,
    pixabay_api_key: Optional[str] = None,
    **kwargs: Any
) -> Tuple[str, DiagramResult]:
    """
    텍스트를 분석하여 적절한 다이어그램을 생성합니다.
    
    Args:
        text: 분석할 텍스트
        output_file: 출력 SVG 파일 경로
        pixabay_api_key: 픽사베이 API 키 (선택 사항)
        **kwargs: 다이어그램 생성에 사용할 추가 매개변수
        
    Returns:
        Tuple[str, DiagramResult]: (생성된 SVG 파일 경로, 다이어그램 정보)
    """
    # 텍스트 분석하여 다이어그램 정보 얻기
    logger.info("텍스트 분석 중...")
    try:
        diagram_info = select_diagram(text)
        logger.info(f"선택된 다이어그램 유형: {diagram_info.diagram_name}")
    except Exception as e:
        logger.error(f"다이어그램 정보 추출 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본값 사용
        logger.warning("기본 다이어그램 정보를 사용합니다.")
        diagram_info = DiagramResult.with_fallback(
            diagram_name="card",
            main_title=text.split('\n')[0][:30] + "..." if text else "텍스트 분석 결과",
            sections=None
        )
    
    # DiagramContent 객체를 딕셔너리로 변환
    sections_dict = []
    for section in diagram_info.sub_title_sections:
        sections_dict.append({
            "title": section.title,
            "content": section.content
        })
    
    # 다이어그램 생성을 위한 매개변수 준비
    if pixabay_api_key:
        kwargs['pixabay_api_key'] = pixabay_api_key
        # 검색어가 지정되지 않았을 경우 메인 타이틀 사용
        if 'pixabay_query' not in kwargs:
            keywords = diagram_info.main_title.split()
            kwargs['pixabay_query'] = ' '.join(keywords[:3]) if len(keywords) > 3 else diagram_info.main_title
    
    # 출력 디렉토리 생성
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 다이어그램 유형에 따라 크기 매개변수 처리
    diagram_type = diagram_info.diagram_name
    
    # 기본 크기 매개변수 설정
    if diagram_type == "card":
        # 카드 다이어그램은 size 매개변수 사용
        if 'width' in kwargs and 'size' not in kwargs:
            kwargs['size'] = kwargs.pop('width')
        if 'height' in kwargs:
            kwargs.pop('height')  # 높이는 무시 (카드 다이어그램은 size만 사용)
    

    elif diagram_type == "image":
        # 이미지 다이어그램은 width와 height 매개변수 사용
        # 기본값은 이미 diagram_utils.py에서 처리됨
        pass
    
    # 다이어그램 생성
    logger.info(f"다이어그램 생성 중: {output_file}")
    try:
        svg_path = generate_diagram(
            diagram_type=diagram_info.diagram_name,
            main_title=diagram_info.main_title,
            sub_title_sections=sections_dict,  # 딕셔너리 리스트로 변환된 섹션 사용
            output_file=output_file,
            **kwargs
        )
        logger.info(f"다이어그램 생성 완료: {svg_path}")
        return svg_path, diagram_info
    except Exception as e:
        logger.error(f"다이어그램 생성 중 오류 발생: {str(e)}")
        # 폴백 다이어그램 생성 시도
        fallback_output = output_file.replace(".svg", "_fallback.svg")
        try:
            # 간단한 폴백 SVG 생성
            logger.warning(f"폴백 다이어그램 생성 중: {fallback_output}")
            svg_path = create_simple_svg_fallback(
                output_file=fallback_output,
                error_message=str(e),
                main_title=f"오류 발생: {diagram_info.main_title}"
            )
            logger.info(f"폴백 다이어그램 생성 완료: {svg_path}")
            return svg_path, diagram_info
        except Exception as inner_e:
            logger.error(f"폴백 다이어그램 생성 중 오류 발생: {str(inner_e)}")
            raise

def main() -> None:
    """명령줄에서 실행될 때의 메인 함수"""
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description="텍스트에서 다이어그램을 생성합니다.")
    parser.add_argument('input_file', help='입력 텍스트 파일 경로')
    parser.add_argument('--output', '-o', default='diagram_output.svg', help='출력 SVG 파일 경로')
    parser.add_argument('--pixabay-key', help='픽사베이 API 키')
    parser.add_argument('--width', type=int, default=800, help='SVG 너비')
    parser.add_argument('--height', type=int, default=1000, help='SVG 높이')
    parser.add_argument('--bg-color', default='#FFFFFF', help='배경색 (예: #FFFFFF)')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    args = parser.parse_args()
    
    # 디버그 모드 설정
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("디버그 모드 활성화됨")
    
    # 입력 파일에서 텍스트 읽기
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logger.error(f"파일 읽기 실패: {str(e)}")
        return
    
    # 다이어그램 생성
    try:
        svg_path, diagram_info = generate_diagram_from_text(
            text=text,
            output_file=args.output,
            pixabay_api_key=args.pixabay_key,
            width=args.width,
            height=args.height,
            background_color=args.bg_color
        )
        print(f"다이어그램 생성 완료: {svg_path}")
        print(f"다이어그램 유형: {diagram_info.diagram_name}")
        print(f"메인 타이틀: {diagram_info.main_title}")
        print(f"섹션 수: {len(diagram_info.sub_title_sections)}개")
    except Exception as e:
        logger.error(f"다이어그램 생성 실패: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 