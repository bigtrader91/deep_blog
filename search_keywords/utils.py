# utils.py
from PySide6.QtCore import QObject, Signal
from bs4 import BeautifulSoup
import requests
import os
from PIL import Image, ImageDraw, ImageFont
import hashlib
import hmac
import base64
from fake_useragent import UserAgent
import concurrent.futures
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import os
from datetime import datetime
import re
import json
import urllib.request
import urllib.parse
import pandas as pd
import chromedriver_autoinstaller
import zipfile
import io
import random
from urllib.parse import urlparse, parse_qs
from logger import log  # log 함수만 import

def install_and_extract_chromedriver():
    """
    크롬 버전에 맞춰 chromedriver를 자동 설치/업데이트하고
    해당 드라이버 경로를 반환합니다.
    """
    chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
    chrome_folder_path = os.path.join(os.getcwd(), chrome_ver)
    if not os.path.exists(chrome_folder_path):
        os.makedirs(chrome_folder_path)

    extracted_folder_path = os.path.join(chrome_folder_path, 'chromedriver-win64')
    driver_path = os.path.join(extracted_folder_path, 'chromedriver.exe')

    if os.path.exists(driver_path):
        print(f"chromedriver is installed: {driver_path}")
    else:
        print(f"install the chrome driver(ver: {chrome_ver})")
        chromedriver_autoinstaller.install(True)

        # 구글 공식 배포 zip 파일도 받아서 업데이트(추가 안전장치)
        URL = 'https://googlechromelabs.github.io/chrome-for-testing/'
        response = requests.get(URL)
        soup = BeautifulSoup(response.content, 'html.parser')
        stable_element = soup.find(id='stable')
        if stable_element:
            table = stable_element.find('table')
            if table:
                from io import StringIO
                import pandas as pd
                df = pd.read_html(StringIO(str(table)))[0]
                download_url = df[(df["Platform"] == "win64") & (df["Binary"] == "chromedriver")]["URL"].values[0]
                response = requests.get(download_url)
                response.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    z.extractall(chrome_folder_path)
            else:
                print("테이블을 찾을 수 없습니다.")
        else:
            print("id='stable'을 찾을 수 없습니다.")

    return driver_path

def create_log_file(log_file_path):
    with open(log_file_path, "w", encoding="utf-8") as file:
        pass

class Signature:
    @staticmethod
    def generate(timestamp, method, uri, secret_key):
        message = "{}.{}.{}".format(timestamp, method, uri)
        hash_value = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)
        return base64.b64encode(hash_value.digest())

def parse_config(file_path):
    config = {}
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key] = value
    return config

