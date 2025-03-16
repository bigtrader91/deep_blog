"""
썸네일 생성 모듈

블로그 게시물, 소셜 미디어 등에 사용할 수 있는 썸네일 이미지 생성 기능을 제공합니다.
다양한 스타일, 레이아웃 및 효과를 지원합니다.
"""

import os
import random
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np

from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)

# 기본 설정값
DEFAULT_CONFIG = {
    "width": 1200,           # 기본 이미지 너비
    "height": 630,           # 기본 이미지 높이 (소셜 미디어에 최적화)
    "padding": 60,           # 여백
    "font_path": "resources/fonts/NanumSquare.ttf",  # 기본 폰트 경로
    "title_font_size": 72,   # 제목 폰트 크기
    "subtitle_font_size": 36, # 부제목 폰트 크기
    "line_spacing": 1.5,     # 줄 간격
    "background_color": (255, 255, 255),  # 배경색 (흰색)
    "text_color": None,      # 텍스트 색상 (자동 계산)
    "blur_radius": 5.0,      # 블러 효과 강도
    "brightness_factor": 0.7, # 밝기 조정 계수
    "overlay_opacity": 0.3,  # 오버레이 투명도
    "background_images_dir": "resources/background_images",  # 배경 이미지 디렉토리
    "output_dir": "output/images",  # 출력 디렉토리
}

def sanitize_filename(text: str) -> str:
    """
    파일명으로 사용할 수 있도록 텍스트를 정리합니다.
    
    Args:
        text: 정리할 텍스트
        
    Returns:
        str: 정리된 파일명
    """
    # 파일명에 사용할 수 없는 문자 제거
    filename = re.sub(r'[\\/*?:"<>|]', "", text)
    # 공백을 언더스코어로 변환
    filename = re.sub(r'\s+', "_", filename.strip())
    # 최대 길이 제한
    if len(filename) > 100:
        filename = filename[:97] + "..."
    return filename

def get_average_color(image: Image.Image) -> Tuple[int, int, int]:
    """
    이미지의 평균 색상을 계산합니다.
    
    Args:
        image: PIL 이미지
        
    Returns:
        Tuple[int, int, int]: RGB 평균 색상
    """
    try:
        # 이미지를 numpy 배열로 변환
        img_array = np.array(image)
        # 평균 계산
        average = img_array.mean(axis=(0, 1))
        return (int(average[0]), int(average[1]), int(average[2]))
    except:
        # numpy가 없거나 계산 실패시 기존 방식 사용
        npixels = image.width * image.height
        cols = image.getcolors(npixels)
        sumRGB = [(x[0] * x[1][0], x[0] * x[1][1], x[0] * x[1][2]) for x in cols]
        avg = tuple([int(sum(x) / npixels) for x in zip(*sumRGB)])
        return avg

def get_contrast_color(background_color: Tuple[int, int, int], brightness_factor: float = 1.0) -> Tuple[int, int, int]:
    """
    배경색에 대비되는 텍스트 색상을 계산합니다.
    
    Args:
        background_color: 배경색 RGB 튜플
        brightness_factor: 밝기 조정 계수
        
    Returns:
        Tuple[int, int, int]: 대비 색상 RGB 튜플
    """
    # 배경색의 밝기 계산 (YIQ 공식 사용)
    luminance = (
        0.299 * background_color[0]
        + 0.587 * background_color[1]
        + 0.114 * background_color[2]
    )
    
    # 밝기 기준점 조정
    adjusted_threshold = 128 * brightness_factor
    
    # 밝은 배경에는 어두운 텍스트, 어두운 배경에는 밝은 텍스트
    if luminance > adjusted_threshold:
        return (0, 0, 0)  # 검은색
    else:
        return (255, 255, 255)  # 흰색

