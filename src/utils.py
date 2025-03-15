# src/utils.py
import os
import asyncio
import requests
import urllib.request
import urllib.parse
import json
from typing import List, Optional, Dict, Any
import random

from exa_py import Exa
from linkup import LinkupClient
from tavily import AsyncTavilyClient

from langchain_community.retrievers import ArxivRetriever
from langchain_community.utilities.pubmed import PubMedAPIWrapper
from langsmith import traceable

from src.state import Section
from src.data_crawler import NaverCrawler  # 이 줄 추가
CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


def naver_search(query: str, search_type: str = "shop") -> Dict[str, Any]:
    """
    네이버 API를 사용하여 검색 결과를 가져옵니다.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 환경 변수에 설정해야 합니다.")
    
    enc_text = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/{search_type}.json?query={enc_text}"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    
    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if rescode == 200:
            return json.loads(response.read().decode('utf-8'))
        else:
            print("Error Code:", rescode)
            return {}
    except Exception as e:
        print("검색 중 예외 발생:", e)
        return {}


def fetch_naver_content(url: str) -> Dict[str, str]:
    """
    네이버 웹페이지의 내용을 스크래핑하여 추출합니다.
    
    Args:
        url (str): 스크래핑할 네이버 URL
        
    Returns:
        Dict[str, str]: 추출된 내용 (제목, 본문 등)
        
    Raises:
        ImportError: 필요한 라이브러리가 설치되어 있지 않은 경우
        Exception: 웹페이지 접근 또는 파싱 과정에서 오류가 발생한 경우
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("requests와 beautifulsoup4 패키지를 설치해야 합니다. pip install requests beautifulsoup4")
    
    try:
        # User-Agent 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 웹페이지 요청
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 에러 발생 시 예외 발생
        
        # 인코딩 확인 및 설정
        if response.encoding.lower() != 'utf-8':
            response.encoding = 'utf-8'
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 결과 저장 딕셔너리
        content = {
            'url': url,
            'title': '',
            'content': '',
            'error': None
        }
        
        # 네이버 지식IN의 경우
        if 'kin.naver.com' in url:
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
        
        # 네이버 뉴스의 경우
        elif 'news.naver.com' in url:
            title_element = soup.select_one('#title_area') or soup.select_one('.media_end_head_headline')
            content_element = soup.select_one('#newsct_article') or soup.select_one('#dic_area')
            
            if title_element:
                content['title'] = title_element.get_text(strip=True)
            
            if content_element:
                content['content'] = content_element.get_text(strip=True)
        

        

        
        # 내용이 없으면 에러 메시지 추가
        if not content['content']:
            content['error'] = '내용을 추출할 수 없습니다. 페이지 구조가 변경되었거나 접근이 제한된 페이지일 수 있습니다.'
        
        return content
    
    except requests.exceptions.RequestException as e:
        return {'url': url, 'title': '', 'content': '', 'error': f'요청 오류: {str(e)}'}
    except Exception as e:
        return {'url': url, 'title': '', 'content': '', 'error': f'스크래핑 오류: {str(e)}'}


def get_config_value(value):
    """
    Helper function to handle both string and enum cases of configuration values
    """
    return value if isinstance(value, str) else value.value

