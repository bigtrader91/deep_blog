"""
검색 결과에서 콘텐츠를 가져오는 유틸리티 클래스

이 모듈은 검색 결과의 URL에서 웹 페이지 내용을 추출하는 기능을 제공합니다.
"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)


class ContentFetcher:
    """검색 결과의 URL에서 콘텐츠를 가져오는 클래스
    
    이 클래스는 검색 결과의 URL에서 웹 페이지 내용을 비동기적으로 추출하는 메서드를 제공합니다.
    """
    
    def __init__(self, user_agent: Optional[str] = None):
        """ContentFetcher 초기화
        
        Args:
            user_agent (Optional[str]): 요청에 사용할 User-Agent 헤더. 기본값은 None.
        """
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
    
    async def fetch_contents_from_search_results(self, search_results: Dict[str, Any], 
                                                max_items: int = 5) -> List[Dict[str, str]]:
        """네이버 검색 결과에서 각 링크의 내용을 병렬로 추출합니다.
        
        Args:
            search_results (Dict[str, Any]): naver_search 함수의 결과
            max_items (int, optional): 처리할 최대 항목 수. 기본값은 5.
            
        Returns:
            List[Dict[str, str]]: 각 URL에서 추출한 콘텐츠 목록
            
        Example:
            ```python
            fetcher = ContentFetcher()
            search_results = naver_search("골절로 인한 통증 치료 방법", "kin")
            contents = await fetcher.fetch_contents_from_search_results(search_results)
            for content in contents:
                print(f"제목: {content['title']}")
                print(f"내용: {content['content'][:100]}...")
            ```
        """
        items = search_results.get('items', [])
        if not items:
            return []
        
        # 처리할 항목 수 제한
        items = items[:max_items]
        
        # 모든 항목에 대해 병렬로 내용 추출
        tasks = [self._fetch_content(item) for item in items]
        contents = await asyncio.gather(*tasks)
        
        return contents
    
    async def _fetch_content(self, item: Dict[str, Any]) -> Dict[str, str]:
        """단일 검색 결과 항목에서 콘텐츠를 추출합니다.
        
        Args:
            item (Dict[str, Any]): 검색 결과 항목
            
        Returns:
            Dict[str, str]: 추출된 콘텐츠
        """
        url = item.get('link', '') or item.get('url', '')
        if not url:
            return {'url': '', 'title': item.get('title', ''), 'content': '', 'error': '링크가 없습니다.'}
        
        try:
            headers = {'User-Agent': self.user_agent}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return {'url': url, 'title': item.get('title', ''), 'content': '', 'error': f'상태 코드: {response.status}'}
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 결과 저장 딕셔너리
                    content = {
                        'url': url,
                        'title': item.get('title', '').replace('<b>', '').replace('</b>', ''),
                        'description': item.get('description', '').replace('<b>', '').replace('</b>', ''),
                        'content': '',
                        'error': None
                    }
                    
                    # 네이버 지식IN의 경우
                    if 'kin.naver.com' in url:
                        content.update(self._extract_naver_kin_content(soup))
                    
                    # 네이버 뉴스의 경우
                    elif 'news.naver.com' in url:
                        content.update(self._extract_naver_news_content(soup))
                    
                    # 네이버 블로그의 경우
                    elif 'blog.naver.com' in url:
                        content.update(self._extract_naver_blog_content(soup))
                    
                    # 네이버 용어사전의 경우
                    elif 'terms.naver.com' in url:
                        content.update(self._extract_naver_terms_content(soup))
                    
                    # 기타 일반 웹페이지의 경우
                    else:
                        content.update(self._extract_general_content(soup))
                    
                    # 내용이 없으면 에러 메시지 추가
                    if not content['content']:
                        content['error'] = '내용을 추출할 수 없습니다. 페이지 구조가 변경되었거나 접근이 제한된 페이지일 수 있습니다.'
                    
                    return content
        
        except Exception as e:
            return {'url': url, 'title': item.get('title', ''), 'content': '', 'error': f'오류: {str(e)}'}
    
    def _extract_naver_kin_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """네이버 지식인 페이지에서 콘텐츠를 추출합니다.
        
        Args:
            soup (BeautifulSoup): 파싱할 HTML 콘텐츠의 BeautifulSoup 객체
            
        Returns:
            Dict[str, Any]: 추출된 콘텐츠
        """
        content = {}
        
        title_element = soup.select_one('.title')
        question_element = soup.select_one('.c-heading__content')
        answer_element = soup.select_one('.se-main-container')
        
        # 답변자 정보와 채택 여부 확인
        is_adopted = False
        answerer_grade = None
        
        # 채택 답변 확인
        adoption_element = soup.select_one('.badge__adoption')
        if adoption_element:
            is_adopted = True
        
        # 답변자 등급 확인
        # 등급은 일반적으로 프로필 이미지 옆이나 닉네임 근처에 표시됨
        answerer_info = soup.select_one('.c-userinfo__author') or soup.select_one('.answer-author')
        if answerer_info:
            grade_element = answerer_info.select_one('.grade') or answerer_info.select_one('.badge')
            if grade_element:
                answerer_grade = grade_element.get_text(strip=True)
            
            # 답변자 이름도 추출
            name_element = answerer_info.select_one('.c-userinfo__author-name') or answerer_info
            if name_element:
                content['answerer_name'] = name_element.get_text(strip=True)
        
        # 채택 여부와 등급 정보 저장
        content['is_adopted'] = is_adopted
        content['answerer_grade'] = answerer_grade
        
        if title_element:
            content['title'] = title_element.get_text(strip=True)
        
        if question_element:
            content['question'] = question_element.get_text(strip=True)
        
        if answer_element:
            content['answer'] = answer_element.get_text(strip=True)
            content['content'] = content['answer']
        
        return content
    
    def _extract_naver_news_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """네이버 뉴스 페이지에서 콘텐츠를 추출합니다.
        
        Args:
            soup (BeautifulSoup): 파싱할 HTML 콘텐츠의 BeautifulSoup 객체
            
        Returns:
            Dict[str, Any]: 추출된 콘텐츠
        """
        content = {}
        
        title_element = soup.select_one('#title_area') or soup.select_one('.media_end_head_headline')
        content_element = soup.select_one('#newsct_article') or soup.select_one('#dic_area')
        
        if title_element:
            content['title'] = title_element.get_text(strip=True)
        
        if content_element:
            content['content'] = content_element.get_text(strip=True)
        
        return content
    
    def _extract_naver_blog_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """네이버 블로그 페이지에서 콘텐츠를 추출합니다.
        
        Args:
            soup (BeautifulSoup): 파싱할 HTML 콘텐츠의 BeautifulSoup 객체
            
        Returns:
            Dict[str, Any]: 추출된 콘텐츠
        """
        content = {}
        
        title_element = soup.select_one('.se-title-text')
        content_element = soup.select_one('.se-main-container')
        
        if title_element:
            content['title'] = title_element.get_text(strip=True)
        
        if content_element:
            content['content'] = content_element.get_text(strip=True)
        
        return content
    
    def _extract_naver_terms_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """네이버 용어사전 페이지에서 콘텐츠를 추출합니다.
        
        Args:
            soup (BeautifulSoup): 파싱할 HTML 콘텐츠의 BeautifulSoup 객체
            
        Returns:
            Dict[str, Any]: 추출된 콘텐츠
        """
        content = {}
        
        title_element = soup.select_one('.headword') or soup.select_one('.word_title')
        content_element = soup.select_one('#size_ct') or soup.select_one('.detail_area')
        
        if title_element:
            content['title'] = title_element.get_text(strip=True)
        
        if content_element:
            content['content'] = content_element.get_text(strip=True)
        
        return content
    
    def _extract_general_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """일반 웹페이지에서 콘텐츠를 추출합니다.
        
        Args:
            soup (BeautifulSoup): 파싱할 HTML 콘텐츠의 BeautifulSoup 객체
            
        Returns:
            Dict[str, Any]: 추출된 콘텐츠
        """
        content = {}
        
        title_element = soup.select_one('title') or soup.select_one('h1')
        content_element = soup.select_one('article') or soup.select_one('.content') or soup.select_one('#content')
        
        if title_element:
            content['title'] = title_element.get_text(strip=True)
        
        if content_element:
            content['content'] = content_element.get_text(strip=True)
        else:
            # 본문 요소를 찾지 못한 경우 body 전체 텍스트 추출
            body = soup.select_one('body')
            if body:
                content['content'] = body.get_text(strip=True)
        
        return content
    
    def fetch_contents_from_search_results_sync(self, search_results: Dict[str, Any], 
                                              max_items: int = 5) -> List[Dict[str, str]]:
        """fetch_contents_from_search_results의 동기 버전입니다.
        
        Args:
            search_results (Dict[str, Any]): naver_search 함수의 결과
            max_items (int, optional): 처리할 최대 항목 수. 기본값은 5.
            
        Returns:
            List[Dict[str, str]]: 각 URL에서 추출한 콘텐츠 목록
            
        Example:
            ```python
            fetcher = ContentFetcher()
            search_results = naver_search("골절로 인한 통증 치료 방법", "kin")
            contents = fetcher.fetch_contents_from_search_results_sync(search_results)
            for content in contents:
                print(f"제목: {content['title']}")
                print(f"내용: {content['content'][:100]}...")
            ```
        """
        # 현재 실행 중인 이벤트 루프 가져오기 시도
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 이벤트 루프가 없는 경우 새로 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Windows에서는 asyncio.run()이 제대로 작동하지 않을 수 있어 직접 실행
        if loop.is_running():
            # 이미 이벤트 루프가 실행 중인 경우 (Jupyter 노트북 등에서)
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                logger.warning("nest_asyncio 패키지를 설치하는 것이 좋습니다: pip install nest_asyncio")
            
            return loop.run_until_complete(self.fetch_contents_from_search_results(search_results, max_items))
        else:
            # 이벤트 루프가 실행 중이 아닌 경우
            try:
                return asyncio.run(self.fetch_contents_from_search_results(search_results, max_items))
            except RuntimeError:
                # asyncio.run()이 실패하면 직접 실행
                return loop.run_until_complete(self.fetch_contents_from_search_results(search_results, max_items))