def split_text_into_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    텍스트를 최대 너비에 맞게 여러 줄로 분할합니다.
    
    Args:
        text: 분할할 텍스트
        font: 사용할 폰트
        max_width: 최대 줄 너비
        
    Returns:
        List[str]: 분할된 텍스트 줄 목록
    """
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        # 현재 단어 너비 계산
        word_width = font.getlength(word)
        
        # 단어가 최대 너비보다 긴 경우 분할
        if word_width > max_width:
            # 현재 줄이 있으면 추가
            if current_line:
                lines.append(current_line)
                current_line = ""
            
            # 긴 단어 분할
            temp_word = word
            while temp_word:
                for i in range(len(temp_word), 0, -1):
                    segment = temp_word[:i]
                    if font.getlength(segment) <= max_width:
                        lines.append(segment)
                        temp_word = temp_word[i:]
                        break
                # 안전장치
                if len(temp_word) > 0 and i == 1:
                    lines.append(temp_word[0])
                    temp_word = temp_word[1:]
        else:
            # 현재 줄에 단어 추가 가능한지 확인
            test_line = current_line + " " + word if current_line else word
            if font.getlength(test_line) <= max_width:
                current_line = test_line
            else:
                # 현재 줄이 꽉 찼으므로 새 줄 시작
                if current_line:
                    lines.append(current_line)
                current_line = word
    
    # 마지막 줄 추가
    if current_line:
        lines.append(current_line)
    
    return lines

def create_overlay(size: Tuple[int, int], color: Tuple[int, int, int], opacity: float) -> Image.Image:
    """
    반투명 오버레이를 생성합니다.
    
    Args:
        size: 오버레이 크기 (width, height)
        color: 오버레이 색상
        opacity: 불투명도 (0.0 ~ 1.0)
        
    Returns:
        Image.Image: 오버레이 이미지
    """
    overlay = Image.new("RGBA", size, color + (int(255 * opacity),))
    return overlay

def add_watermark(image: Image.Image, watermark_text: str, font_path: str, font_size: int = 20, 
                 position: str = "bottom-right", opacity: float = 0.5) -> Image.Image:
    """
    이미지에 워터마크를 추가합니다.
    
    Args:
        image: 워터마크를 추가할 이미지
        watermark_text: 워터마크 텍스트
        font_path: 폰트 파일 경로
        font_size: 폰트 크기
        position: 워터마크 위치 ('bottom-right', 'bottom-left', 'top-right', 'top-left', 'center')
        opacity: 불투명도 (0.0 ~ 1.0)
        
    Returns:
        Image.Image: 워터마크가 추가된 이미지
    """
    # 이미지를 RGBA 모드로 변환
    image = image.convert("RGBA")
    watermark = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)
    
    # 폰트 설정
    font = ImageFont.truetype(font_path, font_size)
    
    # 텍스트 크기 계산
    bbox = font.getbbox(watermark_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 위치 설정
    padding = 10
    if position == "bottom-right":
        position = (image.width - text_width - padding, image.height - text_height - padding)
    elif position == "bottom-left":
        position = (padding, image.height - text_height - padding)
    elif position == "top-right":
        position = (image.width - text_width - padding, padding)
    elif position == "top-left":
        position = (padding, padding)
    else:  # center
        position = ((image.width - text_width) // 2, (image.height - text_height) // 2)
    
    # 워터마크 그리기
    draw.text(position, watermark_text, font=font, fill=(255, 255, 255, int(255 * opacity)))
    
    # 워터마크와 원본 이미지 합치기
    return Image.alpha_composite(image, watermark)

def create_thumbnail(
    title: str,
    subtitle: Optional[str] = None,
    config: Optional[Dict] = None,
    background_image: Optional[str] = None,
    watermark: Optional[str] = None,
    style: str = "standard"
) -> str:
    """
    제목과 부제목으로 썸네일 이미지를 생성합니다.
    
    Args:
        title: 제목 텍스트
        subtitle: 부제목 텍스트 (선택 사항)
        config: 구성 설정 (선택 사항)
        background_image: 배경 이미지 경로 (선택 사항)
        watermark: 워터마크 텍스트 (선택 사항)
        style: 썸네일 스타일 ('standard', 'minimal', 'gradient', 'dark')
        
    Returns:
        str: 생성된 이미지 파일 경로
    """
    # 설정 병합
    cfg = DEFAULT_CONFIG.copy()
    if config:
        cfg.update(config)
    
    # 스타일별 설정 조정
    if style == "minimal":
        cfg["blur_radius"] = 0
        cfg["overlay_opacity"] = 0
        cfg["background_color"] = (255, 255, 255)
    elif style == "gradient":
        cfg["blur_radius"] = 10
        cfg["overlay_opacity"] = 0.5
        cfg["brightness_factor"] = 0.6
    elif style == "dark":
        cfg["background_color"] = (30, 30, 30)
        cfg["blur_radius"] = 3
        cfg["brightness_factor"] = 0.5
    
    # 디렉토리 확인 및 생성
    if not os.path.exists(cfg["output_dir"]):
        os.makedirs(cfg["output_dir"], exist_ok=True)
    
    # 이미지 크기 설정
    img_width = cfg["width"]
    img_height = cfg["height"]
    padding = cfg["padding"]
    
    # 이미지 생성
    try:
        # 배경 이미지 설정
        if background_image and os.path.exists(background_image):
            # 지정된 배경 이미지 사용
            img = Image.open(background_image).convert("RGB")
            img = img.resize((img_width, img_height))
            bg_avg_color = get_average_color(img)
        elif os.path.exists(cfg["background_images_dir"]):
            # 랜덤 배경 이미지 선택
            background_images = [f for f in os.listdir(cfg["background_images_dir"]) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if background_images:
                random_bg = random.choice(background_images)
                bg_path = os.path.join(cfg["background_images_dir"], random_bg)
                img = Image.open(bg_path).convert("RGB")
                img = img.resize((img_width, img_height))
                bg_avg_color = get_average_color(img)
            else:
                # 배경 이미지가 없으면 단색 배경 사용
                img = Image.new("RGB", (img_width, img_height), color=cfg["background_color"])
                bg_avg_color = cfg["background_color"]
        else:
            # 기본 단색 배경
            img = Image.new("RGB", (img_width, img_height), color=cfg["background_color"])
            bg_avg_color = cfg["background_color"]
        
        # 이미지 효과 적용
        # 밝기 조정
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(cfg["brightness_factor"])
        
        # 블러 효과
        if cfg["blur_radius"] > 0:
            img = img.filter(ImageFilter.GaussianBlur(cfg["blur_radius"]))
        
        # 그라데이션 스타일인 경우 오버레이 추가
        if style == "gradient":
            gradient = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
            draw_gradient = ImageDraw.Draw(gradient)
            for y in range(img_height):
                # 아래에서 위로 갈수록 더 투명해지는 그라데이션
                opacity = 200 - int(150 * (y / img_height))
                draw_gradient.line([(0, y), (img_width, y)], fill=(0, 0, 0, opacity))
            
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, gradient)
            img = img.convert("RGB")
        
        # 반투명 오버레이 추가 (텍스트 가독성 향상)
        if cfg["overlay_opacity"] > 0:
            overlay_color = (0, 0, 0) if style == "dark" else (255, 255, 255)
            overlay = create_overlay((img_width, img_height), overlay_color, cfg["overlay_opacity"])
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            img = img.convert("RGB")
        
        # 텍스트 색상 결정
        text_color = cfg["text_color"] if cfg["text_color"] else get_contrast_color(bg_avg_color, cfg["brightness_factor"])
        
        # 이미지에 텍스트 추가
        draw = ImageDraw.Draw(img)
        
        # 제목 텍스트 처리
        effective_width = img_width - (2 * padding)
        title_font_size = cfg["title_font_size"]
        title_font = ImageFont.truetype(cfg["font_path"], title_font_size)
        
        # 제목이 너무 길면 폰트 크기 조정
        title_lines = split_text_into_lines(title, title_font, effective_width)
        while title_font_size > 24 and len(title_lines) > 3:
            title_font_size -= 4
            title_font = ImageFont.truetype(cfg["font_path"], title_font_size)
            title_lines = split_text_into_lines(title, title_font, effective_width)
        
        # 제목 행 높이 계산
        title_bbox = title_font.getbbox(title_lines[0])
        title_line_height = (title_bbox[3] - title_bbox[1]) * cfg["line_spacing"]
        
        # 부제목 처리
        subtitle_lines = []
        subtitle_line_height = 0
        if subtitle:
            subtitle_font = ImageFont.truetype(cfg["font_path"], cfg["subtitle_font_size"])
            subtitle_lines = split_text_into_lines(subtitle, subtitle_font, effective_width)
            subtitle_bbox = subtitle_font.getbbox(subtitle_lines[0])
            subtitle_line_height = (subtitle_bbox[3] - subtitle_bbox[1]) * cfg["line_spacing"]
        
        # 전체 텍스트 높이 계산
        total_height = (len(title_lines) * title_line_height) + (30 if subtitle else 0) + (len(subtitle_lines) * subtitle_line_height)
        
        # 텍스트 시작 y좌표 계산 (수직 중앙 정렬)
        current_y = (img_height - total_height) / 2
        
        # 제목 그리기
        for line in title_lines:
            # 텍스트 폭 계산
            title_bbox = title_font.getbbox(line)
            width = title_bbox[2] - title_bbox[0]
            # 수평 중앙 정렬
            x = (img_width - width) / 2
            draw.text((x, current_y), line, font=title_font, fill=text_color)
            current_y += title_line_height
        
        # 부제목과 제목 사이 간격
        if subtitle:
            current_y += 30
            
            # 부제목 그리기
            for line in subtitle_lines:
                subtitle_bbox = subtitle_font.getbbox(line)
                width = subtitle_bbox[2] - subtitle_bbox[0]
                x = (img_width - width) / 2
                draw.text((x, current_y), line, font=subtitle_font, fill=text_color)
                current_y += subtitle_line_height
        
        # 워터마크 추가
        if watermark:
            img = img.convert("RGBA")
            img = add_watermark(
                img, 
                watermark, 
                cfg["font_path"], 
                font_size=18, 
                position="bottom-right"
            )
        
        # 이미지를 RGB 모드로 변환 (저장을 위해)
        img = img.convert("RGB")
        
        # 파일명 생성 및 저장
        filename = sanitize_filename(title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = os.path.join(cfg["output_dir"], f"thumbnail_{filename}_{timestamp}.jpg")
        
        img.save(img_path, quality=95)
        logger.info(f"썸네일 생성 완료: {img_path}")
        
        return img_path
        
    except Exception as e:
        logger.error(f"썸네일 생성 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본 이미지 생성
        try:
            img = Image.new("RGB", (img_width, img_height), (200, 200, 200))
            draw = ImageDraw.Draw(img)
            err_font = ImageFont.truetype(cfg["font_path"], 30)
            draw.text((50, img_height/2 - 15), f"썸네일 생성 오류: {str(e)[:50]}...", font=err_font, fill=(80, 80, 80))
            
            error_path = os.path.join(cfg["output_dir"], f"error_thumbnail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            img.save(error_path)
            return error_path
        except:
            logger.critical("오류 이미지 생성 실패")
            return ""

def create_social_thumbnail(
    title: str, 
    platform: str = "blog", 
    keywords: Optional[List[str]] = None,
    background_image: Optional[str] = None,
    logo_path: Optional[str] = None,
    author: Optional[str] = None
) -> str:
    """
    소셜 미디어용 썸네일을 생성합니다.
    
    Args:
        title: 제목 텍스트
        platform: 타겟 플랫폼 ('blog', 'facebook', 'twitter', 'instagram')
        keywords: 강조할 키워드 목록
        background_image: 배경 이미지 경로
        logo_path: 로고 이미지 경로
        author: 작성자 이름
        
    Returns:
        str: 생성된 이미지 파일 경로
    """
    # 플랫폼별 크기 설정
    platform_configs = {
        "blog": {"width": 500, "height": 500},     # 블로그 기본 크기
        "facebook": {"width": 1200, "height": 630}, # 페이스북 권장 크기
        "twitter": {"width": 1200, "height": 675},  # 트위터 권장 크기
        "instagram": {"width": 1080, "height": 1080}, # 인스타그램 정사각형
    }
    
    config = DEFAULT_CONFIG.copy()
    if platform in platform_configs:
        config.update(platform_configs[platform])
    
    # 키워드가 있으면 부제목으로 사용
    subtitle = None
    if keywords and len(keywords) > 0:
        subtitle = " · ".join(keywords[:3])  # 최대 3개 키워드만 사용
    
    # 워터마크에 작성자 정보 포함
    watermark = None
    if author:
        watermark = f"Created by {author}"
    
    # 스타일 결정 (플랫폼별로 다른 스타일 사용)
    style_map = {
        "blog": "standard",
        "facebook": "gradient",
        "twitter": "minimal",
        "instagram": "dark"
    }
    style = style_map.get(platform, "standard")
    
    # 로고가 있으면 설정에 추가
    if logo_path and os.path.exists(logo_path):
        # 로고 처리 로직은 create_thumbnail 함수 내부에서 구현해야 함
        # 현재 구현에서는 로고를 지원하지 않으므로 무시됨
        pass
    
    # 썸네일 생성
    return create_thumbnail(
        title=title,
        subtitle=subtitle,
        config=config,
        background_image=background_image,
        watermark=watermark,
        style=style
    )
