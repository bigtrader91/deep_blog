"""
네이버 키워드 수집기

이 모듈은 네이버 검색광고 API와 셀레니움을 통해 다양한 키워드를 수집하는 기능을 제공합니다.
정보성 키워드, 상품 키워드, 트렌드 키워드 등 다양한 유형의 키워드를 수집할 수 있습니다.
"""
import os
import re
import json
import time
import asyncio
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import urllib.parse

from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from src.common.logging import get_logger
from src.common.utils.selenium_utils import (
    setup_chrome_driver, 
    random_delay, 
    safe_driver_get,
    extract_text_from_element,
    close_driver
)
from src.core.search.utils.naver_api_utils import (
    get_relkeyword,
    collect_related_keywords,
    get_naver_searchad_header
)

# 로거 설정
logger = get_logger(__name__)

class NaverKeywordCollector:
    """네이버 키워드 수집기 클래스
    
    네이버 검색광고 API와 셀레니움을 통해 다양한 키워드를 수집합니다.
    """
    
    def __init__(self, api_key: Optional[str] = None, 
                 secret_key: Optional[str] = None, 
                 customer_id: Optional[str] = None,
                 headless: bool = True) -> None:
        """
        NaverKeywordCollector 초기화
        
        Args:
            api_key: 네이버 검색광고 API 키. 기본값은 None으로, 환경 변수에서 로드.
            secret_key: 네이버 검색광고 시크릿 키. 기본값은 None으로, 환경 변수에서 로드.
            customer_id: 네이버 검색광고 고객 ID. 기본값은 None으로, 환경 변수에서 로드.
            headless: 헤드리스 모드 사용 여부. 기본값은 True.
        """
        # API 키 초기화
        self.api_key = api_key or os.getenv("NAVER_API_KEY", "")
        self.secret_key = secret_key or os.getenv("NAVER_SECRET_KEY", "")
        self.customer_id = customer_id or os.getenv("NAVER_CUSTOMER_ID", "")
        
        # API 키 환경 변수 설정
        if self.api_key:
            os.environ["NAVER_API_KEY"] = self.api_key
        if self.secret_key:
            os.environ["NAVER_SECRET_KEY"] = self.secret_key
        if self.customer_id:
            os.environ["NAVER_CUSTOMER_ID"] = self.customer_id
        
        # 헤드리스 모드 설정
        self.headless = headless
        
        # 드라이버 초기화는 필요할 때만 수행
        self._driver = None
    
    @property
    def driver(self):
        """셀레니움 드라이버를 반환합니다. 없으면 생성합니다."""
        if self._driver is None:
            self._driver = setup_chrome_driver(
                headless=self.headless,
                disable_images=True
            )
        return self._driver
    
    def close(self) -> None:
        """드라이버를 종료합니다."""
        if self._driver is not None:
            close_driver(self._driver)
            self._driver = None
    
    def __del__(self) -> None:
        """객체 소멸 시 드라이버를 종료합니다."""
        self.close()
    
    def collect_info_keywords_from_category(self, url: str, pages: int = 1) -> pd.DataFrame:
        """
        특정 URL(카테고리 페이지)에서 정보성 키워드를 수집합니다.
        
        Args:
            url: 수집할 카테고리 URL
            pages: 수집할 페이지 수. 기본값은 1.
            
        Returns:
            pd.DataFrame: 수집된 키워드 DataFrame
        """
        logger.info(f"정보성 키워드 수집 시작: {url}, {pages}페이지")
        keywords = []
        
        try:
            # URL이 유효한지 확인
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"유효하지 않은 URL: {url}")
            
            # 셀레니움으로 페이지 접근
            if not safe_driver_get(self.driver, url):
                logger.error(f"URL 접근 실패: {url}")
                return pd.DataFrame()
            
            # 대괄호 제거 및 전처리 함수
            def clean_keyword(text: str) -> str:
                # 대괄호와 그 내용 제거
                cleaned = re.sub(r'\s*\[.*?\]\s*', '', text)
                # 불필요한 공백 제거
                cleaned = cleaned.strip()
                # "새글", "담기" 텍스트 제거
                cleaned = cleaned.replace("새글", "").replace("담기", "")
                return cleaned
            
            # 페이지별 수집
            for p in range(1, pages + 1):
                try:
                    if p > 1:
                        page_url = f"{url}&page={p}"
                        if not safe_driver_get(self.driver, page_url):
                            logger.warning(f"페이지 접근 실패: {page_url}")
                            continue
                    
                    # 페이지가 존재하는지 확인
                    if "검색된 문서가 없습니다" in self.driver.page_source:
                        logger.info(f"페이지 {p}에 데이터가 없습니다.")
                        continue
                    
                    # 리스트 컨테이너 찾기
                    try:
                        list_wrap = self.driver.find_element(By.CSS_SELECTOR, "#content > div.list_wrap")
                    except Exception:
                        logger.warning(f"페이지 {p}에서 리스트를 찾을 수 없습니다.")
                        continue
                    
                    # 모든 항목 찾기
                    items = list_wrap.find_elements(By.CSS_SELECTOR, "ul > li > div.info_area > div.subject > strong > a:nth-child(1)")
                    if not items:
                        logger.warning(f"페이지 {p}에서 항목을 찾을 수 없습니다.")
                        continue
                    
                    # 키워드 추출 및 정제
                    for item in items:
                        try:
                            title = item.text.strip()
                            if title:
                                # 키워드 수집 시점에서 바로 전처리 적용
                                cleaned_title = clean_keyword(title)
                                if cleaned_title:  # 전처리 후 빈 문자열이 아닌 경우만 추가
                                    keywords.append(cleaned_title)
                                    logger.debug(f"키워드 추가: {cleaned_title}")
                        except Exception as e:
                            logger.warning(f"항목 처리 중 오류: {str(e)}")
                            continue
                    
                    logger.info(f"페이지 {p} 처리 완료 - {len(items)}개 항목 발견")
                    random_delay(1.0, 2.0)
                    
                except Exception as e:
                    logger.error(f"페이지 {p} 처리 중 오류 발생: {str(e)}")
                    continue
            
            # 중복 제거 및 빈 문자열 제거
            keywords = list(set([keyword for keyword in keywords if keyword]))
            
            if not keywords:
                logger.warning(f"수집된 키워드가 없습니다. URL: {url}")
                return pd.DataFrame()
            
            # 각 키워드별로 연관 키워드 수집
            logger.info(f"총 {len(keywords)}개 키워드의 연관 키워드 수집 시작")
            
            dfs = []
            for idx, keyword in enumerate(keywords):
                try:
                    # 연관 키워드 수집
                    df_keyword = self._collect_related_keywords_as_df(keyword)
                    if df_keyword is not None and not df_keyword.empty:
                        dfs.append(df_keyword)
                        logger.info(f"[{idx+1}/{len(keywords)}] 키워드 '{keyword}' 처리 완료")
                    else:
                        logger.warning(f"[{idx+1}/{len(keywords)}] 키워드 '{keyword}'의 연관 키워드 없음")
                    
                    # API 호출 제한 방지를 위한 딜레이
                    if idx < len(keywords) - 1:
                        random_delay(1.5, 3.0)
                        
                except Exception as e:
                    logger.error(f"키워드 '{keyword}' 수집 실패: {str(e)}")
                    random_delay(3.0, 5.0)  # 오류 발생 시 더 긴 딜레이
                    continue
            
            if not dfs:
                logger.warning("연관 키워드 데이터 없음")
                return pd.DataFrame()
            
            # 모든 키워드 데이터 병합
            df_keywords = pd.concat(dfs, axis=0)
            
            # 중복 제거
            df_keywords = df_keywords.drop_duplicates()
            
            # "< 10" 값을 "10"으로 변환
            df_keywords = df_keywords.replace("< 10", "10")
            
            # 숫자 컬럼 변환
            for col in ["월간검색수_PC", "월간검색수_모바일"]:
                if col in df_keywords.columns:
                    df_keywords[col] = pd.to_numeric(df_keywords[col], errors='coerce').fillna(0).astype(int)
            
            # NaN 값 제거
            df_keywords = df_keywords.dropna()
            
            # 인덱스 설정
            if '연관키워드' in df_keywords.columns:
                df_keywords = df_keywords.set_index("연관키워드")
            
            # 결과 저장
            logger.info(f"정보성 키워드 수집 완료: 총 {len(df_keywords)}개 키워드")
            
            return df_keywords
            
        except Exception as e:
            logger.error(f"정보성 키워드 수집 중 오류 발생: {str(e)}")
            return pd.DataFrame()
    
    def _collect_related_keywords_as_df(self, keyword: str) -> pd.DataFrame:
        """
        네이버 키워드도구 API를 이용하여 연관키워드를 DataFrame으로 반환합니다.
        
        Args:
            keyword: 검색할 키워드
            
        Returns:
            pd.DataFrame: 연관 키워드 DataFrame
        """
        try:
            # 키워드 전처리
            keyword = re.sub(r'\s*\[.*?\]\s*', '', keyword).strip()
            if not keyword:
                return pd.DataFrame()
            
            # API 응답 가져오기
            result = get_relkeyword(keyword)
            
            if "error" in result:
                logger.error(f"연관 키워드 조회 실패: {result.get('error')}")
                return pd.DataFrame()
            
            if "keywordList" not in result:
                logger.warning(f"키워드 '{keyword}'에 대한 연관 키워드가 없습니다.")
                return pd.DataFrame()
            
            # DataFrame으로 변환
            df = pd.DataFrame(result["keywordList"])
            if df.empty:
                return df
            
            # 컬럼명 변경
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
            
            # 필요한 컬럼만 선택
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
            logger.error(f"키워드 '{keyword}' 연관키워드 수집 중 오류: {str(e)}")
            return pd.DataFrame()
    
    def collect_datalab_keywords(self, pages: int = 25) -> Tuple[List[str], str]:
        """
        네이버 데이터랩 쇼핑인사이트에서 인기 키워드를 수집합니다.
        
        Args:
            pages: 수집할 페이지 수. 기본값은 25.
            
        Returns:
            Tuple[List[str], str]: (수집된 키워드 목록, 카테고리명)
        """
        keywords = []
        filename = ""
        
        try:
            # 데이터랩 페이지 접근
            url = "https://datalab.naver.com/shoppingInsight/sCategory.naver"
            if not safe_driver_get(self.driver, url):
                logger.error(f"데이터랩 접근 실패: {url}")
                return [], ""
            
            # 페이지 로딩을 위한 대기
            # 데이터랩은 로딩이 느릴 수 있으므로 충분한 시간 대기
            logger.info("데이터랩 페이지 로딩 중...")
            time.sleep(5)
            
            # 카테고리 정보 가져오기
            try:
                category = self.driver.find_element(By.CLASS_NAME, "set_period.category")
                filename = category.text.replace("/", "_").replace("\n", "_")
                logger.info(f"카테고리: {filename}")
            except Exception as e:
                logger.error(f"카테고리 정보 가져오기 실패: {str(e)}")
                filename = f"datalab_keywords_{datetime.now().strftime('%Y%m%d')}"
            
            # 조회 버튼 클릭
            try:
                search_button = self.driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[1]/div/a/span")
                search_button.click()
                time.sleep(2)  # 결과 로딩 대기
            except Exception as e:
                logger.error(f"조회 버튼 클릭 실패: {str(e)}")
                return [], filename
            
            # 페이지별 수집
            for page in range(pages):
                try:
                    # 키워드 목록 가져오기
                    lists = self.driver.find_elements(
                        By.CSS_SELECTOR, 
                        "div.rank_top1000_scroll > ul > li > a"
                    )
                    
                    # 키워드 추출 및 정제
                    for k in lists:
                        try:
                            txt = re.sub("[^ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9 ]", "", k.text)
                            if txt.strip():  # 빈 문자열이 아닌 경우만 추가
                                keywords.append(txt.strip())
                                logger.debug(f"키워드 추가: {txt.strip()}")
                        except Exception as e:
                            logger.warning(f"키워드 추출 중 오류: {str(e)}")
                            continue
                    
                    logger.info(f"페이지 {page+1} 처리 완료: {len(lists)}개 키워드 추가")
                    
                    # 다음 페이지로 이동
                    try:
                        next_button = self.driver.find_element(
                            By.CSS_SELECTOR, 
                            "#content > div.section_instie_area.space_top > div > div:nth-child(2) > div.section_insite_sub > div > div > div.top1000_btn_area > div > a.btn_page_next"
                        )
                        if not next_button.is_enabled():  # 다음 버튼이 비활성화되어 있으면 종료
                            logger.info("마지막 페이지 도달")
                            break
                        next_button.click()
                        time.sleep(1)  # 페이지 로딩 대기
                    except Exception as e:
                        logger.warning(f"다음 페이지 이동 중 오류: {str(e)}")
                        break
                
                except Exception as e:
                    logger.error(f"페이지 {page+1} 처리 중 오류 발생: {str(e)}")
                    break
            
            # 중복 제거
            keywords = list(dict.fromkeys(keywords))
            logger.info(f"데이터랩 키워드 수집 완료: 총 {len(keywords)}개")
            
            return keywords, filename
        
        except Exception as e:
            logger.error(f"데이터랩 키워드 수집 중 오류 발생: {str(e)}")
            return [], filename
    
    def collect_product_keywords(self, pages: int = 25) -> Tuple[pd.DataFrame, str]:
        """
        데이터랩에서 상품 키워드를 수집하고, 각 키워드의 연관 키워드를 가져옵니다.
        
        Args:
            pages: 데이터랩에서 수집할 페이지 수. 기본값은 25.
            
        Returns:
            Tuple[pd.DataFrame, str]: (연관 키워드 DataFrame, 파일명)
        """
        try:
            # 데이터랩에서 키워드 수집
            logger.info("데이터랩 키워드 수집 시작...")
            keywords, filename = self.collect_datalab_keywords(pages)
            
            if not keywords:
                logger.warning("데이터랩에서 수집된 키워드가 없습니다.")
                return pd.DataFrame(), ""
            
            # 연관 키워드 수집
            logger.info(f"총 {len(keywords)}개 키워드의 연관 키워드 수집 시작")
            
            dfs = []
            for idx, keyword in enumerate(keywords):
                try:
                    # 연관 키워드 수집
                    df_keyword = self._collect_related_keywords_as_df(keyword)
                    if df_keyword is not None and not df_keyword.empty:
                        dfs.append(df_keyword)
                        logger.info(f"[{idx+1}/{len(keywords)}] 키워드 '{keyword}' 처리 완료")
                    else:
                        logger.warning(f"[{idx+1}/{len(keywords)}] 키워드 '{keyword}'의 연관 키워드 없음")
                    
                    # API 호출 제한 방지를 위한 딜레이
                    if idx < len(keywords) - 1:
                        random_delay(1.5, 3.0)
                        
                except Exception as e:
                    logger.error(f"키워드 '{keyword}' 수집 실패: {str(e)}")
                    random_delay(3.0, 5.0)  # 오류 발생 시 더 긴 딜레이
                    continue
            
            if not dfs:
                logger.warning("연관 키워드 데이터 없음")
                return pd.DataFrame(), filename
            
            # 모든 키워드 데이터 병합
            df_combined = pd.concat(dfs, axis=0)
            
            # 중복 제거
            df_combined = df_combined.drop_duplicates()
            
            # "< 10" 값을 "10"으로 변환
            df_combined = df_combined.replace("< 10", "10")
            
            # 숫자 컬럼 변환
            for col in ["월간검색수_PC", "월간검색수_모바일"]:
                if col in df_combined.columns:
                    df_combined[col] = pd.to_numeric(df_combined[col], errors='coerce').fillna(0).astype(int)
            
            # 인덱스 설정
            if '연관키워드' in df_combined.columns:
                df_combined = df_combined.set_index("연관키워드")
            
            # 결과 저장
            logger.info(f"상품 키워드 수집 완료: 총 {len(df_combined)}개 키워드")
            
            return df_combined, filename
            
        except Exception as e:
            logger.error(f"상품 키워드 수집 중 오류 발생: {str(e)}")
            return pd.DataFrame(), ""
    
    def extract_category_id(self, url: str) -> str:
        """
        URL에서 카테고리 ID를 추출합니다.
        
        Args:
            url: 카테고리 페이지 URL
            
        Returns:
            str: 추출된 카테고리 ID
        """
        try:
            # URL 파싱
            parsed_url = urllib.parse.urlparse(url)
            
            # 쿼리 파라미터 파싱
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # 카테고리 ID 추출
            if 'categoryId' in query_params:
                return query_params['categoryId'][0]
            
            # 다른 형태의 카테고리 ID 추출 시도
            if 'dirId' in query_params:
                return query_params['dirId'][0]
            
            return datetime.now().strftime("%Y%m%d")
        
        except Exception:
            return datetime.now().strftime("%Y%m%d")
    
    def save_to_excel(self, df: pd.DataFrame, prefix: str = "", category_id: str = "") -> str:
        """
        DataFrame을 엑셀 파일로 저장합니다.
        
        Args:
            df: 저장할 DataFrame
            prefix: 파일명 접두사
            category_id: 카테고리 ID
            
        Returns:
            str: 저장된 파일 경로
        """
        if df.empty:
            logger.warning("저장할 데이터가 없습니다.")
            return ""
        
        try:
            # 파일명 생성
            today = datetime.now().strftime("%Y%m%d")
            
            if not category_id:
                category_id = today
            
            if prefix:
                filename = f"{prefix}_{category_id}_{today}.xlsx"
            else:
                filename = f"keywords_{category_id}_{today}.xlsx"
            
            # 파일 저장
            df.to_excel(filename)
            logger.info(f"데이터 저장 완료: {filename}")
            
            return filename
        
        except Exception as e:
            logger.error(f"파일 저장 중 오류 발생: {str(e)}")
            return ""
    
    async def collect_keywords_async(self, url: str = None, pages: int = 1, keyword_type: str = "info") -> Tuple[pd.DataFrame, str]:
        """
        키워드를 비동기적으로 수집합니다.
        
        Args:
            url: 정보성 키워드 수집 시 사용할 URL
            pages: 수집할 페이지 수
            keyword_type: 키워드 유형 ('info' 또는 'product')
            
        Returns:
            Tuple[pd.DataFrame, str]: (수집된 키워드 DataFrame, 파일명)
        """
        if keyword_type == "info":
            if not url:
                logger.error("정보성 키워드 수집에는 URL이 필요합니다.")
                return pd.DataFrame(), ""
            
            category_id = self.extract_category_id(url)
            df = self.collect_info_keywords_from_category(url, pages)
            filename = self.save_to_excel(df, "정보성키워드", category_id)
            return df, filename
        
        elif keyword_type == "product":
            df, category_name = self.collect_product_keywords(pages)
            filename = self.save_to_excel(df, f"{category_name}_상품키워드")
            return df, filename
        
        else:
            logger.error(f"지원되지 않는 키워드 유형: {keyword_type}")
            return pd.DataFrame(), "" 