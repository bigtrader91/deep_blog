# naver_keywords_collector.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from PySide6.QtCore import QObject, Signal, QThread
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import chromedriver_autoinstaller  # 추가

from datetime import datetime
import time
import pandas as pd
from bs4 import BeautifulSoup

import requests
import re
import os

from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import subprocess
from src.search_keywords.utils import (
    parse_config, 
    Signature, 
    install_and_extract_chromedriver,
    DocumentCountWorker,
    ensure_directory,
    KEYWORD_DIRS,
)
from src.search_keywords.logger import log  # log 함수만 import
from src.search_keywords.utils import extract_category_id
from src.search_keywords.utils import get_header
# 디버깅용 크롬 실행 (이미 실행 중이면 불필요합니다)
# subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chromeCookie"')

ua = UserAgent()
chrome_options = Options()
chrome_options.add_argument(f"user-agent={ua.random}")
chrome_options.add_argument("--lang=ko_KR")

config = parse_config("settings.txt")
api_key = config.get("NAVER_API_KEY", "")
secret_key = config.get("NAVER_SECRET_KEY", "")
customer_id = config.get("CUSTOMER_ID", "")

def find_chromedriver():
    """크롬 드라이버를 찾거나 설치합니다."""
    try:
        # chromedriver-autoinstaller를 사용하여 설치
        chrome_ver = chromedriver_autoinstaller.get_chrome_version()
        log(f"현재 Chrome 버전: {chrome_ver}")
        driver_path = chromedriver_autoinstaller.install()
        log(f"ChromeDriver 설치 완료: {driver_path}")
        return driver_path
    except Exception as e:
        log(f"ChromeDriver 자동 설치 실패: {e}")
        
        try:
            # WebDriver Manager를 사용한 대체 방법
            log("WebDriver Manager를 사용하여 ChromeDriver 설치 시도")
            driver_path = ChromeDriverManager().install()
            log(f"ChromeDriver 설치 완료: {driver_path}")
            return driver_path
        except Exception as e:
            log(f"WebDriver Manager 설치 실패: {e}")
            
            # 기존 설치 함수 사용
            return install_and_extract_chromedriver()

def setup_driver():
    """Chrome WebDriver를 설정하고 반환합니다."""
    try:
        # Chrome 드라이버 설정
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option("detach", True)
        
        # 드라이버 파일 경로 찾기
        driver_path = find_chromedriver()
        log(f"ChromeDriver 설치 완료: {driver_path}")
        
        # Selenium 4.x 방식으로 드라이버 초기화
        service = webdriver.ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        log("Chrome WebDriver 생성 완료")
        
        return driver
        
    except Exception as e:
        log(f"Chrome WebDriver 설정 중 치명적 오류 발생: {str(e)}")
        raise

driver = setup_driver()

try:
    driver.maximize_window()
except:
    pass