def get_search_params(search_api: str, search_api_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Filters the search_api_config dictionary to include only parameters accepted by the specified search API.

    Args:
        search_api (str): The search API identifier (e.g., "exa", "tavily").
        search_api_config (Optional[Dict[str, Any]]): The configuration dictionary for the search API.

    Returns:
        Dict[str, Any]: A dictionary of parameters to pass to the search function.
    """
    # Define accepted parameters for each search API
    SEARCH_API_PARAMS = {
        "exa": ["max_characters", "num_results", "include_domains", "exclude_domains", "subpages"],
        "tavily": [],  # Tavily currently accepts no additional parameters
        "perplexity": [],  # Perplexity accepts no additional parameters
        "arxiv": ["load_max_docs", "get_full_documents", "load_all_available_meta"],
        "pubmed": ["top_k_results", "email", "api_key", "doc_content_chars_max"],
        "linkup": ["depth"],
        "data_crawler": ["display", "include_google", "max_content_length", "max_results"],  # 매개변수 추가
    }

    # Get the list of accepted parameters for the given search API
    accepted_params = SEARCH_API_PARAMS.get(search_api, [])

    # If no config provided, return an empty dict
    if not search_api_config:
        return {}

    # Filter the config to only include accepted parameters
    return {k: v for k, v in search_api_config.items() if k in accepted_params}

def deduplicate_and_format_sources(search_response, max_tokens_per_source, include_raw_content=True):
    """
    Takes a list of search responses and formats them into a readable string.
    Limits the raw_content to approximately max_tokens_per_source tokens.
 
    Args:
        search_responses: List of search response dicts, each containing:
            - query: str
            - results: List of dicts with fields:
                - title: str
                - url: str
                - content: str
                - score: float
                - raw_content: str|None
        max_tokens_per_source: int
        include_raw_content: bool
            
    Returns:
        str: Formatted string with deduplicated sources
    """
     # Collect all results
    sources_list = []
    for response in search_response:
        sources_list.extend(response['results'])
    
    # Deduplicate by URL
    unique_sources = {source['url']: source for source in sources_list}

    # Format output
    formatted_text = "Content from sources:\n"
    for i, source in enumerate(unique_sources.values(), 1):
        formatted_text += f"{'='*80}\n"  # Clear section separator
        formatted_text += f"Source: {source['title']}\n"
        formatted_text += f"{'-'*80}\n"  # Subsection separator
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += f"Most relevant content from source: {source['content']}\n===\n"
        if include_raw_content:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get('raw_content', '')
            if raw_content is None:
                raw_content = ''
                print(f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
        formatted_text += f"{'='*80}\n\n" # End section separator
                
    return formatted_text.strip()

def format_sections(sections: list[Section]) -> str:
    """ Format a list of sections into a string """
    formatted_str = ""
    for idx, section in enumerate(sections, 1):
        formatted_str += f"""
{'='*60}
Section {idx}: {section.name}
{'='*60}
Description:
{section.description}
Requires Research: 
{section.research}

Content:
{section.content if section.content else '[Not yet written]'}

"""
    return formatted_str

@traceable
async def tavily_search_async(search_queries):
    """
    Performs concurrent web searches using the Tavily API.

    Args:
        search_queries (List[SearchQuery]): List of search queries to process

    Returns:
            List[dict]: List of search responses from Tavily API, one per query. Each response has format:
                {
                    'query': str, # The original search query
                    'follow_up_questions': None,      
                    'answer': None,
                    'images': list,
                    'results': [                     # List of search results
                        {
                            'title': str,            # Title of the webpage
                            'url': str,              # URL of the result
                            'content': str,          # Summary/snippet of content
                            'score': float,          # Relevance score
                            'raw_content': str|None  # Full page content if available
                        },
                        ...
                    ]
                }
    """
    tavily_async_client = AsyncTavilyClient()
    search_tasks = []
    for query in search_queries:
            search_tasks.append(
                tavily_async_client.search(
                    query,
                    max_results=5,
                    include_raw_content=True,
                    topic="general"
                )
            )

    # Execute all searches concurrently
    search_docs = await asyncio.gather(*search_tasks)

    return search_docs

@traceable
def perplexity_search(search_queries):
    """Search the web using the Perplexity API.
    
    Args:
        search_queries (List[SearchQuery]): List of search queries to process
  
    Returns:
        List[dict]: List of search responses from Perplexity API, one per query. Each response has format:
            {
                'query': str,                    # The original search query
                'follow_up_questions': None,      
                'answer': None,
                'images': list,
                'results': [                     # List of search results
                    {
                        'title': str,            # Title of the search result
                        'url': str,              # URL of the result
                        'content': str,          # Summary/snippet of content
                        'score': float,          # Relevance score
                        'raw_content': str|None  # Full content or None for secondary citations
                    },
                    ...
                ]
            }
    """

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}"
    }
    
    search_docs = []
    for query in search_queries:

        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "Search the web and provide factual information with sources."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Parse the response
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", ["https://perplexity.ai"])
        
        # Create results list for this query
        results = []
        
        # First citation gets the full content
        results.append({
            "title": f"Perplexity Search, Source 1",
            "url": citations[0],
            "content": content,
            "raw_content": content,
            "score": 1.0  # Adding score to match Tavily format
        })
        
        # Add additional citations without duplicating content
        for i, citation in enumerate(citations[1:], start=2):
            results.append({
                "title": f"Perplexity Search, Source {i}",
                "url": citation,
                "content": "See primary source for full content",
                "raw_content": None,
                "score": 0.5  # Lower score for secondary sources
            })
        
        # Format response to match Tavily structure
        search_docs.append({
            "query": query,
            "follow_up_questions": None,
            "answer": None,
            "images": [],
            "results": results
        })
    
    return search_docs

@traceable
async def exa_search(search_queries, max_characters: Optional[int] = None, num_results=5, 
                     include_domains: Optional[List[str]] = None, 
                     exclude_domains: Optional[List[str]] = None,
                     subpages: Optional[int] = None):
    """Search the web using the Exa API.
    
    Args:
        search_queries (List[SearchQuery]): List of search queries to process
        max_characters (int, optional): Maximum number of characters to retrieve for each result's raw content.
                                       If None, the text parameter will be set to True instead of an object.
        num_results (int): Number of search results per query. Defaults to 5.
        include_domains (List[str], optional): List of domains to include in search results. 
            When specified, only results from these domains will be returned.
        exclude_domains (List[str], optional): List of domains to exclude from search results.
            Cannot be used together with include_domains.
        subpages (int, optional): Number of subpages to retrieve per result. If None, subpages are not retrieved.
        
    Returns:
        List[dict]: List of search responses from Exa API, one per query. Each response has format:
            {
                'query': str,                    # The original search query
                'follow_up_questions': None,      
                'answer': None,
                'images': list,
                'results': [                     # List of search results
                    {
                        'title': str,            # Title of the search result
                        'url': str,              # URL of the result
                        'content': str,          # Summary/snippet of content
                        'score': float,          # Relevance score
                        'raw_content': str|None  # Full content or None for secondary citations
                    },
                    ...
                ]
            }
    """
    # Check that include_domains and exclude_domains are not both specified
    if include_domains and exclude_domains:
        raise ValueError("Cannot specify both include_domains and exclude_domains")
    
    # Initialize Exa client (API key should be configured in your .env file)
    exa = Exa(api_key = f"{os.getenv('EXA_API_KEY')}")
    
    # Define the function to process a single query
    async def process_query(query):
        # Use run_in_executor to make the synchronous exa call in a non-blocking way
        loop = asyncio.get_event_loop()
        
        # Define the function for the executor with all parameters
        def exa_search_fn():
            # Build parameters dictionary
            kwargs = {
                # Set text to True if max_characters is None, otherwise use an object with max_characters
                "text": True if max_characters is None else {"max_characters": max_characters},
                "summary": True,  # This is an amazing feature by EXA. It provides an AI generated summary of the content based on the query
                "num_results": num_results
            }
            
            # Add optional parameters only if they are provided
            if subpages is not None:
                kwargs["subpages"] = subpages
                
            if include_domains:
                kwargs["include_domains"] = include_domains
            elif exclude_domains:
                kwargs["exclude_domains"] = exclude_domains
                
            return exa.search_and_contents(query, **kwargs)
        
        response = await loop.run_in_executor(None, exa_search_fn)
        
        # Format the response to match the expected output structure
        formatted_results = []
        seen_urls = set()  # Track URLs to avoid duplicates
        
        # Helper function to safely get value regardless of if item is dict or object
        def get_value(item, key, default=None):
            if isinstance(item, dict):
                return item.get(key, default)
            else:
                return getattr(item, key, default) if hasattr(item, key) else default
        
        # Access the results from the SearchResponse object
        results_list = get_value(response, 'results', [])
        
        # First process all main results
        for result in results_list:
            # Get the score with a default of 0.0 if it's None or not present
            score = get_value(result, 'score', 0.0)
            
            # Combine summary and text for content if both are available
            text_content = get_value(result, 'text', '')
            summary_content = get_value(result, 'summary', '')
            
            content = text_content
            if summary_content:
                if content:
                    content = f"{summary_content}\n\n{content}"
                else:
                    content = summary_content
            
            title = get_value(result, 'title', '')
            url = get_value(result, 'url', '')
            
            # Skip if we've seen this URL before (removes duplicate entries)
            if url in seen_urls:
                continue
                
            seen_urls.add(url)
            
            # Main result entry
            result_entry = {
                "title": title,
                "url": url,
                "content": content,
                "score": score,
                "raw_content": text_content
            }
            
            # Add the main result to the formatted results
            formatted_results.append(result_entry)
        
        # Now process subpages only if the subpages parameter was provided
        if subpages is not None:
            for result in results_list:
                subpages_list = get_value(result, 'subpages', [])
                for subpage in subpages_list:
                    # Get subpage score
                    subpage_score = get_value(subpage, 'score', 0.0)
                    
                    # Combine summary and text for subpage content
                    subpage_text = get_value(subpage, 'text', '')
                    subpage_summary = get_value(subpage, 'summary', '')
                    
                    subpage_content = subpage_text
                    if subpage_summary:
                        if subpage_content:
                            subpage_content = f"{subpage_summary}\n\n{subpage_content}"
                        else:
                            subpage_content = subpage_summary
                    
                    subpage_url = get_value(subpage, 'url', '')
                    
                    # Skip if we've seen this URL before
                    if subpage_url in seen_urls:
                        continue
                        
                    seen_urls.add(subpage_url)
                    
                    formatted_results.append({
                        "title": get_value(subpage, 'title', ''),
                        "url": subpage_url,
                        "content": subpage_content,
                        "score": subpage_score,
                        "raw_content": subpage_text
                    })
        
        # Collect images if available (only from main results to avoid duplication)
        images = []
        for result in results_list:
            image = get_value(result, 'image')
            if image and image not in images:  # Avoid duplicate images
                images.append(image)
                
        return {
            "query": query,
            "follow_up_questions": None,
            "answer": None,
            "images": images,
            "results": formatted_results
        }
    
    # Process all queries sequentially with delay to respect rate limit
    search_docs = []
    for i, query in enumerate(search_queries):
        try:
            # Add delay between requests (0.25s = 4 requests per second, well within the 5/s limit)
            if i > 0:  # Don't delay the first request
                await asyncio.sleep(0.25)
            
            result = await process_query(query)
            search_docs.append(result)
        except Exception as e:
            # Handle exceptions gracefully
            print(f"Error processing query '{query}': {str(e)}")
            # Add a placeholder result for failed queries to maintain index alignment
            search_docs.append({
                "query": query,
                "follow_up_questions": None,
                "answer": None,
                "images": [],
                "results": [],
                "error": str(e)
            })
            
            # Add additional delay if we hit a rate limit error
            if "429" in str(e):
                print("Rate limit exceeded. Adding additional delay...")
                await asyncio.sleep(1.0)  # Add a longer delay if we hit a rate limit
    
    return search_docs

@traceable
async def arxiv_search_async(search_queries, load_max_docs=5, get_full_documents=True, load_all_available_meta=True):
    """
    Performs concurrent searches on arXiv using the ArxivRetriever.

    Args:
        search_queries (List[str]): List of search queries or article IDs
        load_max_docs (int, optional): Maximum number of documents to return per query. Default is 5.
        get_full_documents (bool, optional): Whether to fetch full text of documents. Default is True.
        load_all_available_meta (bool, optional): Whether to load all available metadata. Default is True.

    Returns:
        List[dict]: List of search responses from arXiv, one per query. Each response has format:
            {
                'query': str,                    # The original search query
                'follow_up_questions': None,      
                'answer': None,
                'images': [],
                'results': [                     # List of search results
                    {
                        'title': str,            # Title of the paper
                        'url': str,              # URL (Entry ID) of the paper
                        'content': str,          # Formatted summary with metadata
                        'score': float,          # Relevance score (approximated)
                        'raw_content': str|None  # Full paper content if available
                    },
                    ...
                ]
            }
    """
    
    async def process_single_query(query):
        try:
            # Create retriever for each query
            retriever = ArxivRetriever(
                load_max_docs=load_max_docs,
                get_full_documents=get_full_documents,
                load_all_available_meta=load_all_available_meta
            )
            
            # Run the synchronous retriever in a thread pool
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, lambda: retriever.invoke(query))
            
            results = []
            # Assign decreasing scores based on the order
            base_score = 1.0
            score_decrement = 1.0 / (len(docs) + 1 if docs else 1)  # 0 대신 1 사용
            
            for i, doc in enumerate(docs):
                # Extract metadata
                metadata = doc.metadata
                
                # Use entry_id as the URL (this is the actual arxiv link)
                url = metadata.get('entry_id', '')
                
                # Format content with all useful metadata
                content_parts = []

                # Primary information
                if 'Summary' in metadata:
                    content_parts.append(f"Summary: {metadata['Summary']}")

                if 'Authors' in metadata:
                    content_parts.append(f"Authors: {metadata['Authors']}")

                # Add publication information
                published = metadata.get('Published')
                published_str = published.isoformat() if hasattr(published, 'isoformat') else str(published) if published else ''
                if published_str:
                    content_parts.append(f"Published: {published_str}")

                # Add additional metadata if available
                if 'primary_category' in metadata:
                    content_parts.append(f"Primary Category: {metadata['primary_category']}")

                if 'categories' in metadata and metadata['categories']:
                    content_parts.append(f"Categories: {', '.join(metadata['categories'])}")

                if 'comment' in metadata and metadata['comment']:
                    content_parts.append(f"Comment: {metadata['comment']}")

                if 'journal_ref' in metadata and metadata['journal_ref']:
                    content_parts.append(f"Journal Reference: {metadata['journal_ref']}")

                if 'doi' in metadata and metadata['doi']:
                    content_parts.append(f"DOI: {metadata['doi']}")

                # Get PDF link if available in the links
                pdf_link = ""
                if 'links' in metadata and metadata['links']:
                    for link in metadata['links']:
                        if 'pdf' in link:
                            pdf_link = link
                            content_parts.append(f"PDF: {pdf_link}")
                            break

                # Join all content parts with newlines 
                content = "\n".join(content_parts)
                
                result = {
                    'title': metadata.get('Title', ''),
                    'url': url,  # Using entry_id as the URL
                    'content': content,
                    'score': base_score - (i * score_decrement),
                    'raw_content': doc.page_content if get_full_documents else None
                }
                results.append(result)
                
            return {
                'query': query,
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': results
            }
        except Exception as e:
            # Handle exceptions gracefully
            print(f"Error processing arXiv query '{query}': {str(e)}")
            return {
                'query': query,
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': [],
                'error': str(e)
            }
    
    # Process queries sequentially with delay to respect arXiv rate limit (1 request per 3 seconds)
    search_docs = []
    for i, query in enumerate(search_queries):
        try:
            # Add delay between requests (3 seconds per ArXiv's rate limit)
            if i > 0:  # Don't delay the first request
                await asyncio.sleep(3.0)
            
            result = await process_single_query(query)
            search_docs.append(result)
        except Exception as e:
            # Handle exceptions gracefully
            print(f"Error processing arXiv query '{query}': {str(e)}")
            search_docs.append({
                'query': query,
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': [],
                'error': str(e)
            })
            
            # Add additional delay if we hit a rate limit error
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("ArXiv rate limit exceeded. Adding additional delay...")
                await asyncio.sleep(5.0)  # Add a longer delay if we hit a rate limit
    
    return search_docs

@traceable
async def pubmed_search_async(search_queries, top_k_results=5, email=None, api_key=None, doc_content_chars_max=4000):
    """
    Performs concurrent searches on PubMed using the PubMedAPIWrapper.

    Args:
        search_queries (List[str]): List of search queries
        top_k_results (int, optional): Maximum number of documents to return per query. Default is 5.
        email (str, optional): Email address for PubMed API. Required by NCBI.
        api_key (str, optional): API key for PubMed API for higher rate limits.
        doc_content_chars_max (int, optional): Maximum characters for document content. Default is 4000.

    Returns:
        List[dict]: List of search responses from PubMed, one per query. Each response has format:
            {
                'query': str,                    # The original search query
                'follow_up_questions': None,      
                'answer': None,
                'images': [],
                'results': [                     # List of search results
                    {
                        'title': str,            # Title of the paper
                        'url': str,              # URL to the paper on PubMed
                        'content': str,          # Formatted summary with metadata
                        'score': float,          # Relevance score (approximated)
                        'raw_content': str       # Full abstract content
                    },
                    ...
                ]
            }
    """
    
    async def process_single_query(query):
        try:
            # print(f"Processing PubMed query: '{query}'")
            
            # Create PubMed wrapper for the query
            wrapper = PubMedAPIWrapper(
                top_k_results=top_k_results,
                doc_content_chars_max=doc_content_chars_max,
                email=email if email else "your_email@example.com",
                api_key=api_key if api_key else ""
            )
            
            # Run the synchronous wrapper in a thread pool
            loop = asyncio.get_event_loop()
            
            # Use wrapper.lazy_load instead of load to get better visibility
            docs = await loop.run_in_executor(None, lambda: list(wrapper.lazy_load(query)))
            
            print(f"Query '{query}' returned {len(docs)} results")
            
            results = []
            # Assign decreasing scores based on the order
            base_score = 1.0
            score_decrement = 1.0 / (len(docs) + 1 if docs else 1)  # 0 대신 1 사용
            
            for i, doc in enumerate(docs):
                # Format content with metadata
                content_parts = []
                
                if doc.get('Published'):
                    content_parts.append(f"Published: {doc['Published']}")
                
                if doc.get('Copyright Information'):
                    content_parts.append(f"Copyright Information: {doc['Copyright Information']}")
                
                if doc.get('Summary'):
                    content_parts.append(f"Summary: {doc['Summary']}")
                
                # Generate PubMed URL from the article UID
                uid = doc.get('uid', '')
                url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/" if uid else ""
                
                # Join all content parts with newlines
                content = "\n".join(content_parts)
                
                result = {
                    'title': doc.get('Title', ''),
                    'url': url,
                    'content': content,
                    'score': base_score - (i * score_decrement),
                    'raw_content': doc.get('Summary', '')
                }
                results.append(result)
            
            return {
                'query': query,
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': results
            }
        except Exception as e:
            # Handle exceptions with more detailed information
            error_msg = f"Error processing PubMed query '{query}': {str(e)}"
            print(error_msg)
            import traceback
            print(traceback.format_exc())  # Print full traceback for debugging
            
            return {
                'query': query,
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': [],
                'error': str(e)
            }
    
    # Process all queries with a reasonable delay between them
    search_docs = []
    
    # Start with a small delay that increases if we encounter rate limiting
    delay = 1.0  # Start with a more conservative delay
    
    for i, query in enumerate(search_queries):
        try:
            # Add delay between requests
            if i > 0:  # Don't delay the first request
                # print(f"Waiting {delay} seconds before next query...")
                await asyncio.sleep(delay)
            
            result = await process_single_query(query)
            search_docs.append(result)
            
            # If query was successful with results, we can slightly reduce delay (but not below minimum)
            if result.get('results') and len(result['results']) > 0:
                delay = max(0.5, delay * 0.9)  # Don't go below 0.5 seconds
            
        except Exception as e:
            # Handle exceptions gracefully
            error_msg = f"Error in main loop processing PubMed query '{query}': {str(e)}"
            print(error_msg)
            
            search_docs.append({
                'query': query,
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': [],
                'error': str(e)
            })
            
            # If we hit an exception, increase delay for next query
            delay = min(5.0, delay * 1.5)  # Don't exceed 5 seconds
    
    return search_docs

@traceable
async def linkup_search(search_queries, depth: Optional[str] = "standard"):
    """
    Linkup API를 사용하여 동시에 웹 검색을 수행합니다.

    Args:
        search_queries (List[SearchQuery]): 처리할 검색 쿼리 목록
        depth (str, optional): "standard" (기본값) 또는 "deep". 자세한 내용은 https://docs.linkup.so/pages/documentation/get-started/concepts 참조

    Returns:
        List[dict]: Linkup API의 검색 응답 목록(쿼리당 하나). 각 응답의 형식:
            {
                'results': [            # 검색 결과 목록
                    {
                        'title': str,   # 검색 결과의 제목
                        'url': str,     # 결과의 URL
                        'content': str, # 내용의 요약/스니펫
                    },
                    ...
                ]
            }
    """
    client = LinkupClient()
    search_tasks = []
    for query in search_queries:
        search_tasks.append(
                client.async_search(
                    query,
                    depth,
                    output_type="searchResults",
                )
            )

    search_results = []
    for response in await asyncio.gather(*search_tasks):
        search_results.append(
            {
                "results": [
                    {"title": result.name, "url": result.url, "content": result.content}
                    for result in response.results
                ],
            }
        )

    return search_results

@traceable
async def data_crawler_search(search_queries, display: int = 2, include_google: bool = False, 
                             max_content_length: int = 1000, max_results: int = 5):
    """
    네이버 API와 웹 크롤링을 사용하여 검색을 수행합니다.
    필요한 경우 구글 뉴스 결과도 포함합니다.
    
    Args:
        search_queries (List[str]): 처리할 검색 쿼리 목록
        display (int, optional): 각 소스별 검색 결과 개수. 기본값은 2.
        include_google (bool, optional): 구글 뉴스 데이터 포함 여부. 기본값은 False.
        max_content_length (int, optional): 최대 콘텐츠 길이. 기본값은 1000자.
        max_results (int, optional): 모든 소스에서 반환할 최대 결과 개수. 기본값은 5.
        
    Returns:
        List[dict]: 네이버(및 선택적으로 구글) 검색 결과 목록
    """
    crawler = NaverCrawler()
    
    search_docs = []
    
    for i, query in enumerate(search_queries):
        try:
            # 재시도 로직 추가 (최대 3번 시도)
            retry_count = 0
            max_retries = 3
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    # 추가 딜레이 - 첫 쿼리는 딜레이 없이, 이후 쿼리는 2-7초 딜레이
                    if i > 0 or retry_count > 0:
                        await asyncio.sleep(random.uniform(2.0, 7.0))
                    
                    # max_total_results 매개변수 추가
                    results = await crawler.crawl_all(query, display, include_google, max_total_results=max_results)
                    success = True
                except Exception as e:
                    retry_count += 1
                    print(f"네이버 검색 쿼리 '{query}' 처리 중 오류 발생 (시도 {retry_count}/{max_retries}): {str(e)}")
                    if retry_count >= max_retries:
                        raise
                    # 재시도 전 딜레이 증가
                    await asyncio.sleep(random.uniform(3.0, 10.0))
            
            # 성공한 경우에만 결과 처리
            if success:
                # 모든 소스의 결과를 합칩니다
                all_results = []
                
                # 최대 결과 개수 카운터
                result_count = 0
                
                # 뉴스 결과 처리
                for item in results.get('news', []):
                    if result_count >= max_results:
                        break
                    
                    # 콘텐츠 길이 제한
                    content = item.get('content', '')
                    if len(content) > max_content_length:
                        content = content[:max_content_length] + "... [잘림]"
                    
                    all_results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'content': item.get('description', ''),
                        'score': 1.0,  # 기본 점수
                        'raw_content': content
                    })
                    result_count += 1
                
                # 백과사전 결과 처리
                for item in results.get('encyc', []):
                    if result_count >= max_results:
                        break
                    
                    # 콘텐츠 길이 제한
                    content = item.get('content', '')
                    if len(content) > max_content_length:
                        content = content[:max_content_length] + "... [잘림]"
                    
                    all_results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'content': item.get('description', ''),
                        'score': 1.0,  # 기본 점수
                        'raw_content': content
                    })
                    result_count += 1
                
                # 지식인 결과 처리
                for item in results.get('kin', []):
                    if result_count >= max_results:
                        break
                    
                    # 콘텐츠 길이 제한
                    content = item.get('content', '')
                    if len(content) > max_content_length:
                        content = content[:max_content_length] + "... [잘림]"
                    
                    all_results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'content': item.get('description', ''),
                        'score': 1.0,  # 기본 점수
                        'raw_content': content
                    })
                    result_count += 1
                    
                # 구글 뉴스 결과 처리
                if include_google and 'google_news' in results:
                    for item in results.get('google_news', []):
                        if result_count >= max_results:
                            break
                        
                        # 콘텐츠 길이 제한
                        content = item.get('content', '')
                        if len(content) > max_content_length:
                            content = content[:max_content_length] + "... [잘림]"
                        
                        all_results.append({
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'content': '',  # 구글 뉴스는 description이 없을 수 있음
                            'score': 1.0,  # 기본 점수
                            'raw_content': content
                        })
                        result_count += 1
                
                # 검색 결과 추가
                search_docs.append({
                    'query': query,
                    'follow_up_questions': None,
                    'answer': None,
                    'images': [],
                    'results': all_results
                })
            
        except Exception as e:
            # 최종 오류 기록 및 빈 결과 반환
            print(f"네이버 검색 쿼리 '{query}' 처리 실패: {str(e)}")
            search_docs.append({
                'query': query,
                'follow_up_questions': None,
                'answer': None,
                'images': [],
                'results': [],
                'error': str(e)
            })
    
    return search_docs

async def select_and_execute_search(search_api: str, query_list: list[str], params_to_pass: dict) -> str:
    """Select and execute the appropriate search API.
    
    Args:
        search_api: Name of the search API to use
        query_list: List of search queries to execute
        params_to_pass: Parameters to pass to the search API
        
    Returns:
        Formatted string containing search results
        
    Raises:
        ValueError: If an unsupported search API is specified
    """
    if search_api == "tavily":
        search_results = await tavily_search_async(query_list, **params_to_pass)
        return deduplicate_and_format_sources(search_results, max_tokens_per_source=4000, include_raw_content=False)
    elif search_api == "perplexity":
        search_results = perplexity_search(query_list, **params_to_pass)
        return deduplicate_and_format_sources(search_results, max_tokens_per_source=4000)
    elif search_api == "exa":
        search_results = await exa_search(query_list, **params_to_pass)
        return deduplicate_and_format_sources(search_results, max_tokens_per_source=4000)
    elif search_api == "arxiv":
        search_results = await arxiv_search_async(query_list, **params_to_pass)
        return deduplicate_and_format_sources(search_results, max_tokens_per_source=4000)
    elif search_api == "pubmed":
        search_results = await pubmed_search_async(query_list, **params_to_pass)
        return deduplicate_and_format_sources(search_results, max_tokens_per_source=4000)
    elif search_api == "linkup":
        search_results = await linkup_search(query_list, **params_to_pass)
        return deduplicate_and_format_sources(search_results, max_tokens_per_source=4000)
    elif search_api == "data_crawler":  # 새로운 검색 API 추가
        search_results = await data_crawler_search(query_list, **params_to_pass)
        return deduplicate_and_format_sources(search_results, max_tokens_per_source=4000)
    else:
        raise ValueError(f"Unsupported search API: {search_api}")

async def fetch_contents_from_search_results(search_results: Dict[str, Any], max_items: int = 5) -> List[Dict[str, str]]:
    """
    네이버 검색 결과에서 각 링크의 내용을 병렬로 추출합니다.
    
    Args:
        search_results (Dict[str, Any]): naver_search 함수의 결과
        max_items (int, optional): 처리할 최대 항목 수. 기본값은 5.
        
    Returns:
        List[Dict[str, str]]: 각 URL에서 추출한 콘텐츠 목록
        
    Example:
        ```python
        search_results = naver_search("골절로 인한 통증 치료 방법", "kin")
        contents = await fetch_contents_from_search_results(search_results)
        for content in contents:
            print(f"제목: {content['title']}")
            print(f"내용: {content['content'][:100]}...")
        ```
    """
    try:
        import asyncio
        import aiohttp
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("aiohttp와 beautifulsoup4 패키지를 설치해야 합니다. pip install aiohttp beautifulsoup4")
    
    items = search_results.get('items', [])
    if not items:
        return []
    
    # 처리할 항목 수 제한
    items = items[:max_items]
    
    async def fetch_content(item):
        url = item.get('link', '')
        if not url:
            return {'url': '', 'title': item.get('title', ''), 'content': '', 'error': '링크가 없습니다.'}
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
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
                    
                    # 네이버 뉴스의 경우
                    elif 'news.naver.com' in url:
                        title_element = soup.select_one('#title_area') or soup.select_one('.media_end_head_headline')
                        content_element = soup.select_one('#newsct_article') or soup.select_one('#dic_area')
                        
                        if title_element:
                            content['title'] = title_element.get_text(strip=True)
                        
                        if content_element:
                            content['content'] = content_element.get_text(strip=True)
                    
                    # 네이버 블로그의 경우
                    elif 'blog.naver.com' in url:
                        title_element = soup.select_one('.se-title-text')
                        content_element = soup.select_one('.se-main-container')
                        
                        if title_element:
                            content['title'] = title_element.get_text(strip=True)
                        
                        if content_element:
                            content['content'] = content_element.get_text(strip=True)
                    
                    # 네이버 용어사전의 경우
                    elif 'terms.naver.com' in url:
                        title_element = soup.select_one('.headword') or soup.select_one('.word_title')
                        content_element = soup.select_one('#size_ct') or soup.select_one('.detail_area')
                        
                        if title_element:
                            content['title'] = title_element.get_text(strip=True)
                        
                        if content_element:
                            content['content'] = content_element.get_text(strip=True)
                    
                    # 기타 일반 웹페이지의 경우
                    else:
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
                    
                    # 내용이 없으면 에러 메시지 추가
                    if not content['content']:
                        content['error'] = '내용을 추출할 수 없습니다. 페이지 구조가 변경되었거나 접근이 제한된 페이지일 수 있습니다.'
                    
                    return content
        
        except Exception as e:
            return {'url': url, 'title': item.get('title', ''), 'content': '', 'error': f'오류: {str(e)}'}
    
    # 모든 항목에 대해 병렬로 내용 추출
    tasks = [fetch_content(item) for item in items]
    contents = await asyncio.gather(*tasks)
    
    return contents

def fetch_contents_from_search_results_sync(search_results: Dict[str, Any], max_items: int = 5) -> List[Dict[str, str]]:
    """
    fetch_contents_from_search_results의 동기 버전입니다.
    
    Args:
        search_results (Dict[str, Any]): naver_search 함수의 결과
        max_items (int, optional): 처리할 최대 항목 수. 기본값은 5.
        
    Returns:
        List[Dict[str, str]]: 각 URL에서 추출한 콘텐츠 목록
        
    Example:
        ```python
        search_results = naver_search("골절로 인한 통증 치료 방법", "kin")
        contents = fetch_contents_from_search_results_sync(search_results)
        for content in contents:
            print(f"제목: {content['title']}")
            print(f"내용: {content['content'][:100]}...")
        ```
    """
    try:
        import asyncio
    except ImportError:
        raise ImportError("asyncio 패키지를 설치해야 합니다.")
    
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
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(fetch_contents_from_search_results(search_results, max_items))
    else:
        # 이벤트 루프가 실행 중이 아닌 경우
        try:
            return asyncio.run(fetch_contents_from_search_results(search_results, max_items))
        except RuntimeError:
            # asyncio.run()이 실패하면 직접 실행
            return loop.run_until_complete(fetch_contents_from_search_results(search_results, max_items))