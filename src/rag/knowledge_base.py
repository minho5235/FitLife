"""
RAG 모듈 - 지식베이스 구축 및 검색 (HuggingFace 무료 임베딩 버전)
"""
import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional
import json
from pathlib import Path

from src.config import (
    CHROMA_PERSIST_DIR, 
    COLLECTION_NAME,
    RAG_TOP_K
)


class KnowledgeBase:
    """건강 지식베이스 관리 클래스"""
    
    def __init__(self):
        # 임베딩 모델 초기화 (HuggingFace - 무료, 로컬)
        print("   임베딩 모델 로딩 중... (처음엔 다운로드로 시간이 걸릴 수 있어요)")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("   임베딩 모델 로딩 완료!")
        
        # ChromaDB 초기화
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        
        # 컬렉션 생성 또는 가져오기
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "FitLife AI 건강 지식베이스"}
        )
        
        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "]
        )
    
    def add_documents(self, documents: List[Dict], category: str):
        """
        문서 추가
        
        Args:
            documents: [{"title": "...", "content": "...", "source": "..."}, ...]
            category: "food" | "exercise" | "guideline"
        """
        for i, doc in enumerate(documents):
            # 텍스트 분할
            chunks = self.text_splitter.split_text(doc["content"])
            
            for j, chunk in enumerate(chunks):
                # 임베딩 생성
                embedding = self.embeddings.embed_query(chunk)
                
                # ChromaDB에 추가
                doc_id = f"{category}_{i}_{j}"
                self.collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "title": doc.get("title", ""),
                        "category": category,
                        "source": doc.get("source", ""),
                        "chunk_index": j
                    }]
                )
        
        print(f"✅ {len(documents)}개 문서 추가 완료 (카테고리: {category})")
    
    def search(self, query: str, top_k: int = RAG_TOP_K, category: Optional[str] = None) -> List[Dict]:
        """
        유사 문서 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 수
            category: 카테고리 필터 (선택)
            
        Returns:
            검색 결과 리스트
        """
        # 쿼리 임베딩
        query_embedding = self.embeddings.embed_query(query)
        
        # 검색 조건
        where_filter = {"category": category} if category else None
        
        # 검색 실행
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # 결과 정리
        search_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                search_results.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i]  # 거리를 유사도로 변환
                })
        
        return search_results
    
    def get_stats(self) -> Dict:
        """지식베이스 통계"""
        return {
            "total_documents": self.collection.count(),
            "collection_name": COLLECTION_NAME
        }
    
    def clear(self):
        """지식베이스 초기화"""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "FitLife AI 건강 지식베이스"}
        )
        print("🗑️ 지식베이스 초기화 완료")


def load_knowledge_from_json(filepath: str) -> List[Dict]:
    """JSON 파일에서 지식 로드"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# 테스트용
if __name__ == "__main__":
    kb = KnowledgeBase()
    print(f"📊 지식베이스 상태: {kb.get_stats()}")