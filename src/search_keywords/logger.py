# logger.py

# 전역 로거 인스턴스를 저장할 변수
_logger = None

def get_logger():
    """전역 로거 인스턴스 반환"""
    return _logger

def set_logger(logger):
    """전역 로거 인스턴스 설정"""
    global _logger
    _logger = logger

def log(message):
    """로그 메시지 출력"""
    logger = get_logger()
    if logger:
        logger(message)
    else:
        print(message) 