def 정보성키워드수집(url, pages=1, progress_callback=None):
    """
    특정 URL(카테고리 페이지)에서 정보성 키워드를 수집하여
    각 키워드별로 연관키워드까지 추출 후 DataFrame 반환
    """
    start_time = time.time()
    단어모음 = []
    last_update_time = start_time
    update_interval = 1.0  # 업데이트 간격 (초)
    
    # Selenium driver 사용
    try:
        driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기
        
        # 대괄호 제거 및 전처리 함수
        def clean_keyword(text):
            # 대괄호와 그 내용 제거
            cleaned = re.sub(r'\s*\[.*?\]\s*', '', text)
            # 불필요한 공백 제거
            cleaned = cleaned.strip()
            # "새글", "담기" 텍스트 제거
            cleaned = cleaned.replace("새글", "").replace("담기", "")
            return cleaned
        
        for p in range(1, pages + 1):
            try:
                if p > 1:
                    page_url = f"{url}&page={p}"
                    driver.get(page_url)
                    time.sleep(2)
                
                # 페이지가 존재하는지 확인
                if "검색된 문서가 없습니다" in driver.page_source:
                    if progress_callback:
                        progress_callback(f"페이지 {p}에 데이터가 없습니다.")
                    continue
                
                # 리스트 컨테이너 찾기
                list_wrap = driver.find_element(By.CSS_SELECTOR, "#content > div.list_wrap")
                if not list_wrap:
                    log(f"페이지 {p}에서 리스트를 찾을 수 없습니다.")
                    continue
                
                # 모든 항목 찾기
                items = list_wrap.find_elements(By.CSS_SELECTOR, "ul > li > div.info_area > div.subject > strong > a:nth-child(1)")
                if not items:
                    log(f"페이지 {p}에서 항목을 찾을 수 없습니다.")
                    continue
                
                for item in items:  # 각 페이지의 모든 항목
                    try:
                        title = item.text.strip()
                        if title:
                            # 키워드 수집 시점에서 바로 전처리 적용
                            cleaned_title = clean_keyword(title)
                            if cleaned_title:  # 전처리 후 빈 문자열이 아닌 경우만 추가
                                단어모음.append(cleaned_title)
                                current_time = time.time()
                                if current_time - last_update_time >= update_interval:
                                    if progress_callback:
                                        progress_callback(f"키워드 추가: {cleaned_title}")
                                    last_update_time = current_time
                    except Exception as e:
                        if progress_callback:
                            progress_callback(f"항목 처리 중 오류: {str(e)}")
                        continue
                
                if progress_callback:
                    progress_callback(f"페이지 {p} 처리 완료 - {len(items)}개 항목 발견")
                time.sleep(1)
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"페이지 {p} 처리 중 오류 발생: {str(e)}")
                continue

    except Exception as e:
        if progress_callback:
            progress_callback(f"브라우저 처리 중 오류 발생: {str(e)}")
        return None

    if not 단어모음:
        log(f"수집된 키워드가 없습니다. URL: {url}")
        return None

    # 이제 단어모음은 이미 전처리된 상태이므로 추가 전처리 불필요
    단어모음2 = [x for x in 단어모음 if x]  # 빈 문자열만 제거
    
    total_keywords = len(단어모음2)
    if progress_callback:
        progress_callback(f"수집된 키워드 수: {total_keywords}")
    
    dfs = []
    last_update_time = time.time()

    def calculate_eta(current_count, total_count, elapsed_time):
        """예상 종료 시간 계산"""
        if current_count == 0:
            return "계산 중..."
        items_per_second = current_count / elapsed_time
        remaining_items = total_count - current_count
        remaining_seconds = remaining_items / items_per_second
        eta = datetime.now() + pd.Timedelta(seconds=remaining_seconds)
        return eta.strftime('%H:%M:%S')

    for index, 키워드 in enumerate(단어모음2):
        키워드 = 키워드.replace(" ", "")
        try:
            df_keyword = 연관키워드수집(키워드)
            time.sleep(2)
            if df_keyword is not None and not df_keyword.empty:
                dfs.append(df_keyword)
                
                current_count = index + 1
                # 10개 단위로 진행률 표시
                if current_count % 10 == 0 or current_count == total_keywords:
                    elapsed_time = time.time() - start_time
                    eta = calculate_eta(current_count, total_keywords, elapsed_time)
                    progress = round(current_count * 100 / total_keywords, 1)
                    
                    if progress_callback:
                        progress_callback(
                            f"키워드 처리 진행률: {progress}% ({current_count}/{total_keywords}) "
                            f"- 예상 종료 시각: {eta}"
                        )

        except Exception as e:
            if progress_callback:
                progress_callback(f"키워드 '{키워드}' 수집 실패: {str(e)}")
            time.sleep(3)
            continue

    if not dfs:
        return None

    df_keyword = pd.concat(dfs, axis=0)
    df_keyword = df_keyword.drop_duplicates()
    df_keyword = df_keyword.replace("< 10", "10")
    df_keyword['월간검색수_PC'] = pd.to_numeric(df_keyword['월간검색수_PC'], errors='coerce').fillna(0).astype(int)
    df_keyword['월간검색수_모바일'] = pd.to_numeric(df_keyword['월간검색수_모바일'], errors='coerce').fillna(0).astype(int)
    df_keyword.dropna(inplace=True)
    df_keyword2 = df_keyword.set_index("연관키워드")

    if progress_callback:
        progress_callback("데이터 저장 중...")
        
    # 엑셀 파일로 저장
    today = datetime.now().strftime("%Y%m%d")
    category_id = extract_category_id(url)
    
    # 정보성 키워드 폴더 생성 및 저장
    info_dir = ensure_directory(KEYWORD_DIRS['info'])
    excel_filename = os.path.join(info_dir, f"정보성키워드_{category_id}_{today}.xlsx")
    df_keyword2.to_excel(excel_filename)
    
    if progress_callback:
        progress_callback(f"데이터 저장 완료: {excel_filename}")

    return df_keyword2

