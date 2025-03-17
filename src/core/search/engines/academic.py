"""
학술 검색을 위한 엔진들을 제공합니다.

이 모듈은 arXiv, PubMed 등의 학술 검색 API를 활용한 검색 클래스를 제공합니다.
"""

import asyncio
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_community.retrievers import ArxivRetriever
from langchain_community.utilities.pubmed import PubMedAPIWrapper

from src.common.logging import get_logger

# 로거 설정
logger = get_logger(__name__)

class ArxivSearcher:
    """arXiv API를 활용한 학술 논문 검색기

    이 클래스는 arXiv API를 통해 학술 논문을 검색하고 추출합니다.
    """
    
    def __init__(self, 
                 load_max_docs: int = 5, 
                 get_full_documents: bool = True, 
                 load_all_available_meta: bool = True) -> None:
        """ArxivSearcher 초기화
        
        Args:
            load_max_docs (int, optional): 검색당 최대 문서 개수. 기본값은 5.
            get_full_documents (bool, optional): 전체 문서 내용 가져오기 여부. 기본값은 True.
            load_all_available_meta (bool, optional): 모든 메타데이터 로드 여부. 기본값은 True.
        """
        self.load_max_docs = load_max_docs
        self.get_full_documents = get_full_documents
        self.load_all_available_meta = load_all_available_meta
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """arXiv에서 검색을 수행합니다.
        
        Args:
            query (str): 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            # 비동기 컨텍스트에서 동기 함수 실행
            retriever = ArxivRetriever(
                load_max_docs=self.load_max_docs,
                get_full_documents=self.get_full_documents,
                load_all_available_meta=self.load_all_available_meta
            )
            
            # 쓰레드 풀에서 동기 검색 실행
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, lambda: retriever.invoke(query))
            
            results = []
            # 순서에 따라 감소하는 점수 할당
            base_score = 1.0
            score_decrement = 1.0 / (len(docs) + 1 if docs else 1)
            
            for i, doc in enumerate(docs):
                # 메타데이터 추출
                metadata = doc.metadata
                
                # entry_id를 URL로 사용 (실제 arXiv 링크)
                url = metadata.get('entry_id', '')
                
                # 모든 유용한 메타데이터로 내용 포맷팅
                content_parts = []

                # 주요 정보
                if 'Summary' in metadata:
                    content_parts.append(f"요약: {metadata['Summary']}")

                if 'Authors' in metadata:
                    content_parts.append(f"저자: {metadata['Authors']}")

                # 출판 정보 추가
                published = metadata.get('Published')
                published_str = published.isoformat() if hasattr(published, 'isoformat') else str(published) if published else ''
                if published_str:
                    content_parts.append(f"출판일: {published_str}")

                # 추가 메타데이터
                if 'primary_category' in metadata:
                    content_parts.append(f"주요 카테고리: {metadata['primary_category']}")

                if 'categories' in metadata and metadata['categories']:
                    content_parts.append(f"카테고리: {', '.join(metadata['categories'])}")

                if 'comment' in metadata and metadata['comment']:
                    content_parts.append(f"코멘트: {metadata['comment']}")

                if 'journal_ref' in metadata and metadata['journal_ref']:
                    content_parts.append(f"저널 참조: {metadata['journal_ref']}")

                if 'doi' in metadata and metadata['doi']:
                    content_parts.append(f"DOI: {metadata['doi']}")

                # PDF 링크 추출
                pdf_link = ""
                if 'links' in metadata and metadata['links']:
                    for link in metadata['links']:
                        if 'pdf' in link:
                            pdf_link = link
                            content_parts.append(f"PDF: {pdf_link}")
                            break

                # 모든 내용 결합
                content = "\n".join(content_parts)
                
                # 통일된 결과 형식
                result = {
                    'title': metadata.get('Title', ''),
                    'url': url,
                    'content': content,
                    'raw_content': doc.page_content if self.get_full_documents else None,
                    'score': base_score - (i * score_decrement),
                    'source_type': 'arxiv',
                    'metadata': {
                        'published': published_str,
                        'authors': metadata.get('Authors', ''),
                        'summary': metadata.get('Summary', ''),
                        'categories': metadata.get('categories', []),
                        'primary_category': metadata.get('primary_category', ''),
                        'doi': metadata.get('doi', ''),
                        'journal_ref': metadata.get('journal_ref', ''),
                        'pdf_link': pdf_link,
                        'comment': metadata.get('comment', ''),
                        'crawled_at': datetime.now().isoformat()
                    }
                }
                results.append(result)
            
            logger.info(f"arXiv 검색 완료: '{query}', {len(results)}개 결과 발견")
            return results
            
        except Exception as e:
            logger.error(f"arXiv 검색 중 오류 발생: {str(e)}")
            return []
    
    async def search_all(self, queries: List[str]) -> List[Dict[str, Any]]:
        """여러 쿼리에 대해 검색을 수행합니다.
        
        Args:
            queries (List[str]): 검색 쿼리 목록
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        all_results = []
        
        for i, query in enumerate(queries):
            # API 속도 제한 준수 (3초 간격)
            if i > 0:
                await asyncio.sleep(3.0)
            
            try:
                results = await self.search(query)
                all_results.append({
                    'query': query,
                    'results': results
                })
            except Exception as e:
                logger.error(f"검색 쿼리 '{query}' 처리 중 오류 발생: {str(e)}")
                all_results.append({
                    'query': query,
                    'results': [],
                    'error': str(e)
                })
        
        return all_results


