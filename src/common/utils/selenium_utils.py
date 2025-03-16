"""
셀레니움 관련 유틸리티

이 모듈은 웹 크롤링 및 스크래핑을 위한 셀레니움 관련 유틸리티 함수들을 제공합니다.
"""
import os
import sys
import time
import random
import logging
import zipfile
import platform
import subprocess
from typing import Optional, Dict, Any, Union, List, Tuple
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from fake_useragent import UserAgent, FakeUserAgentError

from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)

def create_user_agent() -> UserAgent:
    """
    UserAgent 객체를 생성합니다.
    
    Returns:
        UserAgent: fake-useragent 라이브러리의 UserAgent 객체
    """
    try:
        return UserAgent()
    except FakeUserAgentError:
        logger.warning("랜덤 User-Agent 생성 실패, 기본값 사용")
        return UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")

def get_random_user_agent() -> str:
    """
    랜덤 User-Agent 문자열을 반환합니다.
    
    Returns:
        str: 랜덤 User-Agent 문자열
    """
    ua = create_user_agent()
    return ua.random

def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    지정된 범위 내에서 랜덤 시간만큼 대기합니다.
    
    Args:
        min_seconds: 최소 대기 시간(초)
        max_seconds: 최대 대기 시간(초)
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def find_chrome_driver() -> str:
    """
    시스템에서 크롬 드라이버를 찾거나 필요한 경우 다운로드합니다.
    
    Returns:
        str: 크롬 드라이버 경로
    """
    # 기본 ChromeDriver 경로
    driver_dir = Path.home() / ".webdrivers"
    driver_dir.mkdir(exist_ok=True)
    
    # 운영체제별 드라이버 파일명
    is_windows = platform.system() == "Windows"
    driver_name = "chromedriver.exe" if is_windows else "chromedriver"
    driver_path = driver_dir / driver_name
    
    # 드라이버가 없으면 설치
    if not driver_path.exists():
        logger.info("ChromeDriver를 설치합니다...")
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver 설치 완료: {driver_path}")
        except Exception as e:
            logger.error(f"ChromeDriver 자동 설치 실패: {str(e)}")
            logger.info("수동으로 ChromeDriver 설치를 시도합니다.")
            driver_path = install_chrome_driver_manually(driver_dir, driver_name)
    
    return str(driver_path)

def install_chrome_driver_manually(driver_dir: Path, driver_name: str) -> str:
    """
    수동으로 ChromeDriver를 다운로드하고 설치합니다.
    
    Args:
        driver_dir: 드라이버를 설치할 디렉토리
        driver_name: 드라이버 파일명
        
    Returns:
        str: 설치된 ChromeDriver 경로
    """
    try:
        # 크롬 버전 확인
        try:
            # Windows
            if platform.system() == "Windows":
                from win32com.client import Dispatch
                parser = Dispatch("Scripting.FileSystemObject")
                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                if not os.path.exists(chrome_path):
                    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                version = parser.GetFileVersion(chrome_path)
            # Mac OS
            elif platform.system() == "Darwin":
                process = subprocess.Popen(
                    ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                    stdout=subprocess.PIPE
                )
                output = process.communicate()[0].decode("utf-8")
                version = output.strip().split()[-1]
            # Linux
            else:
                process = subprocess.Popen(
                    ["google-chrome", "--version"],
                    stdout=subprocess.PIPE
                )
                output = process.communicate()[0].decode("utf-8")
                version = output.strip().split()[-1]
                
            # 버전 정보가 없으면 기본값 사용
            if not version:
                version = "108.0.5359.71"  # 기본 버전
            
            # 메이저 버전만 추출
            major_version = version.split(".")[0]
            
        except Exception as e:
            logger.warning(f"크롬 버전 확인 실패: {str(e)}, 기본 버전을 사용합니다.")
            major_version = "108"
        
        # 드라이버 다운로드 URL
        base_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        response = requests.get(base_url)
        driver_version = response.text.strip()
        
        # 운영체제별 다운로드 URL
        if platform.system() == "Windows":
            zip_name = "chromedriver_win32.zip"
        elif platform.system() == "Darwin":
            if platform.machine() == "arm64":
                zip_name = "chromedriver_mac64_m1.zip"
            else:
                zip_name = "chromedriver_mac64.zip"
        else:  # Linux
            zip_name = "chromedriver_linux64.zip"
        
        download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/{zip_name}"
        
        # 드라이버 다운로드
        logger.info(f"ChromeDriver {driver_version} 다운로드 중...")
        response = requests.get(download_url)
        zip_path = driver_dir / "chromedriver.zip"
        
        with open(zip_path, "wb") as f:
            f.write(response.content)
        
        # 압축 해제
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(driver_dir)
        
        # 실행 권한 부여 (Linux/Mac)
        driver_path = driver_dir / driver_name
        if platform.system() != "Windows":
            os.chmod(driver_path, 0o755)
        
        # 임시 파일 삭제
        if zip_path.exists():
            zip_path.unlink()
        
        logger.info(f"ChromeDriver {driver_version} 설치 완료: {driver_path}")
        return str(driver_path)
        
    except Exception as e:
        logger.error(f"ChromeDriver 수동 설치 실패: {str(e)}")
        raise RuntimeError(f"ChromeDriver 설치 실패: {str(e)}")

