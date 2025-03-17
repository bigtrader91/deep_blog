"""
Google News RSS를 활용한 뉴스 데이터 수집 엔진

이 모듈은 Google News RSS 피드를 사용하여 최신 뉴스를 수집하고,
각 뉴스 링크의 상세 내용까지 크롤링합니다.
"""

import asyncio
import random
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

import requests
import feedparser
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Selenium 관련 임포트
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)

class GoogleNews:
    """Google News RSS를 이용한 뉴스 수집기

    이 클래스는 Google News RSS 피드를 통해 키워드 기반으로 뉴스를 검색하고,
    각 뉴스 기사의 원문 링크에 접속하여 상세 내용을 크롤링합니다.
    """
    
    def __init__(self) -> None:
        """GoogleNews 초기화"""
        # fake-useragent를 사용한 UserAgent 초기화
        self.user_agent = UserAgent()
        
        # 뉴스 사이트별 컨텐츠 셀렉터 매핑
        self.site_specific_selectors = {
            'news.naver.com': ['#newsct', '#dic_area', '#articeBody', '.end_body'],
            'n.news.naver.com': ['#newsct', '#dic_area', '#articeBody', '.end_body'],
            'www.yna.co.kr': ['.article', '.story-news', '#articleWrap'],
            'www.yonhapnews.co.kr': ['.article-view', '.article-txt'],
            'www.mk.co.kr': ['#artText', '.art_txt', '.article_body'],
            'www.hani.co.kr': ['.article-text', '.article-body', '.article_body'],
            'www.chosun.com': ['.article_body', '#news_body_id', '.news_body'],
            'news.joins.com': ['.article_body', '.article_content', '#article_body'],
            'www.donga.com': ['.article_txt', '#content', '.article'],
            'www.khan.co.kr': ['.art_body', '.article-body', '#articleBody'],
            'www.hankyung.com': ['.article-body', '.content-article', '#newsView']
        }
    
    def search_by_keyword(self, keyword: str, max_results: int = 10, include_content: bool = False) -> List[Dict[str, Any]]:
        """Google News에서 키워드로 뉴스를 검색합니다.
        
        Args:
            keyword (str): 검색 키워드
            max_results (int, optional): 최대 결과 개수. 기본값은 10.
            include_content (bool, optional): RSS 피드 내 요약 콘텐츠 포함 여부. 기본값은 False.
            
        Returns:
            List[Dict[str, Any]]: 검색된 뉴스 아이템 목록
        """
        url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            headers = {
                'User-Agent': self.user_agent.random,
                'Accept': 'application/rss+xml, application/xml, text/xml',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            items = []
            for entry in feed.entries[:max_results]:
                item = {
                    'title': entry.title,
                    'url': entry.link,
                    'published': entry.published,
                    'source': entry.source.title if hasattr(entry, 'source') else None,
                }
                if include_content and hasattr(entry, 'summary'):
                    item['content'] = entry.summary
                items.append(item)
            
            return items
        
        except Exception as e:
            logger.error(f"Google News 검색 중 오류 발생: {str(e)}")
            return []
    
    def _get_random_user_agent(self) -> str:
        """임의의 User-Agent를 반환합니다.
        
        Returns:
            str: 임의의 User-Agent 문자열
        """
        return self.user_agent.random
    
    def _random_delay(self, min_delay: float = 0.5, max_delay: float = 3.0) -> None:
        """요청 사이에 랜덤한 딜레이를 추가합니다.
        
        Args:
            min_delay (float, optional): 최소 딜레이 시간(초). 기본값은 0.5초.
            max_delay (float, optional): 최대 딜레이 시간(초). 기본값은 3.0초.
        """
        time.sleep(random.uniform(min_delay, max_delay))
    
    def _get_site_specific_selectors(self, url: str) -> List[str]:
        """사이트별 맞춤 셀렉터를 반환합니다.
        
        Args:
            url (str): 뉴스 URL
            
        Returns:
            List[str]: 사이트에 맞는 CSS 셀렉터 목록
        """
        domain_match = re.search(r'https?://([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            parts = domain.split('.')
            if len(parts) > 2:
                main_domain = '.'.join(parts[-2:])
                if domain in self.site_specific_selectors:
                    return self.site_specific_selectors[domain]
                elif main_domain in self.site_specific_selectors:
                    return self.site_specific_selectors[main_domain]
            if domain in self.site_specific_selectors:
                return self.site_specific_selectors[domain]
        
        return [
            'article', 
            '.article-body', 
            '.article-content',
            '.news-content', 
            '.content-article',
            '.entry-content',
            '.post-content',
            '.article__body',
            '.story-body',
            '.news__detail', 
            '.news_content',
            '.news-article-body',
            '.news-view-body',
            '#articleBody',
            '#articleContent',
            '#newsContent',
            '#news_body_area',
            '#newsViewArea',
            '#articeBody',
            '#content',
            'main'
        ]
    
    def _extract_content_by_tags(self, soup: BeautifulSoup, final_url: str) -> str:
        """HTML에서 태그 기반으로 본문 내용을 추출합니다.
        
        본문 추출에 실패한 경우, 주요 태그별로 내용을 추출하는 대체 방법입니다.
        
        Args:
            soup (BeautifulSoup): 파싱된 HTML
            final_url (str): 최종 URL
            
        Returns:
            str: 추출된 본문 내용
        """
        candidate_texts = []
        p_tags = soup.find_all('p')
        logger.debug(f"총 {len(p_tags)}개의 p 태그 발견")
        MIN_P_LENGTH = 10
        meaningful_p_tags = [p for p in p_tags if len(p.get_text().strip()) >= MIN_P_LENGTH]
        logger.debug(f"의미 있는 p 태그: {len(meaningful_p_tags)}개")
        if meaningful_p_tags:
            all_p_text = '\n'.join([p.get_text().strip() for p in meaningful_p_tags])
            if len(all_p_text) > 50:
                candidate_texts.append(all_p_text)
                logger.debug(f"모든 p 태그 결합 텍스트 길이: {len(all_p_text)}")
            parents = {}
            for p in meaningful_p_tags:
                parent = p.parent
                if parent:
                    if parent not in parents:
                        parents[parent] = []
                    parents[parent].append(p)
            if parents:
                main_parent = max(parents.items(), key=lambda x: len(x[1]))[0]
                content = '\n'.join([p.get_text().strip() for p in parents[main_parent]])
                if content:
                    logger.debug(f"가장 많은 p 태그({len(parents[main_parent])})를 포함한 부모 요소 텍스트 길이: {len(content)}")
                    candidate_texts.append(content)
        articles = soup.find_all('article')
        logger.debug(f"총 {len(articles)}개의 article 태그 발견")
        if articles:
            for i, article in enumerate(articles):
                p_texts = [p.get_text().strip() for p in article.find_all('p') if len(p.get_text().strip()) > 10]
                if p_texts:
                    article_content = '\n'.join(p_texts)
                    logger.debug(f"article[{i}] 내 p 태그 결합 텍스트 길이: {len(article_content)}")
                    candidate_texts.append(article_content)
                else:
                    article_text = article.get_text().strip()
                    if len(article_text) > 30:
                        logger.debug(f"article[{i}] 전체 텍스트 길이: {len(article_text)}")
                        candidate_texts.append(article_text)
        important_ids = ['content', 'main', 'article', 'news', 'body', 'story', 'text', 'container']
        for id_value in important_ids:
            elements = soup.find_all(id=re.compile(f".*{id_value}.*", re.IGNORECASE))
            if elements:
                logger.debug(f"id='{id_value}' 요소 {len(elements)}개 발견")
                for element in elements:
                    text = element.get_text().strip()
                    if len(text) > 100:
                        candidate_texts.append(text)
        content_classes = ['article', 'content', 'body', 'text', 'news', 'story', 'main', 'detail', 'view']
        for class_name in content_classes:
            divs = soup.find_all('div', class_=re.compile(f".*{class_name}.*", re.IGNORECASE))
            if divs:
                logger.debug(f"class='{class_name}' div 요소 {len(divs)}개 발견")
                for div in divs:
                    text = div.get_text().strip()
                    if len(text) > 50:
                        candidate_texts.append(text)
        all_divs = soup.find_all('div')
        if all_divs:
            text_lengths = [(div, len(div.get_text().strip())) for div in all_divs]
            text_lengths.sort(key=lambda x: x[1], reverse=True)
            top_divs = text_lengths[:min(5, len(text_lengths))]
            for div, length in top_divs:
                if length > 30:
                    logger.debug(f"상위 div 텍스트 길이: {length}")
                    candidate_texts.append(div.get_text().strip())
        domain_match = re.search(r'https?://([^/]+)', final_url)
        if domain_match:
            domain = domain_match.group(1)
            logger.debug(f"사이트별 맞춤 추출 시도: {domain}")
            if 'news.naver.com' in domain:
                article_body = soup.select_one('#articleBody, #newsEndContents, #articeBody, .end_body')
                if article_body:
                    logger.debug(f"네이버 뉴스 본문 요소 발견")
                    candidate_texts.append(article_body.get_text().strip())
            elif 'news.daum.net' in domain:
                article_body = soup.select_one('.article_view')
                if article_body:
                    logger.debug(f"다음 뉴스 본문 요소 발견")
                    candidate_texts.append(article_body.get_text().strip())
            elif 'news.google.com' in domain:
                return "원본 기사를 보려면 링크 방문이 필요합니다. 구글 뉴스는 미리보기만 제공합니다."
        logger.debug(f"총 {len(candidate_texts)}개의 후보 텍스트 수집됨")
        if candidate_texts:
            sorted_candidates = sorted(candidate_texts, key=len, reverse=True)
            logger.debug(f"가장 긴 후보 텍스트 길이: {len(sorted_candidates[0])}")
            valid_candidates = [t for t in sorted_candidates if len(t) >= 30]
            if valid_candidates:
                return valid_candidates[0]
        all_text = soup.get_text(separator='\n').strip()
        if len(all_text) > 0:
            logger.debug(f"모든 추출 방법 실패, 페이지 전체 텍스트 반환 (길이: {len(all_text)})")
            return all_text[:1000000] + ("..." if len(all_text) > 1000000 else "")
        return "내용을 추출할 수 없습니다."
        
    def _fetch_with_selenium(self, url: str, ua: Optional[UserAgent] = None, max_content_length: int = 1000000) -> Tuple[str, str, Dict[str, Any]]:
        """
        Selenium을 사용하여 헤드리스 모드에서 페이지를 로드한 후, 최종 URL 및 본문 내용을 추출합니다.
        Selenium Manager가 자동으로 크롬드라이버를 관리합니다.
        """
        ua = ua or self.user_agent
        ua_string = ua.random

        options = Options()
        # 최신 headless 모드 사용 (Chrome 109 이상 권장)
        options.add_argument("--headless=new")
        options.add_argument(f"user-agent={ua_string}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
        # 최신 셀레니움에서는 Selenium Manager가 자동으로 크롬드라이버를 관리합니다.
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            # 페이지 로딩을 위한 충분한 대기시간 적용
            time.sleep(random.uniform(2, 4))
            final_url = driver.current_url
            html = driver.page_source
            logger.info(f"Selenium으로 페이지 로드 완료: {url} -> {final_url}")
        except Exception as e:
            logger.error(f"Selenium fetch error: {url}, {str(e)}")
            driver.quit()
            return "", f"Error: {str(e)}", {}
        driver.quit()
        
        # 이후 BeautifulSoup을 이용하여 HTML 파싱 및 본문 추출 로직 진행
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'iframe', 'ins', 'header', 'footer', 'nav', 'aside']):
            tag.extract()
        
        metadata = {}
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else "제목 없음"
        metadata['title'] = title
        # 추가 메타데이터 및 본문 추출 로직은 기존과 동일하게 진행...
        
        # 사이트별 셀렉터 사용 등 본문 추출 로직
        main_content = None
        content_selectors = self._get_site_specific_selectors(final_url)
        logger.debug(f"컨텐츠 셀렉터 {len(content_selectors)}개 검사 중...")
        for selector in content_selectors:
            content_elems = soup.select(selector)
            if content_elems:
                main_content = max(content_elems, key=lambda e: len(e.get_text()))
                logger.debug(f"셀렉터 '{selector}'로 요소 발견")
                break
        if main_content:
            for elem in main_content.select('.reporter_area, .copyright, .byline, .article-ads, .article-tags'):
                elem.extract()
            text = main_content.get_text(separator='\n').strip()
            logger.debug(f"주요 컨텐츠 텍스트 추출 성공: {len(text)}자")
        else:
            logger.info(f"주요 컨텐츠 영역을 찾지 못해 태그 기반 추출 시도: {final_url}")
            text = self._extract_content_by_tags(soup, final_url)
        
        # 텍스트 정제
        text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
        text = re.sub(r'\s+', ' ', text)
        for pattern in [r'광고|AD|Advertisement|Sponsored',
                        r'copyright|ⓒ|\(c\)|\©',
                        r'구독하기|뉴스레터|뉴스스탠드',
                        r'톡톡톡|기사제보|오류신고',
                        r'더보기|관련기사|추천기사']:
            text = re.sub(pattern, '', text)
        if len(text) > max_content_length:
            text = text[:max_content_length] + "... [잘림]"
        
        return "", text, metadata

    
    async def fetch_content(self, url: str, user_agent: Optional[UserAgent] = None, max_content_length: int = 1000000) -> Tuple[str, str, Dict[str, Any]]:
        """주어진 URL에서 Selenium을 사용하여 웹 페이지 내용을 가져옵니다.
        
        Args:
            url (str): 크롤링할 URL
            user_agent (UserAgent, optional): UserAgent 객체. 기본값은 None.
            max_content_length (int, optional): 최대 콘텐츠 길이. 기본값은 1000000자.
            
        Returns:
            Tuple[str, str, Dict[str, Any]]: (HTML 내용, 추출된 텍스트, 추가 메타데이터)
        """
        ua = user_agent or self.user_agent
        html, text, metadata = await asyncio.to_thread(self._fetch_with_selenium, url, ua, max_content_length)
        return html, text, metadata
    
    async def process_news_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 항목을 처리하고 상세 내용을 추가합니다.
        
        Args:
            item (Dict[str, Any]): 뉴스 항목
            
        Returns:
            Dict[str, Any]: 상세 내용이 추가된 뉴스 항목
        """
        url = item['url']
        original_url = url  # 원본 URL 저장
        try:
            html, content, metadata = await self.fetch_content(url)
            original_content_found = bool(content and not content.startswith("Error:"))
            result = {
                'title': item['title'],
                'url': url,
                'content': content if original_content_found else "원본 기사를 직접 방문해야 합니다. 원본 URL: " + url,
                'raw_content': content if original_content_found else "",
                'score': 1.0,
                'source_type': 'google_news',
                'metadata': {
                    'description': metadata.get('description', ''),
                    'published': item.get('published', ''),
                    'press': metadata.get('press', item.get('source', '')),
                    'crawled_at': datetime.now().isoformat(),
                    'original_content_found': original_content_found
                }
            }
            
            if url != original_url:
                result['metadata']['original_google_link'] = original_url
                
            # 추가 메타데이터 병합
            for key, value in metadata.items():
                if key not in ['description', 'press', 'crawled_at'] and value:
                    result['metadata'][key] = value
                    
            return result
        except Exception as e:
            logger.error(f"뉴스 처리 중 오류 발생: {url}, {str(e)}")
            return {
                'title': item['title'],
                'url': url,
                'content': f"내용 가져오기 실패: {str(e)}",
                'raw_content': "",
                'score': 0.0,
                'source_type': 'google_news',
                'metadata': {
                    'description': '',
                    'published': item.get('published', ''),
                    'error': str(e),
                    'crawled_at': datetime.now().isoformat()
                }
            }
    
    async def search_all(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """키워드로 뉴스를 검색하고 각 뉴스의 상세 내용을 수집합니다.
        
        Args:
            query (str): 검색 키워드
            max_results (int, optional): 최대 결과 개수. 기본값은 10.
            
        Returns:
            List[Dict[str, Any]]: 상세 내용이 추가된 뉴스 목록
        """
        items = self.search_by_keyword(query, max_results, include_content=False)
        
        if not items:
            logger.warning(f"'{query}' 검색 결과가 없습니다.")
            return []
        
        logger.info(f"'{query}' 검색 결과 {len(items)}개 항목 발견, 상세 정보 수집 중...")
        tasks = [self.process_news_content(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"항목 처리 실패: {items[i]['url']}, 오류: {str(result)}")
                processed_results.append({
                    'title': items[i]['title'],
                    'url': items[i]['url'],
                    'content': f"내용 가져오기 실패: {str(result)}",
                    'raw_content': "",
                    'score': 0.0,
                    'source_type': 'google_news',
                    'metadata': {
                        'description': '',
                        'published': items[i].get('published', ''),
                        'press': items[i].get('source', ''),
                        'crawled_at': datetime.now().isoformat(),
                        'error': str(result)
                    }
                })
            else:
                processed_results.append(result)
        
        logger.info(f"총 {len(processed_results)}개 항목 처리 완료")
        return processed_results
    
    def save_results(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """수집한 결과를 JSON 파일로 저장합니다.
        
        Args:
            results (List[Dict[str, Any]]): 수집한 결과
            filename (str, optional): 저장할 파일명. 기본값은 None으로, 시간 기반 파일명 생성.
            
        Returns:
            str: 저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"google_news_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return filename