class PubMedSearcher:
    """PubMed API를 활용한 의학 논문 검색기

    이 클래스는 PubMed API를 통해 의학/생명과학 논문을 검색하고 추출합니다.
    """
    
    def __init__(self, 
                 top_k_results: int = 5,
                 doc_content_chars_max: int = 1000000,
                 email: Optional[str] = None,
                 api_key: Optional[str] = None) -> None:
        """PubMedSearcher 초기화
        
        Args:
            top_k_results (int, optional): 검색당 최대 결과 개수. 기본값은 5.
            doc_content_chars_max (int, optional): 최대 문서 내용 길이. 기본값은 1000000.
            email (str, optional): PubMed API 사용을 위한 이메일. NCBI에 필요함.
            api_key (str, optional): PubMed API 키. 높은 요청 한도 제공.
        """
        self.top_k_results = top_k_results
        self.doc_content_chars_max = doc_content_chars_max
        self.email = email or os.getenv("PUBMED_EMAIL", "your_email@example.com")
        self.api_key = api_key or os.getenv("PUBMED_API_KEY", "")
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """PubMed에서 검색을 수행합니다.
        
        Args:
            query (str): 검색 쿼리
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            # PubMed 래퍼 생성
            wrapper = PubMedAPIWrapper(
                top_k_results=self.top_k_results,
                doc_content_chars_max=self.doc_content_chars_max,
                email=self.email,
                api_key=self.api_key
            )
            
            # 쓰레드 풀에서 동기 검색 실행
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, lambda: list(wrapper.lazy_load(query)))
            
            results = []
            # 순서에 따라 감소하는 점수 할당
            base_score = 1.0
            score_decrement = 1.0 / (len(docs) + 1 if docs else 1)
            
            for i, doc in enumerate(docs):
                # 내용 포맷팅
                content_parts = []
                
                if doc.get('Published'):
                    content_parts.append(f"출판일: {doc['Published']}")
                
                if doc.get('Copyright Information'):
                    content_parts.append(f"저작권 정보: {doc['Copyright Information']}")
                
                if doc.get('Summary'):
                    content_parts.append(f"요약: {doc['Summary']}")
                
                if doc.get('Authors'):
                    content_parts.append(f"저자: {doc['Authors']}")
                
                # UID로 PubMed URL 생성
                uid = doc.get('uid', '')
                url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/" if uid else ""
                
                # 모든 내용 결합
                content = "\n".join(content_parts)
                
                # 통일된 결과 형식
                result = {
                    'title': doc.get('Title', ''),
                    'url': url,
                    'content': content,
                    'raw_content': doc.get('Summary', ''),
                    'score': base_score - (i * score_decrement),
                    'source_type': 'pubmed',
                    'metadata': {
                        'published': doc.get('Published', ''),
                        'authors': doc.get('Authors', ''),
                        'summary': doc.get('Summary', ''),
                        'copyright': doc.get('Copyright Information', ''),
                        'uid': uid,
                        'crawled_at': datetime.now().isoformat()
                    }
                }
                results.append(result)
            
            logger.info(f"PubMed 검색 완료: '{query}', {len(results)}개 결과 발견")
            return results
            
        except Exception as e:
            logger.error(f"PubMed 검색 중 오류 발생: {str(e)}")
            return []
    
    async def search_all(self, queries: List[str]) -> List[Dict[str, Any]]:
        """여러 쿼리에 대해 검색을 수행합니다.
        
        Args:
            queries (List[str]): 검색 쿼리 목록
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        all_results = []
        
        # 처음에는 작은 딜레이로 시작하고, 필요시 증가
        delay = 1.0
        
        for i, query in enumerate(queries):
            # 첫 요청이 아닌 경우 딜레이 추가
            if i > 0:
                await asyncio.sleep(delay)
            
            try:
                results = await self.search(query)
                all_results.append({
                    'query': query,
                    'results': results
                })
                
                # 결과가 있다면 딜레이 약간 감소 (최소 0.5초)
                if results:
                    delay = max(0.5, delay * 0.9)
                    
            except Exception as e:
                logger.error(f"검색 쿼리 '{query}' 처리 중 오류 발생: {str(e)}")
                all_results.append({
                    'query': query,
                    'results': [],
                    'error': str(e)
                })
                
                # 오류 발생시 딜레이 증가 (최대 5초)
                delay = min(5.0, delay * 1.5)
        
        return all_results
