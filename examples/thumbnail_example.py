"""
썸네일 생성 예제

이 스크립트는 다양한 종류의 썸네일을 생성하는 예제를 보여줍니다.
"""
import os
import sys
from typing import List

# 모듈 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 썸네일 생성기 임포트
from src.core.content.generator.thumnail import create_thumbnail, create_social_thumbnail

def create_directory_if_not_exists(directory_path: str) -> None:
    """
    디렉토리가 존재하지 않으면 생성합니다.
    
    Args:
        directory_path: 생성할 디렉토리 경로
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
        print(f"디렉토리 생성: {directory_path}")

def setup_resources() -> None:
    """
    필요한 리소스 디렉토리를 설정합니다.
    """
    # 필요한 디렉토리 생성
    create_directory_if_not_exists("resources/fonts")
    create_directory_if_not_exists("resources/background_images")
    create_directory_if_not_exists("output/images")
    
    # 폰트 파일 확인 (예시)
    font_path = "resources/fonts/NanumSquare.ttf"
    if not os.path.exists(font_path):
        print(f"경고: 폰트 파일이 없습니다: {font_path}")
        print("나눔스퀘어 폰트를 다운로드하여 리소스 폴더에 넣어주세요.")
        print("다운로드 링크: https://hangeul.naver.com/font")

def example_basic_thumbnail() -> None:
    """
    기본 썸네일 생성 예제
    """
    print("\n[예제 1] 기본 썸네일 생성")
    
    # 기본 썸네일 생성
    title = "건강한 생활을 위한 10가지 습관"
    subtitle = "일상에서 쉽게 실천할 수 있는 건강 팁"
    
    # 커스텀 설정
    config = {
        "title_font_size": 65,
        "subtitle_font_size": 30,
        "font_path": "resources/fonts/NanumSquare.ttf"  # 폰트 경로 수정
    }
    
    # 썸네일 생성
    thumbnail_path = create_thumbnail(
        title=title,
        subtitle=subtitle,
        config=config,
        style="standard"
    )
    
    if thumbnail_path:
        print(f"썸네일 생성 완료: {thumbnail_path}")
    else:
        print("썸네일 생성 실패")

def example_styled_thumbnails() -> None:
    """
    여러 스타일의 썸네일 생성 예제
    """
    print("\n[예제 2] 다양한 스타일의 썸네일 생성")
    
    title = "프로그래밍 언어 트렌드 2023"
    subtitle = "데이터 분석 | 머신러닝 | 웹 개발"
    
    # 다양한 스타일로 생성
    styles = ["minimal", "gradient", "dark", "standard"]
    
    for style in styles:
        print(f"스타일 '{style}' 썸네일 생성 중...")
        
        thumbnail_path = create_thumbnail(
            title=title,
            subtitle=subtitle,
            style=style,
            watermark="© Tech Blog 2023"
        )
        
        if thumbnail_path:
            print(f"'{style}' 스타일 썸네일 생성 완료: {thumbnail_path}")
        else:
            print(f"'{style}' 스타일 썸네일 생성 실패")

def example_social_media_thumbnails() -> None:
    """
    소셜 미디어 플랫폼별 썸네일 생성 예제
    """
    print("\n[예제 3] 소셜 미디어 썸네일 생성")
    
    title = "인공지능과 함께하는 미래 사회"
    keywords = ["AI", "미래기술", "디지털 트랜스포메이션"]
    
    # 다양한 플랫폼용 썸네일 생성
    platforms = ["blog", "facebook", "twitter", "instagram"]
    
    for platform in platforms:
        print(f"{platform.capitalize()} 썸네일 생성 중...")
        
        thumbnail_path = create_social_thumbnail(
            title=title,
            platform=platform,
            keywords=keywords,
            author="AI 연구소"
        )
        
        if thumbnail_path:
            print(f"{platform.capitalize()} 썸네일 생성 완료: {thumbnail_path}")
        else:
            print(f"{platform.capitalize()} 썸네일 생성 실패")

def main() -> None:
    """
    메인 실행 함수
    """
    print("=== 썸네일 생성 예제 ===")
    
    # 리소스 디렉토리 설정
    setup_resources()
    
    # 예제 1: 기본 썸네일 생성
    example_basic_thumbnail()
    
    # 예제 2: 다양한 스타일의 썸네일 생성
    example_styled_thumbnails()
    
    # 예제 3: 소셜 미디어 썸네일 생성
    example_social_media_thumbnails()
    
    print("\n모든 예제 실행 완료")

if __name__ == "__main__":
    main() 