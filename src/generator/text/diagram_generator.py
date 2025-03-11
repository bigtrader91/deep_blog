# src.generator.text.diagram_generator.py

"""
텍스트에서 다이어그램을 생성하는 통합 모듈입니다.

이 모듈은 텍스트를 분석하여 적절한 다이어그램 유형을 선택하고,
선택된 유형에 따라 SVG 다이어그램을 생성합니다.
"""
import os
import sys
import argparse
import logging
import glob
import random
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
    logger.info("텍스트 분석 중...")

    # 1) LLM 통해 다이어그램 정보 추출
    try:
        diagram_info = select_diagram(text)
        logger.info(f"LLM이 선택한 다이어그램 유형(초안): {diagram_info.diagram_name}")
    except Exception as e:
        logger.error(f"다이어그램 정보 추출 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본값 사용
        logger.warning("기본 다이어그램 정보를 사용합니다.")
        diagram_info = DiagramResult.with_fallback(
            diagram_name="card",
            main_title=text.split('\n')[0][:30] + "..." if text else "텍스트 분석 결과",
            sections=None
        )
    
    # 2) DiagramResult → dict로 변환해서 'sub_title_sections' + 'keywords' 확인
    diagram_data = diagram_info.to_dict()
    # 구조 예: {
    #   "diagram_name": "card" or "image",
    #   "main_title": "...",
    #   "sub_title_sections": [
    #       {"title": "...", "content": "...", "keywords": [ ... ]}, ...
    #   ],
    #   "keywords": [ ... ]
    # }

    # 3) 만약 sub_title_sections 중 일부가 keywords가 비어있으면
    #    LLM이 준 전체 keywords를 채워넣음 (선택적 로직)
    for section_dict in diagram_data["sub_title_sections"]:
        if "keywords" not in section_dict or not section_dict["keywords"]:
            section_dict["keywords"] = diagram_data["keywords"]

    # 4) 다이어그램 생성시 사용할 섹션 리스트
    sections_dict = diagram_data["sub_title_sections"]

    # 5) 픽사베이 관련 매개변수 설정
    #    - 여기서 'auto:' 모드를 사용하면, 다이어그램 모듈이 섹션 keywords로부터 쿼리를 생성
    if pixabay_api_key:
        kwargs["pixabay_api_key"] = pixabay_api_key
        # 항상 auto 모드로 설정 (키워드를 반영)
        kwargs["pixabay_query"] = "auto:"
        logger.info("픽사베이 검색어를 auto:로 설정 (섹션 키워드 자동 활용)")

    # 6) 출력 디렉토리 생성
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 7) 다이어그램 유형에 따른 매개변수 처리
    diagram_type = diagram_data["diagram_name"]

    # (a) 카드 다이어그램은 size만 사용
    if diagram_type == "card":
        if 'width' in kwargs and 'size' not in kwargs:
            kwargs['size'] = kwargs.pop('width')
        if 'height' in kwargs:
            kwargs.pop('height', None)

    # (b) 이미지 다이어그램은 width, height 사용 → 추가 처리 없음

    # 8) 랜덤 효과 (예: 어두움, 블러)
    #    이미 kwargs에 없다면, 여기서 추가 가능
    if "card_darkness" not in kwargs:
        kwargs["card_darkness"] = random.uniform(0.5, 0.9)
    if "card_blur" not in kwargs:
        kwargs["card_blur"] = random.uniform(1.0, 5.0)
    logger.info(f"랜덤 효과: 어두움={kwargs['card_darkness']:.2f}, 블러={kwargs['card_blur']:.2f}")

    # 9) 실제 다이어그램 생성
    logger.info(f"다이어그램 생성 중: {output_file}")
    try:
        svg_path = generate_diagram(
            diagram_type=diagram_type,                 # "card" or "image"
            main_title=diagram_data["main_title"],
            sub_title_sections=sections_dict,
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
            logger.warning(f"폴백 다이어그램 생성 중: {fallback_output}")
            svg_path = create_simple_svg_fallback(
                output_file=fallback_output,
                error_message=str(e),
                main_title=f"오류 발생: {diagram_data['main_title']}"
            )
            logger.info(f"폴백 다이어그램 생성 완료: {svg_path}")
            return svg_path, diagram_info
        except Exception as inner_e:
            logger.error(f"폴백 다이어그램 생성 중 오류 발생: {str(inner_e)}")
            raise


def main() -> None:
    """명령줄에서 실행될 때의 메인 함수"""
    parser = argparse.ArgumentParser(description="텍스트에서 다이어그램을 생성합니다.")
    parser.add_argument('input_file', help='입력 텍스트 파일 경로')
    parser.add_argument('--output', '-o', default='diagram_output.svg', help='출력 SVG 파일 경로')
    parser.add_argument('--pixabay-key', help='픽사베이 API 키')
    parser.add_argument('--width', type=int, default=800, help='SVG 너비/높이 (1:1 비율)')
    parser.add_argument('--bg-color', default='#111111', help='배경색 (예: #111111)')
    parser.add_argument('--background-image', help='배경 이미지 (SVG 전체 배경)')
    parser.add_argument('--random-bg-image', help='배경 이미지를 랜덤하게 선택할 디렉토리 (*.jpg, *.png, *.jpeg)')
    parser.add_argument('--bg-opacity', type=float, default=0.6, help='배경 이미지 투명도 (0.0-1.0)')
    parser.add_argument('--debug', action='store_true', help='디버그 모드 활성화')
    args = parser.parse_args()

    # 디버그 모드
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("디버그 모드 활성화됨")

    # 입력 파일 읽기
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logger.error(f"파일 읽기 실패: {str(e)}")
        sys.exit(1)

    # 1:1 비율로만 사용
    size = args.width

    # kwargs: 다이어그램 생성 시 전달할 매개변수
    kwargs = {
        "size": size,
        "background_color": args.bg_color,
        "enable_card_backgrounds": False,
        "header_image": None,
    }

    # 픽사베이 키가 있으면 -> API 키 전달 + auto: 모드에서 키워드 사용
    if args.pixabay_key:
        kwargs["pixabay_api_key"] = args.pixabay_key
        # 여기서는 직접 pixabay_query 설정하지 않고, generate_diagram_from_text 내에서 auto:로 설정

    # 배경 이미지 설정
    if args.random_bg_image and os.path.isdir(args.random_bg_image):
        # 디렉토리 내 임의 파일 선택
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.svg']:
            images.extend(glob.glob(os.path.join(args.random_bg_image, ext)))
        if images:
            rand_bg = random.choice(images)
            kwargs["background_image"] = rand_bg
            kwargs["background_image_opacity"] = args.bg_opacity
            logger.info(f"랜덤 배경 이미지 선택: {rand_bg}")
    elif args.background_image:
        kwargs["background_image"] = args.background_image
        kwargs["background_image_opacity"] = args.bg_opacity

    # 실제 다이어그램 생성
    try:
        svg_path, diagram_info = generate_diagram_from_text(
            text=text,
            output_file=args.output,
            **kwargs
        )
        print(f"다이어그램 생성 완료: {svg_path}")
        print(f"다이어그램 유형: {diagram_info.diagram_name}")
        print(f"메인 타이틀: {diagram_info.main_title}")
        print(f"섹션 수: {len(diagram_info.sub_title_sections)}개")

    except Exception as e:
        logger.error(f"다이어그램 생성 실패: {str(e)}")
        sys.exit(1)

    # 사용 예시 출력
    print("\n[ 사용 예시 ]")
    print("1. 기본 사용법 (픽사베이 배경 이미지 자동 활용):")
    print("   python -m src.generator.text.diagram_generator input.txt --output output.svg --pixabay-key YOUR_KEY")
    print("\n2. 로컬 배경 이미지 적용:")
    print("   python -m src.generator.text.diagram_generator input.txt --output output.svg --background-image /path/to/img.jpg --bg-opacity 0.6")
    print("\n3. 디렉토리에서 랜덤 배경 이미지:")
    print("   python -m src.generator.text.diagram_generator input.txt --output output.svg --random-bg-image images/backgrounds/")
    print("\n4. 디버그 모드:")
    print("   python -m src.generator.text.diagram_generator input.txt --output output.svg --pixabay-key YOUR_KEY --debug")


if __name__ == "__main__":
    main()
