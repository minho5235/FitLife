"""
RAG 모듈
"""
# [수정] load_knowledge_from_json을 삭제했습니다.
from .knowledge_base import KnowledgeBase
from .chain import FitLifeRAG

__all__ = ["KnowledgeBase", "FitLifeRAG"]