def create_chrome_options(headless: bool = True, disable_images: bool = False) -> Options:
    """
    Chrome 브라우저 옵션을 설정합니다.
    
    Args:
        headless: 헤드리스 모드 사용 여부
        disable_images: 이미지 로딩 비활성화 여부
    
    Returns:
        Options: 설정된 Chrome 옵션 객체
    """
    options = Options()
    
    # 사용자 에이전트 설정
    options.add_argument(f"user-agent={get_random_user_agent()}")
    
    # 헤드리스 모드 설정
    if headless:
        options.add_argument("--headless")
    
    # 기본 옵션 설정
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--blink-settings=imagesEnabled=true")
    options.add_argument("--disable-notifications")
    
    # 창 크기 설정
    options.add_argument("--window-size=1920,1080")
    
    # 이미지 로딩 비활성화 (선택적)
    if disable_images:
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
    
    return options

def setup_chrome_driver(
    headless: bool = True, 
    disable_images: bool = False,
    custom_options: Optional[Options] = None
) -> webdriver.Chrome:
    """
    Chrome WebDriver를 설정하고 초기화합니다.
    
    Args:
        headless: 헤드리스 모드 사용 여부
        disable_images: 이미지 로딩 비활성화 여부
        custom_options: 사용자 정의 Chrome 옵션
        
    Returns:
        webdriver.Chrome: 초기화된 Chrome WebDriver 객체
    """
    try:
        # 크롬 드라이버 경로 찾기
        driver_path = find_chrome_driver()
        
        # 크롬 옵션 설정
        options = custom_options if custom_options else create_chrome_options(headless, disable_images)
        
        # 서비스 객체 생성
        service = Service(executable_path=driver_path)
        
        # 드라이버 초기화
        driver = webdriver.Chrome(service=service, options=options)
        
        # 페이지 로드 타임아웃 설정
        driver.set_page_load_timeout(30)
        
        return driver
        
    except Exception as e:
        logger.error(f"Chrome 드라이버 설정 중 오류 발생: {str(e)}")
        raise RuntimeError(f"Chrome 드라이버 초기화 실패: {str(e)}")

def safe_driver_get(driver: webdriver.Chrome, url: str, retries: int = 3, timeout: int = 30) -> bool:
    """
    안전하게 URL을 로드합니다. 실패 시 재시도합니다.
    
    Args:
        driver: Chrome WebDriver 객체
        url: 로드할 URL
        retries: 최대 재시도 횟수
        timeout: 페이지 로드 타임아웃(초)
        
    Returns:
        bool: 성공 여부
    """
    for attempt in range(retries):
        try:
            logger.debug(f"URL 로드 시도 ({attempt+1}/{retries}): {url}")
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            return True
        except TimeoutException:
            logger.warning(f"URL 로드 타임아웃 ({attempt+1}/{retries}): {url}")
            if attempt == retries - 1:
                logger.error(f"URL 로드 실패 (최대 재시도 횟수 초과): {url}")
                return False
            # 페이지 로드 취소 시도
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
            random_delay(2.0, 5.0)
        except WebDriverException as e:
            logger.warning(f"드라이버 예외 발생 ({attempt+1}/{retries}): {str(e)}")
            if attempt == retries - 1:
                logger.error(f"URL 로드 실패 (드라이버 예외): {url}")
                return False
            random_delay(2.0, 5.0)
        except Exception as e:
            logger.error(f"URL 로드 중 예외 발생: {str(e)}")
            return False
    
    return False

def extract_text_from_element(driver: webdriver.Chrome, css_selector: str, wait_time: int = 10) -> str:
    """
    CSS 선택자를 사용하여 요소의 텍스트를 추출합니다.
    
    Args:
        driver: Chrome WebDriver 객체
        css_selector: 요소를 찾을 CSS 선택자
        wait_time: 요소가 나타날 때까지 대기할 최대 시간(초)
        
    Returns:
        str: 추출된 텍스트 (요소를 찾지 못하면 빈 문자열)
    """
    try:
        # 요소가 나타날 때까지 대기
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        return element.text.strip()
    except TimeoutException:
        logger.warning(f"요소를 찾지 못함 (타임아웃): {css_selector}")
        return ""
    except NoSuchElementException:
        logger.warning(f"요소를 찾지 못함: {css_selector}")
        return ""
    except Exception as e:
        logger.error(f"요소 텍스트 추출 중 오류 발생: {str(e)}")
        return ""

def save_screenshot(driver: webdriver.Chrome, filename: str = None) -> str:
    """
    현재 페이지의 스크린샷을 저장합니다.
    
    Args:
        driver: Chrome WebDriver 객체
        filename: 저장할 파일명 (기본값: screenshot_YYYYMMDD_HHMMSS.png)
        
    Returns:
        str: 저장된 스크린샷 파일 경로
    """
    try:
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        driver.save_screenshot(filename)
        logger.info(f"스크린샷 저장 완료: {filename}")
        return filename
    except Exception as e:
        logger.error(f"스크린샷 저장 중 오류 발생: {str(e)}")
        return ""

def close_driver(driver: webdriver.Chrome) -> None:
    """
    WebDriver를 안전하게 종료합니다.
    
    Args:
        driver: 종료할 Chrome WebDriver 객체
    """
    try:
        driver.quit()
        logger.debug("WebDriver 종료 완료")
    except Exception as e:
        logger.warning(f"WebDriver 종료 중 오류 발생: {str(e)}") 