def 데이터랩수집(pages=25, progress_callback=None):
    """
    네이버 데이터랩 쇼핑인사이트 - 카테고리 추이의 인기 키워드 pages만큼 수집
    """
    try:
        keywords = []
        driver.get("https://datalab.naver.com/shoppingInsight/sCategory.naver")
        time.sleep(60)

        category = driver.find_element(By.CLASS_NAME, "set_period.category")
        filename = category.text.replace("/", "_").replace("\n", "_")
        
        if progress_callback:
            progress_callback(f"카테고리: {filename} - 데이터 수집 시작")
        
        # 조회 클릭 
        driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[1]/div/a/span").click()
        time.sleep(1)

        for page in range(pages):
            # CSS 선택자 수정
            lists = driver.find_elements(
                By.CSS_SELECTOR, 
                "div.rank_top1000_scroll > ul > li > a"
            )
            
            for k in lists:
                try:
                    txt = re.sub("[^ㄱ-ㅎㅏ-ㅣ가-힣 ]", "", k.text)
                    if txt.strip():  # 빈 문자열이 아닌 경우만 추가
                        keywords.append(txt)
                        log(f"키워드 추가: {txt}")
                except Exception as e:
                    log(f"키워드 추출 중 오류: {str(e)}")
                    continue
                
            # 다음 페이지로 이동 (CSS 선택자 수정)
            try:
                next_button = driver.find_element(
                    By.CSS_SELECTOR, 
                    "#content > div.section_instie_area.space_top > div > div:nth-child(2) > div.section_insite_sub > div > div > div.top1000_btn_area > div > a.btn_page_next"
                )
                if not next_button.is_enabled():  # 다음 버튼이 비활성화되어 있으면 종료
                    log("마지막 페이지 도달")
                    break
                next_button.click()
                time.sleep(1)  # 페이지 로딩을 위해 대기 시간 증가
            except Exception as e:
                log(f"다음 페이지 이동 중 오류: {str(e)}")
                break

        if progress_callback:
            progress_callback(f"데이터랩 수집 완료: {len(keywords)}개 키워드")
        return keywords, filename

    except Exception as e:
        if progress_callback:
            progress_callback(f"데이터랩 수집 중 오류: {str(e)}")
        return [], None

def calculate_eta(current_count, total_count, elapsed_time):
    """예상 종료 시간 계산"""
    if current_count == 0:
        return "계산 중..."
    items_per_second = current_count / elapsed_time
    remaining_items = total_count - current_count
    remaining_seconds = remaining_items / items_per_second
    eta = datetime.now() + pd.Timedelta(seconds=remaining_seconds)
    return eta.strftime('%H:%M:%S')

def 연관키워드수집(keyword):
    """
    네이버 키워드도구 API를 이용하여 연관키워드를 조회
    """
    try:
        # 대괄호와 그 내용 제거
        keyword = re.sub(r'\s*\[.*?\]\s*', '', keyword).strip()
        if not keyword:  # 키워드가 비어있으면 빈 DataFrame 반환
            return pd.DataFrame()
            
        BASE_URL = "https://api.naver.com"
        uri = "/keywordstool"
        method = "GET"
        
        
        r = requests.get(
            BASE_URL + uri + f"?hintKeywords={keyword}&showDetail=1",
            headers=get_header()
        )
        data = r.json()
        
        if "keywordList" not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data["keywordList"])
        if df.empty:
            return df

        df.rename(
            {
                "compIdx": "경쟁정도",
                "monthlyAveMobileClkCnt": "월평균클릭수_모바일",
                "monthlyAveMobileCtr": "월평균클릭률_모바일",
                "monthlyAvePcClkCnt": "월평균클릭수_PC",
                "monthlyAvePcCtr": "월평균클릭률_PC",
                "monthlyMobileQcCnt": "월간검색수_모바일",
                "monthlyPcQcCnt": "월간검색수_PC",
                "plAvgDepth": "월평균노출광고수",
                "relKeyword": "연관키워드",
            },
            axis=1,
            inplace=True,
        )
        df = df[
            [
                "연관키워드",
                "월간검색수_PC",
                "월간검색수_모바일",
                "월평균클릭수_PC",
                "월평균클릭수_모바일",
                "월평균클릭률_PC",
                "월평균클릭률_모바일",
                "경쟁정도",
                "월평균노출광고수",
            ]
        ]
        
        return df
        
    except Exception as e:
        log(f"키워드 '{keyword}' 연관키워드 수집 중 오류: {str(e)}")
        return pd.DataFrame()