def extract_category_id(url: str) -> str:
    """
    주어진 URL에서 categoryId 값을 추출하여 반환합니다.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('categoryId', [None])[0]

def get_header():
    """
    키워드도구 API 호출 시 필요한 헤더 생성
    """
    config = parse_config("settings.txt")
    api_key = config.get("NAVER_API_KEY", "")
    secret_key = config.get("NAVER_SECRET_KEY", "")
    customer_id = config.get("CUSTOMER_ID", "")

    timestamp = str(round(time.time() * 1000))
    signature = Signature.generate(timestamp, "GET", "/keywordstool", secret_key)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": str(customer_id),
        "X-Signature": signature,
    }

def sanitize_filename(text, max_length=50):
    """
    텍스트를 파일명으로 사용할 수 있도록 전처리
    
    Args:
        text (str): 원본 텍스트
        max_length (int): 최대 파일명 길이 (확장자 제외)
    
    Returns:
        str: 전처리된 파일명
    """
    # 1. 특수문자 및 공백을 언더스코어로 변경
    import re
    # 한글, 영문, 숫자만 허용하고 나머지는 언더스코어로 변경
    filename = re.sub(r'[^\w\s가-힣]', '_', text)
    
    # 2. 연속된 언더스코어를 하나로 변경
    filename = re.sub(r'_{2,}', '_', filename)
    
    # 3. 앞뒤 언더스코어 제거
    filename = filename.strip('_')
    
    # 4. 공백을 언더스코어로 변경
    filename = filename.replace(' ', '_')
    
    # 5. 길이 제한
    if len(filename) > max_length:
        # 마지막 언더스코어 위치 확인
        last_underscore = filename[:max_length].rfind('_')
        if last_underscore > 0:
            # 단어 단위로 자르기
            filename = filename[:last_underscore]
        else:
            # 언더스코어가 없으면 그냥 자르기
            filename = filename[:max_length]
    
    # 6. 파일명이 비어있으면 기본값 사용
    if not filename:
        filename = "image"
    
    return filename

def create_image_from_text(text, font_path="NanumSquare.ttf"):
    """
    주어진 텍스트를 이미지로 생성해서 저장
    """
    config = parse_config("settings.txt")
    img_width = int(config.get('IMG_WIDTH', 512))
    img_height = int(config.get('IMG_HEIGHT', 512))
    background_color = tuple(map(int, config.get('BACKGROUND_COLOR', '255,255,255').split(',')))
    line_spacing = float(config.get('LINE_SPACING', '1.5'))  # 줄 간격 설정 추가
    # 텍스트 색상은 자동 대비로 정해보겠습니다.
    # 필요시 TEXT_COLOR 키를 직접 넣어도 됩니다.

    background_images_dir = "background_images"
    if os.path.exists(background_images_dir):
        all_files = os.listdir(background_images_dir)
    else:
        all_files = []

    if all_files:
        background_image_path = os.path.join(background_images_dir, random.choice(all_files))
    else:
        background_image_path = None

    padding = 40
    img_width_with_padding = img_width + 2 * padding
    img_height_with_padding = img_height + 2 * padding

    if background_image_path and os.path.exists(background_image_path):
        img = Image.open(background_image_path).resize((img_width_with_padding, img_height_with_padding))
        bg_avg_color = get_average_color(img)
    else:
        img = Image.new("RGB", (img_width_with_padding, img_height_with_padding), color=background_color)
        bg_avg_color = background_color

    enhancer = ImageEnhance.Brightness(img)
    brightness_factor = random.uniform(0.4, 0.8)
    img = enhancer.enhance(brightness_factor)
    text_color = get_contrast_color(bg_avg_color, brightness_factor * 3)

    blur_radius = random.uniform(4, 8)
    img = img.filter(ImageFilter.GaussianBlur(blur_radius))

    d = ImageDraw.Draw(img)
    font_size = 60
    font = ImageFont.truetype(font_path, font_size)
    
    lines = split_text_into_lines(text, font, img_width - 40)
    
    # 텍스트 높이 계산을 위해 getbbox 사용
    bbox = font.getbbox(lines[0])
    line_height = (bbox[3] - bbox[1]) * line_spacing  # 설정에서 가져온 줄 간격 적용
    
    # 전체 텍스트가 이미지에 맞도록 폰트 크기 조정
    while font_size > 10 and (len(lines) * line_height > img_height or font.getlength(max(lines, key=len)) > img_width):
        font_size -= 2
        font = ImageFont.truetype(font_path, font_size)
        lines = split_text_into_lines(text, font, img_width - 40)
        bbox = font.getbbox(lines[0])
        line_height = (bbox[3] - bbox[1]) * line_spacing  # 설정에서 가져온 줄 간격 적용

    total_text_height = len(lines) * line_height
    y_text = (img_height_with_padding - total_text_height) / 2

    for line in lines:
        bbox = font.getbbox(line)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        d.text(((img_width_with_padding - width) / 2, y_text), line, font=font, fill=text_color)
        y_text += line_height  # 설정에서 가져온 줄 간격 적용

    if not os.path.exists('images'):
        os.makedirs('images')

    # 파일명 생성
    filename = sanitize_filename(text)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = f"images/{filename}_{timestamp}.jpg"
    
    img.save(img_path)
    return img_path

def get_average_color(image):
    npixels = image.width * image.height
    cols = image.getcolors(npixels)
    sumRGB = [(x[0] * x[1][0], x[0] * x[1][1], x[0] * x[1][2]) for x in cols]
    avg = tuple([int(sum(x) / npixels) for x in zip(*sumRGB)])
    return avg

def get_contrast_color(background_color, brightness_factor=1.0):
    luminance = (
        0.299 * background_color[0]
        + 0.587 * background_color[1]
        + 0.114 * background_color[2]
    )
    adjusted_threshold = 128 * brightness_factor
    if luminance > adjusted_threshold:
        return (0, 0, 0)
    else:
        return (255, 255, 255)

def split_text_into_lines(text, font, max_width):
    lines = []
    words = text.split()
    for word in words:
        # getsize 대신 getbbox 사용
        word_width = font.getlength(word)
        if word_width <= max_width:
            if lines and font.getlength(lines[-1] + " " + word) <= max_width:
                lines[-1] += " " + word
            else:
                lines.append(word)
        else:
            temp_word = word
            while temp_word:
                cur_line = temp_word
                while font.getlength(cur_line) > max_width:
                    cur_line = cur_line[:-1]
                lines.append(cur_line)
                temp_word = temp_word[len(cur_line):]
    return lines

###################################
# 아래부터 '문서수' 관련 API 로직 #
###################################

class DocumentCountWorker(QObject):
    finished = Signal()
    progress = Signal(str)
    result = Signal(object)
    error = Signal(str)

    def __init__(self, df_keyword, filename=None, is_info=False):
        super().__init__()
        self.df_keyword = df_keyword
        self.filename = filename
        self.is_info = is_info  # 정보성 키워드 여부
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        try:
            start_time = time.time()
            df_keyword = self.df_keyword.copy()
            df_high_competition = df_keyword[df_keyword['경쟁정도'] == '높음'].copy()
            df_others = df_keyword[df_keyword['경쟁정도'] != '높음'].copy()

            keywords = df_others.index.tolist()
            df_to_process = df_others.copy()
            
            document_counts = []
            total_keywords = len(keywords)
            last_progress_time = time.time()
            
            self.progress.emit(f"총 {total_keywords}개 키워드 문서수 수집 시작...")
            
            for i, keyword in enumerate(keywords):
                if not self.is_running:
                    return
                    
                try:
                    count = 문서수구하기(keyword)
                    document_counts.append(count)
                    time.sleep(0.11)
                    
                    current_count = i + 1
                    current_time = time.time()
                    
                    # 진행률 표시 조건:
                    # 1. 100개 단위로 표시
                    # 2. 마지막 진행률 표시 후 30초가 지났을 때
                    # 3. 마지막 키워드 처리 완료 시
                    if (current_count % 100 == 0 or 
                        current_time - last_progress_time >= 30 or 
                        current_count == total_keywords):
                        
                        elapsed_time = time.time() - start_time
                        eta = calculate_eta(current_count, total_keywords, elapsed_time)
                        progress = round(current_count * 100 / total_keywords, 1)
                        
                        self.progress.emit(
                            f"문서수 처리 진행률: {progress}% ({current_count}/{total_keywords}) "
                            f"- 예상 종료 시각: {eta}"
                        )
                        last_progress_time = current_time
                    
                except Exception as e:
                    self.progress.emit(f"키워드 '{keyword}' 처리 중 에러: {e}")
                    document_counts.append(0)
                    time.sleep(1)
                    continue

            self.progress.emit("문서수 데이터 전처리 시작...")
            
            # 문서수 컬럼 추가
            df_to_process['문서수'] = document_counts
            df_to_process['문서수'] = df_to_process['문서수'].fillna(0).astype(int)

            # 데이터 타입 변환
            df_to_process['월간검색수_PC'] = df_to_process['월간검색수_PC'].astype(int)
            df_to_process['월간검색수_모바일'] = df_to_process['월간검색수_모바일'].astype(int)

            # 비율 계산
            total_searches = df_to_process['월간검색수_PC'] + df_to_process['월간검색수_모바일']
            df_to_process['비율'] = df_to_process['문서수'] / (total_searches + 1e-9)

            # 경쟁정도 '높음' 처리
            df_high_competition['문서수'] = 0
            df_high_competition['비율'] = 0

            # 결과 합치기
            df_combined = pd.concat([df_to_process, df_high_competition])
            df_combined = df_combined.sort_index()
            
            self.progress.emit("데이터 저장 중...")
            
            today = datetime.now().strftime("%Y%m%d")
            
            # 문서비율 결과 저장 (info 또는 product 디렉토리에)
            if self.is_info:
                save_dir = ensure_directory(KEYWORD_DIRS['info'])
                excel_filename = os.path.join(save_dir, f"정보성키워드_문서비율_{today}.xlsx")
            else:
                save_dir = ensure_directory(KEYWORD_DIRS['product'])
                # 파일명에서 경로와 날짜 부분 제거
                base_filename = os.path.basename(self.filename)
                base_filename = os.path.splitext(base_filename)[0]
                base_filename = re.sub(r'_\d{8}$', '', base_filename)
                excel_filename = os.path.join(save_dir, f"{base_filename}_문서비율_{today}.xlsx")
            
            df_combined.to_excel(excel_filename)
            self.progress.emit(f"데이터 저장 완료: {excel_filename}")
            self.progress.emit(f"문서수 수집 완료. 총 {len(df_combined)}개 키워드 처리됨")
            self.result.emit(df_combined)
            
        except Exception as e:
            self.error.emit(f"문서수 처리 중 에러 발생: {str(e)}")
        finally:
            self.finished.emit()

def calculate_eta(current_count, total_count, elapsed_time):
    """예상 종료 시간 계산"""
    if current_count == 0:
        return "계산 중..."
    items_per_second = current_count / elapsed_time
    remaining_items = total_count - current_count
    remaining_seconds = remaining_items / items_per_second
    eta = datetime.now() + pd.Timedelta(seconds=remaining_seconds)
    return eta.strftime('%H:%M:%S')

def 문서수구하기(keyword):
    """
    네이버 '블로그 검색 API'를 통해 검색 결과의 total 값을 반환
    """
    config = parse_config("settings.txt")
    client_id = config.get("CLIENT_ID", "")
    client_secret = config.get("CLIENT_SECRET", "")

    if not client_id or not client_secret:
        log("CLIENT_ID 또는 CLIENT_SECRET이 설정되어 있지 않습니다.")
        return 0

    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/blog?query={encText}"

    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            data = json.loads(response_body.decode('utf-8'))
            return data.get("total", 0)
        else:
            log(f"Error Code: {rescode}")
            return 0
    except Exception as e:
        log(f"문서수 API 호출 중 에러: {e}")
        return 0

def ensure_directory(directory):
    """지정된 디렉토리가 없으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        log(f"디렉토리 생성: {directory}")
    return directory

# 상수로 디렉토리 경로 정의
KEYWORD_DIRS = {
    'info': 'keywords/info',  # 정보성 키워드
    'product': 'keywords/product',  # 상품 키워드
    'related': 'keywords/related',  # 연관 키워드
}
