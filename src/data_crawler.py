"""
네이버 검색 API를 활용한 병렬 데이터 수집기

이 모듈은 네이버 검색 API를 사용하여 뉴스, 백과사전, 지식인에서 
데이터를 병렬로 수집하고 각 링크의 상세 내용까지 크롤링합니다.
또한 Google News RSS를 이용한 뉴스 수집 기능도 제공합니다.
"""
import os
import json
import asyncio
import random
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import quote

import aiohttp
import nest_asyncio
import requests
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fake_useragent import UserAgent

# 비동기 작업을 Jupyter Notebook에서 실행하기 위한 설정
nest_asyncio.apply()

# 환경 변수 로드
load_dotenv()

class GoogleNews:
    """구글 뉴스를 검색하고 결과를 반환하는 클래스
    
    이 클래스는 Google News RSS 피드를 사용하여 최신 뉴스나 키워드 기반 뉴스를 검색합니다.
    
    Attributes:
        base_url (str): 구글 뉴스 RSS 기본 URL
    """
    
    def __init__(self) -> None:
        """GoogleNews 클래스를 초기화합니다."""
        self.base_url = "https://news.google.com/rss"
    
    def _fetch_news(self, url: str, k: int = 3) -> List[Dict[str, str]]:
        """주어진 URL에서 뉴스를 가져옵니다.
        
        Args:
            url (str): 뉴스를 가져올 URL
            k (int, optional): 가져올 뉴스의 최대 개수. 기본값은 3.
            
        Returns:
            List[Dict[str, str]]: 뉴스 제목과 링크를 포함한 딕셔너리 리스트
        """
        news_data = feedparser.parse(url)
        return [
            {"title": entry.title, "link": entry.link}
            for entry in news_data.entries[:k]
        ]
    
    def _collect_news(self, news_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """뉴스 리스트를 정리하여 반환합니다.
        
        Args:
            news_list (List[Dict[str, str]]): 뉴스 정보를 포함한 딕셔너리 리스트
            
        Returns:
            List[Dict[str, str]]: URL과 내용을 포함한 딕셔너리 리스트
        """
        if not news_list:
            print("해당 키워드의 뉴스가 없습니다.")
            return []
        
        result = []
        for news in news_list:
            result.append({"url": news["link"], "content": news["title"]})
        
        return result
    
    def search_latest(self, k: int = 3) -> List[Dict[str, str]]:
        """최신 뉴스를 검색합니다.
        
        Args:
            k (int, optional): 검색할 뉴스의 최대 개수. 기본값은 3.
            
        Returns:
            List[Dict[str, str]]: URL과 내용을 포함한 딕셔너리 리스트
        """
        url = f"{self.base_url}?hl=ko&gl=KR&ceid=KR:ko"
        news_list = self._fetch_news(url, k)
        return self._collect_news(news_list)
    
    def search_by_keyword(self, keyword: Optional[str] = None, k: int = 3) -> List[Dict[str, str]]:
        """키워드로 뉴스를 검색합니다.
        
        Args:
            keyword (Optional[str], optional): 검색할 키워드. 기본값은 None.
            k (int, optional): 검색할 뉴스의 최대 개수. 기본값은 3.
            
        Returns:
            List[Dict[str, str]]: URL과 내용을 포함한 딕셔너리 리스트
        """
        if keyword:
            encoded_keyword = quote(keyword)
            url = f"{self.base_url}/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            url = f"{self.base_url}?hl=ko&gl=KR&ceid=KR:ko"
        news_list = self._fetch_news(url, k)
        return self._collect_news(news_list)
    
    async def fetch_content(self, url: str, user_agent: UserAgent) -> Tuple[str, str, Dict[str, Any]]:
        """주어진 URL에서 뉴스 내용을 가져옵니다.
        
        Args:
            url (str): 크롤링할 뉴스 URL
            user_agent (UserAgent): User-Agent 생성기
            
        Returns:
            Tuple[str, str, Dict[str, Any]]: (HTML 내용, 추출된 텍스트 내용, 추가 메타데이터)
        """
        headers = {'User-Agent': user_agent.random}
        
        # 랜덤 딜레이 추가
        await asyncio.sleep(random.uniform(0.5, 3.0))
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 불필요한 요소 제거
                    for script in soup(['script', 'style', 'iframe', 'ins']):
                        script.extract()
                    
                    # 뉴스 본문 추출 시도
                    main_content = None
                    
                    # 주요 뉴스 컨텐츠 영역 탐색
                    for selector in ['article', '.article-body', '.article_body', '.news-content', '.story-body', '.content-article']:
                        content = soup.select_one(selector)
                        if content:
                            main_content = content
                            break
                    
                    # 발행일, 작성자 추출 시도
                    pub_date = None
                    date_selectors = ['.date', '.time', '.published', '.pubdate', '.timestamp']
                    for selector in date_selectors:
                        date_elem = soup.select_one(selector)
                        if date_elem:
                            pub_date = date_elem.get_text().strip()
                            break
                    
                    # 언론사 추출
                    press = None
                    press_selectors = ['.publisher', '.source', '.author', '.byline']
                    for selector in press_selectors:
                        press_elem = soup.select_one(selector)
                        if press_elem:
                            press = press_elem.get_text().strip()
                            break
                    
                    # 텍스트 추출
                    if main_content:
                        text = main_content.get_text(separator='\n').strip()
                    else:
                        # 본문 영역을 찾지 못한 경우 일반적인 방법으로 텍스트 추출
                        text = soup.get_text(separator='\n').strip()
                    
                    # 정제
                    text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
                    text = re.sub(r'\s+', ' ', text)
                    
                    metadata = {
                        'date': pub_date,
                        'press': press
                    }
                    
                    return html, text, metadata
                else:
                    return "", f"Error: Status code {response.status}", {}
    

class NaverCrawler:
    """네이버 검색 API와 웹 크롤링을 이용한 데이터 수집기
    
    이 클래스는 네이버 검색 API를 통해 뉴스, 백과사전, 지식인의 검색 결과를 가져오고,
    각 결과의 링크에 접속하여 상세 내용을 크롤링합니다.
    또한 Google News RSS를 통해 뉴스 데이터도 수집할 수 있습니다.
    
    Attributes:
        client_id (str): 네이버 API 클라이언트 ID
        client_secret (str): 네이버 API 클라이언트 시크릿
        user_agent (UserAgent): fake-useragent 라이브러리를 사용한 User-Agent 생성기
        headers (Dict[str, str]): API 요청에 사용할 기본 헤더
        google_news (GoogleNews): Google News RSS 기반 뉴스 검색 도구
    """
    
    def __init__(self) -> None:
        """NaverCrawler 초기화"""
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경 변수가 필요합니다")
        
        # UserAgent 초기화 (fake-useragent 사용)
        self.user_agent = UserAgent()
        
        # API 요청용 기본 헤더
        self.headers = {
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.client_secret
        }
        
        # Google News 초기화
        self.google_news = GoogleNews()
    
    def _get_random_user_agent(self) -> str:
        """임의의 User-Agent를 반환합니다.
        
        Returns:
            str: 임의의 User-Agent 문자열
        """
        # fake-useragent를 사용하여 랜덤 User-Agent 생성
        # random 속성을 사용하면 매번 다른 브라우저의 User-Agent를 무작위로 제공
        return self.user_agent.random
    
    def _random_delay(self, min_delay: float = 0.5, max_delay: float = 3.0) -> None:
        """요청 사이에 랜덤한 딜레이를 추가합니다.
        
        Args:
            min_delay (float, optional): 최소 딜레이 시간(초). 기본값은 0.5초.
            max_delay (float, optional): 최대 딜레이 시간(초). 기본값은 3.0초.
        """
        time.sleep(random.uniform(min_delay, max_delay))
    
    async def _async_random_delay(self, min_delay: float = 0.5, max_delay: float = 3.0) -> None:
        """비동기 작업 사이에 랜덤한 딜레이를 추가합니다.
        
        Args:
            min_delay (float, optional): 최소 딜레이 시간(초). 기본값은 0.5초.
            max_delay (float, optional): 최대 딜레이 시간(초). 기본값은 3.0초.
        """
        await asyncio.sleep(random.uniform(min_delay, max_delay))
    
    def _clean_html_tags(self, text: str) -> str:
        """HTML 태그를 제거하고 텍스트를 정리합니다.
        
        Args:
            text (str): 정리할 텍스트
            
        Returns:
            str: HTML 태그가 제거된 정리된 텍스트
        """
        # HTML 태그 제거
        clean_text = re.sub(r'<.*?>', '', text)
        # HTML 엔티티 디코딩
        clean_text = clean_text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return clean_text
    
    async def search_news(self, query: str, display: int = 10, start: int = 1, sort: str = "sim") -> Dict[str, Any]:
        """네이버 뉴스 검색 API를 사용하여 뉴스 기사를 검색합니다.
        
        Args:
            query (str): 검색어
            display (int, optional): 검색 결과 개수. 기본값은 10.
            start (int, optional): 검색 시작 위치. 기본값은 1.
            sort (str, optional): 정렬 방식('sim': 유사도순, 'date': 날짜순). 기본값은 'sim'.
            
        Returns:
            Dict[str, Any]: 뉴스 검색 결과
        """
        url = f"https://openapi.naver.com/v1/search/news.json?query={quote(query)}&display={display}&start={start}&sort={sort}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # 결과 내의 HTML 태그 제거
                    for item in result.get('items', []):
                        if 'title' in item:
                            item['title'] = self._clean_html_tags(item['title'])
                        if 'description' in item:
                            item['description'] = self._clean_html_tags(item['description'])
                    
                    return result
                else:
                    response_text = await response.text()
                    raise Exception(f"뉴스 검색 API 호출 실패: {response.status}, {response_text}")
    
    async def search_encyc(self, query: str, display: int = 10, start: int = 1) -> Dict[str, Any]:
        """네이버 백과사전 검색 API를 사용하여 백과사전 항목을 검색합니다.
        
        Args:
            query (str): 검색어
            display (int, optional): 검색 결과 개수. 기본값은 10.
            start (int, optional): 검색 시작 위치. 기본값은 1.
            
        Returns:
            Dict[str, Any]: 백과사전 검색 결과
        """
        url = f"https://openapi.naver.com/v1/search/encyc.json?query={quote(query)}&display={display}&start={start}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # 결과 내의 HTML 태그 제거
                    for item in result.get('items', []):
                        if 'title' in item:
                            item['title'] = self._clean_html_tags(item['title'])
                        if 'description' in item:
                            item['description'] = self._clean_html_tags(item['description'])
                    
                    return result
                else:
                    response_text = await response.text()
                    raise Exception(f"백과사전 검색 API 호출 실패: {response.status}, {response_text}")
    
    async def search_kin(self, query: str, display: int = 10, start: int = 1, sort: str = "sim") -> Dict[str, Any]:
        """네이버 지식인 검색 API를 사용하여 지식인 질문을 검색합니다.
        
        Args:
            query (str): 검색어
            display (int, optional): 검색 결과 개수. 기본값은 10.
            start (int, optional): 검색 시작 위치. 기본값은 1.
            sort (str, optional): 정렬 방식('sim': 유사도순, 'date': 날짜순). 기본값은 'sim'.
            
        Returns:
            Dict[str, Any]: 지식인 검색 결과
        """
        url = f"https://openapi.naver.com/v1/search/kin.json?query={quote(query)}&display={display}&start={start}&sort={sort}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # 결과 내의 HTML 태그 제거
                    for item in result.get('items', []):
                        if 'title' in item:
                            item['title'] = self._clean_html_tags(item['title'])
                        if 'description' in item:
                            item['description'] = self._clean_html_tags(item['description'])
                    
                    return result
                else:
                    response_text = await response.text()
                    raise Exception(f"지식인 검색 API 호출 실패: {response.status}, {response_text}")
    
    async def fetch_content(self, url: str, source_type: str = None, max_content_length: int = 2000) -> Tuple[str, str, Dict[str, Any]]:
        """주어진 URL에서 웹 페이지 내용을 가져옵니다.
        
        Args:
            url (str): 크롤링할 URL
            source_type (str, optional): 소스 유형(news, encyc, kin). 기본값은 None.
            max_content_length (int, optional): 최대 콘텐츠 길이. 기본값은 2000자.
            
        Returns:
            Tuple[str, str, Dict[str, Any]]: (HTML 내용, 추출된 텍스트 내용, 추가 메타데이터)
        """
        headers = {'User-Agent': self._get_random_user_agent()}
        
        # 쿠키와 리퍼러 추가 (더 자연스러운 요청처럼 보이게)
        cookies = {}
        headers['Referer'] = 'https://search.naver.com/'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        headers['Accept-Language'] = 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3'
        
        # 랜덤 딜레이 증가 (1-5초)
        await self._async_random_delay(1.0, 5.0)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, cookies=cookies) as response:
                    if response.status == 200:
                        # 인코딩 문제 해결: 여러 인코딩 시도
                        try:
                            # 먼저 응답 헤더에서 charset 확인
                            content_type = response.headers.get('Content-Type', '')
                            charset = None
                            if 'charset=' in content_type:
                                charset = content_type.split('charset=')[-1].strip()
                            
                            # charset이 지정되어 있으면 해당 인코딩 사용
                            if charset:
                                html = await response.text(encoding=charset, errors='replace')
                            else:
                                # UTF-8 시도
                                try:
                                    html = await response.text(encoding='utf-8', errors='strict')
                                except UnicodeDecodeError:
                                    # UTF-8 실패시 EUC-KR 시도
                                    try:
                                        html = await response.text(encoding='euc-kr', errors='replace')
                                    except UnicodeDecodeError:
                                        # 마지막으로 CP949 시도
                                        html = await response.text(encoding='cp949', errors='replace')
                        except Exception as e:
                            # 어떤 인코딩도 실패하면 바이너리로 읽고 디코딩 대신 errors='replace' 사용
                            binary = await response.read()
                            html = binary.decode('utf-8', errors='replace')
                        
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 불필요한 요소 제거
                        for script in soup(['script', 'style', 'iframe', 'ins']):
                            script.extract()
                        
                        # 뉴스 본문 추출 시도
                        main_content = None
                        
                        # 주요 뉴스 컨텐츠 영역 탐색
                        for selector in ['article', '.article-body', '.article_body', '.news-content', '.story-body', '.content-article']:
                            content = soup.select_one(selector)
                            if content:
                                main_content = content
                                break
                        
                        # 발행일, 작성자 추출 시도
                        pub_date = None
                        date_selectors = ['.t11', '.report_date', '.article_date', '.date', '.time']
                        for selector in date_selectors:
                            date_elem = soup.select_one(selector)
                            if date_elem:
                                pub_date = date_elem.get_text().strip()
                                break
                        
                        # 언론사 추출
                        press = None
                        press_selectors = ['.press', '.source', '.publisher', '.article_by']
                        for selector in press_selectors:
                            press_elem = soup.select_one(selector)
                            if press_elem:
                                press = press_elem.get_text().strip()
                                break
                        
                        # 텍스트 추출
                        if main_content:
                            text = main_content.get_text(separator='\n').strip()
                        else:
                            # 본문 영역을 찾지 못한 경우 일반적인 방법으로 텍스트 추출
                            text = soup.get_text(separator='\n').strip()
                        
                        # 정제
                        text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
                        text = re.sub(r'\s+', ' ', text)
                        
                        # 텍스트 길이 제한 (토큰 제한 방지)
                        if len(text) > max_content_length:
                            text = text[:max_content_length] + "... [잘림]"
                        
                        metadata = {
                            'date': pub_date,
                            'press': press
                        }
                        
                        # HTML은 빈 문자열로 반환 (토큰 절약)
                        return "", text, metadata
                    else:
                        return "", f"Error: Status code {response.status}", {}
        except Exception as e:
            return "", f"Error: {str(e)}", {}
    
    def _extract_content_by_source(self, soup: BeautifulSoup, source_type: str) -> Dict[str, Any]:
        """소스 유형에 따라 특화된 콘텐츠 추출 로직을 적용합니다.
        
        Args:
            soup (BeautifulSoup): 파싱할 HTML 콘텐츠의 BeautifulSoup 객체
            source_type (str): 소스 유형(news, encyc, kin)
            
        Returns:
            Dict[str, Any]: 추출된 텍스트와 메타데이터
        """
        result = {'text': ''}
        
        if not source_type:
            # 일반적인 텍스트 추출
            text = soup.get_text(separator='\n').strip()
            # 여러 줄 공백 제거
            text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
            # 연속된 공백 제거
            text = re.sub(r'\s+', ' ', text)
            result['text'] = text
            return result
        
        if source_type == 'news':
            # 뉴스 특화 파싱
            # 주요 뉴스 컨텐츠 영역 탐색
            main_content = None
            
            # 네이버 뉴스 구조
            if soup.select_one('#dic_area'):
                main_content = soup.select_one('#dic_area')
            # 다른 뉴스 사이트의 일반적인 구조
            elif soup.select_one('article'):
                main_content = soup.select_one('article')
            elif soup.select_one('.news_body'):
                main_content = soup.select_one('.news_body')
            elif soup.select_one('.article_body'):
                main_content = soup.select_one('.article_body')
            elif soup.select_one('.article-body'):
                main_content = soup.select_one('.article-body')
            
            # 발행일, 작성자, 언론사 추출 시도
            pub_date = None
            date_selectors = ['.t11', '.report_date', '.article_date', '.date', '.time']
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    pub_date = date_elem.get_text().strip()
                    break
            
            result['date'] = pub_date
            
            # 언론사 추출
            press = None
            press_selectors = ['.press', '.source', '.publisher', '.article_by']
            for selector in press_selectors:
                press_elem = soup.select_one(selector)
                if press_elem:
                    press = press_elem.get_text().strip()
                    break
            
            result['press'] = press
            
            # 텍스트 추출
            if main_content:
                # 불필요한 요소 제거
                for elem in main_content.select('.reporter_area, .byline, .copyright'):
                    if elem:
                        elem.extract()
                
                text = main_content.get_text(separator='\n').strip()
                # 정제
                text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
                text = re.sub(r'\s+', ' ', text)
                result['text'] = text
            else:
                # 본문 영역을 찾지 못한 경우 일반적인 방법으로 텍스트 추출
                text = soup.get_text(separator='\n').strip()
                text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
                text = re.sub(r'\s+', ' ', text)
                result['text'] = text
        
        elif source_type == 'encyc':
            # 백과사전 특화 파싱
            # 네이버 백과사전 구조
            main_content = None
            
            if soup.select_one('.summary_area'):
                summary = soup.select_one('.summary_area').get_text().strip()
                result['summary'] = summary
            
            if soup.select_one('#content'):
                main_content = soup.select_one('#content')
            elif soup.select_one('.article'):
                main_content = soup.select_one('.article')
            
            if main_content:
                # 불필요한 요소 제거
                for elem in main_content.select('.manager_area, .button_area, .related_area'):
                    if elem:
                        elem.extract()
                
                text = main_content.get_text(separator='\n').strip()
                # 정제
                text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
                text = re.sub(r'\s+', ' ', text)
                result['text'] = text
            else:
                # 본문 영역을 찾지 못한 경우 일반적인 방법으로 텍스트 추출
                text = soup.get_text(separator='\n').strip()
                text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
                text = re.sub(r'\s+', ' ', text)
                result['text'] = text
            
            # 카테고리 추출
            categories = []
            for cat in soup.select('.location a'):
                categories.append(cat.get_text().strip())
            
            if categories:
                result['categories'] = categories
        
        elif source_type == 'kin':
            # 지식인 특화 파싱
            # 질문 영역
            question = None
            if soup.select_one('.c-heading__title'):
                question = soup.select_one('.c-heading__title').get_text().strip()
            elif soup.select_one('.title'):
                question = soup.select_one('.title').get_text().strip()
            
            result['question'] = question
            
            # 질문 내용
            question_content = None
            if soup.select_one('.c-heading__content'):
                question_content = soup.select_one('.c-heading__content').get_text().strip()
            elif soup.select_one('.c-heading__detail'):
                question_content = soup.select_one('.c-heading__detail').get_text().strip()
            
            result['question_content'] = question_content
            
            # 답변 추출
            answers = []
            for answer in soup.select('.answer-content__item'):
                answer_text = answer.get_text().strip()
                answers.append(answer_text)
            
            result['answers'] = answers
            
            # 텍스트 조합
            text_parts = []
            if question:
                text_parts.append(f"질문: {question}")
            if question_content:
                text_parts.append(f"질문 내용: {question_content}")
            if answers:
                for i, answer in enumerate(answers, 1):
                    text_parts.append(f"답변 {i}: {answer}")
            
            text = '\n\n'.join(text_parts)
            result['text'] = text
        
        return result
    
    async def process_news_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 검색 결과 아이템을 처리하고 상세 내용을 추가합니다.
        
        Args:
            item (Dict[str, Any]): 뉴스 검색 결과 아이템
            
        Returns:
            Dict[str, Any]: 상세 내용이 추가된 뉴스 아이템
        """
        url = item['link']
        html, content, metadata = await self.fetch_content(url, 'news')
        
        result = {
            'title': item['title'],
            'link': url,
            'description': item['description'],
            'pubDate': item['pubDate'],
            'content': content,
            'source': 'news',
            'crawled_at': datetime.now().isoformat()
        }
        
        # 메타데이터 추가
        for key, value in metadata.items():
            if value:  # 값이 있는 경우에만 추가
                result[key] = value
        
        return result
    
    async def process_encyc_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """백과사전 검색 결과 아이템을 처리하고 상세 내용을 추가합니다.
        
        Args:
            item (Dict[str, Any]): 백과사전 검색 결과 아이템
            
        Returns:
            Dict[str, Any]: 상세 내용이 추가된 백과사전 아이템
        """
        url = item['link']
        html, content, metadata = await self.fetch_content(url, 'encyc')
        
        result = {
            'title': item['title'],
            'link': url,
            'description': item['description'],
            'content': content,
            'source': 'encyc',
            'crawled_at': datetime.now().isoformat()
        }
        
        # 메타데이터 추가
        for key, value in metadata.items():
            if value:  # 값이 있는 경우에만 추가
                result[key] = value
        
        return result
    
    async def process_kin_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """지식인 검색 결과 아이템을 처리하고 상세 내용을 추가합니다.
        
        Args:
            item (Dict[str, Any]): 지식인 검색 결과 아이템
            
        Returns:
            Dict[str, Any]: 상세 내용이 추가된 지식인 아이템
        """
        url = item['link']
        html, content, metadata = await self.fetch_content(url, 'kin')
        
        result = {
            'title': item['title'],
            'link': url,
            'description': item['description'],
            'content': content,
            'source': 'kin',
            'crawled_at': datetime.now().isoformat()
        }
        
        # 메타데이터 추가
        for key, value in metadata.items():
            if value:  # 값이 있는 경우에만 추가
                result[key] = value
        
        return result
    
    async def search_google_news(self, query: str, display: int = 10) -> List[Dict[str, Any]]:
        """Google News RSS를 사용하여 뉴스를 검색합니다.
        
        Args:
            query (str): 검색어
            display (int, optional): 검색 결과 개수. 기본값은 10.
            
        Returns:
            List[Dict[str, Any]]: 구글 뉴스 검색 결과 리스트
        """
        # 동기 함수를 비동기 컨텍스트에서 실행
        news_items = await asyncio.to_thread(
            self.google_news.search_by_keyword, query, display
        )
        return news_items
    
    async def process_google_news_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """구글 뉴스 아이템을 처리하고 상세 내용을 추가합니다.
        
        Args:
            item (Dict[str, Any]): 구글 뉴스 아이템
            
        Returns:
            Dict[str, Any]: 상세 내용이 추가된 구글 뉴스 아이템
        """
        url = item['url']
        html, content, metadata = await self.google_news.fetch_content(url, self.user_agent)
        
        result = {
            'title': item['content'],  # 구글 뉴스에서는 'content'가 제목
            'link': url,
            'description': '',  # 구글 뉴스에서는 기본적으로 설명이 없음
            'content': content,
            'source': 'google_news',
            'crawled_at': datetime.now().isoformat()
        }
        
        # 메타데이터 추가
        for key, value in metadata.items():
            if value:  # 값이 있는 경우에만 추가
                result[key] = value
        
        return result
    
    async def crawl_all(self, query: str, display: int = 3, include_google: bool = False, max_total_results: int = 8) -> Dict[str, List[Dict[str, Any]]]:
        """뉴스, 백과사전, 지식인에서 동시에 데이터를 수집합니다.
        필요에 따라 구글 뉴스 데이터도 수집합니다.
        
        Args:
            query (str): 검색어
            display (int, optional): 각 소스별 검색 결과 개수. 기본값은 3.
            include_google (bool, optional): 구글 뉴스 데이터 포함 여부. 기본값은 False.
            max_total_results (int, optional): 최대 총 결과 개수. 기본값은 8.
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: 각 소스별 상세 검색 결과
        """
        # 병렬로 API 호출
        news_task = asyncio.create_task(self.search_news(query, display))
        encyc_task = asyncio.create_task(self.search_encyc(query, display))
        kin_task = asyncio.create_task(self.search_kin(query, display))
        
        # 구글 뉴스 추가
        if include_google:
            google_news_task = asyncio.create_task(self.search_google_news(query, display))
        
        news_results = await news_task
        encyc_results = await encyc_task
        kin_results = await kin_task
        
        if include_google:
            google_news_results = await google_news_task
        
        # 각 검색 결과에서 상세 내용 가져오기
        news_items = news_results.get('items', [])
        encyc_items = encyc_results.get('items', [])
        kin_items = kin_results.get('items', [])
        
        # 최대 총 결과 개수를 초과하지 않도록 각 소스의 결과 개수 균등 분배
        total_sources = 3 + (1 if include_google else 0)
        max_per_source = max(1, max_total_results // total_sources)
        
        news_items = news_items[:max_per_source]
        encyc_items = encyc_items[:max_per_source]
        kin_items = kin_items[:max_per_source]
        
        # 각 검색 결과에서 상세 내용 가져오기
        news_tasks = [self.process_news_content(item) for item in news_items]
        encyc_tasks = [self.process_encyc_content(item) for item in encyc_items]
        kin_tasks = [self.process_kin_content(item) for item in kin_items]
        
        if include_google:
            google_news_tasks = [self.process_google_news_content(item) for item in google_news_results[:max_per_source]]
        else:
            google_news_tasks = []
        
        # 모든 태스크 병렬 실행
        all_tasks = news_tasks + encyc_tasks + kin_tasks + google_news_tasks
        all_results = await asyncio.gather(*all_tasks)
        
        # 결과 분류
        news_content = all_results[:len(news_tasks)]
        encyc_content = all_results[len(news_tasks):len(news_tasks) + len(encyc_tasks)]
        kin_content = all_results[len(news_tasks) + len(encyc_tasks):len(news_tasks) + len(encyc_tasks) + len(kin_tasks)]
        
        results = {
            'news': news_content,
            'encyc': encyc_content,
            'kin': kin_content
        }
        
        if include_google:
            google_news_content = all_results[len(news_tasks) + len(encyc_tasks) + len(kin_tasks):]
            results['google_news'] = google_news_content
        
        return results
    
    def save_results(self, results: Dict[str, List[Dict[str, Any]]], filename: str = None) -> str:
        """수집한 결과를 JSON 파일로 저장합니다.
        
        Args:
            results (Dict[str, List[Dict[str, Any]]]): 수집한 결과
            filename (str, optional): 저장할 파일명. 기본값은 None으로, 시간 기반 파일명 생성.
            
        Returns:
            str: 저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"naver_search_results_{timestamp}.json"
        
        # HTML 내용은 용량이 크므로 기본적으로 저장하지 않음
        results_without_html = {
            source: [
                {k: v for k, v in item.items() if k != 'html'}
                for item in items
            ]
            for source, items in results.items()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_without_html, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def save_full_results(self, results: Dict[str, List[Dict[str, Any]]], filename: str = None) -> str:
        """HTML 내용을 포함한 전체 수집 결과를 JSON 파일로 저장합니다.
        
        Args:
            results (Dict[str, List[Dict[str, Any]]]): 수집한 결과
            filename (str, optional): 저장할 파일명. 기본값은 None으로, 시간 기반 파일명 생성.
            
        Returns:
            str: 저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"naver_search_full_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return filename


async def main(query: str, display: int = 5, include_google: bool = False) -> None:
    """메인 함수
    
    Args:
        query (str): 검색어
        display (int, optional): 각 소스별 검색 결과 개수. 기본값은 5.
        include_google (bool, optional): 구글 뉴스 데이터 포함 여부. 기본값은 False.
    """
    crawler = NaverCrawler()
    results = await crawler.crawl_all(query, display, include_google)
    
    # 결과 저장 (HTML 제외)
    filename = crawler.save_results(results)
    print(f"수집 완료: {filename}")
    
    # HTML을 포함한 전체 결과 저장 (선택적)
    # full_filename = crawler.save_full_results(results)
    # print(f"전체 결과 저장 완료: {full_filename}")
    
    # 수집된 데이터 요약 출력
    print(f"\n검색어: {query}")
    print(f"뉴스 기사: {len(results['news'])} 건")
    print(f"백과사전 항목: {len(results['encyc'])} 건")
    print(f"지식인 질문: {len(results['kin'])} 건")
    if include_google:
        print(f"구글 뉴스: {len(results['google_news'])} 건")


# 실행 예제
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = sys.argv[1]
        display = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        include_google = False
        if len(sys.argv) > 3 and sys.argv[3].lower() in ('y', 'yes', 'true', '1'):
            include_google = True
        asyncio.run(main(query, display, include_google))
    else:
        print("사용법: python data_crawler.py <검색어> [표시할 결과 수] [구글뉴스포함(y/n)]") 