def 상품키워드수집(keywords, filename, pages=1, progress_callback=None):
    """상품 키워드 수집"""
    try:
        # 모든 키워드에 대해 연관키워드 수집
        dfs = []
        total_keywords = len(keywords)
        start_time = time.time()
        
        if progress_callback:
            progress_callback(f"총 {total_keywords}개 키워드 연관키워드 수집 시작...")
        
        for index, keyword in enumerate(keywords):
            try:
                keyword = keyword.strip()  # 공백 제거
                if not keyword:  # 빈 문자열 건너뛰기
                    continue
                    
                df_keyword = 연관키워드수집(keyword)
                if df_keyword is not None and not df_keyword.empty:
                    dfs.append(df_keyword)
                
                # 10개 단위로 진행률 표시
                current_count = index + 1
                if current_count % 10 == 0 or current_count == total_keywords:
                    elapsed_time = time.time() - start_time
                    eta = calculate_eta(current_count, total_keywords, elapsed_time)
                    progress = round(current_count * 100 / total_keywords, 1)
                    
                    if progress_callback:
                        progress_callback(
                            f"연관키워드 수집 진행률: {progress}% ({current_count}/{total_keywords}) "
                            f"- 예상 종료 시각: {eta}"
                        )
                
                time.sleep(1)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"키워드 '{keyword}' 처리 중 오류: {str(e)}")
                continue

        if not dfs:
            if progress_callback:
                progress_callback("수집된 연관키워드가 없습니다.")
            return None, None

        # DataFrame 합치기 및 전처리
        df_combined = pd.concat(dfs, axis=0)
        df_combined = df_combined.drop_duplicates()
        df_combined = df_combined.replace("< 10", "10")
        
        if progress_callback:
            progress_callback("데이터 전처리 시작...")
        
        # 데이터 타입 변환
        numeric_columns = ['월간검색수_PC', '월간검색수_모바일']
        for col in numeric_columns:
            df_combined[col] = pd.to_numeric(df_combined[col], errors='coerce').fillna(0).astype(int)
        
        # 인덱스 설정 - 연관키워드를 인덱스로
        if '연관키워드' in df_combined.columns:
            df_combined = df_combined.set_index("연관키워드")
        
        if progress_callback:
            progress_callback("데이터 저장 중...")
            
        # 엑셀 파일로 저장
        today = datetime.now().strftime("%Y%m%d")
        
        # 상품 키워드 폴더 생성 및 저장
        product_dir = ensure_directory(KEYWORD_DIRS['product'])
        excel_filename = os.path.join(product_dir, f"{filename}_상품키워드_{today}.xlsx")
        df_combined.to_excel(excel_filename)
        
        if progress_callback:
            progress_callback(f"데이터 저장 완료: {excel_filename}")
        
        return df_combined, excel_filename

    except Exception as e:
        if progress_callback:
            progress_callback(f"상품 키워드 수집 중 에러: {str(e)}")
        return None, None

class KeywordCollectorWorker(QObject):
    finished = Signal()
    progress = Signal(str)
    result = Signal(object)
    error = Signal(str)

    def __init__(self, url=None, pages=1, mode='info'):
        super().__init__()
        self.url = url
        self.pages = pages
        self.mode = mode
        self.is_running = True

    def stop(self):
        self.is_running = False

    def collect_info_keywords(self):
        try:
            if not self.is_running:
                return
            
            self.progress.emit("정보성 키워드 수집 시작...")
            df = 정보성키워드수집(self.url, self.pages, progress_callback=self.progress.emit)
            
            if df is not None:
                self.result.emit(df)
                self.progress.emit("정보성 키워드 수집 완료")
            else:
                self.error.emit("키워드 수집 결과가 없습니다")
        except Exception as e:
            self.error.emit(f"에러 발생: {str(e)}")
        finally:
            self.finished.emit()

    def collect_product_keywords(self):
        try:
            if not self.is_running:
                return
            
            self.progress.emit("데이터랩 수집 시작...")
            keywords, filename = 데이터랩수집(self.pages, self.progress.emit)
            
            if not self.is_running:
                return
                
            self.progress.emit("연관 키워드 수집 시작...")
            df, excel_filename = 상품키워드수집(keywords, filename, self.pages, self.progress.emit)
            
            if df is not None:
                self.result.emit((df, excel_filename))
                self.progress.emit("상품 키워드 수집 완료")
            else:
                self.error.emit("키워드 수집 결과가 없습니다")
        except Exception as e:
            self.error.emit(f"에러 발생: {str(e)}")
        finally:
            self.finished.emit()

    def run(self):
        if self.mode == 'info':
            self.collect_info_keywords()
        else:
            self.collect_product_keywords()
