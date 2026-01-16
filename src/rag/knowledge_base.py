"""
FitLife AI - KnowledgeBase (최신 라이브러리 호환 버전)
"""
import os
from typing import List, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_community.embeddings import HuggingFaceEmbeddings
# ★ [수정] 최신 LangChain 경로는 여기입니다!
from langchain_core.documents import Document

# 설정 파일 로드
import src.config as config

load_dotenv()

class KnowledgeBase:
    def __init__(self):
        # 1. Supabase 클라이언트 연결
        self.supabase_url = config.SUPABASE_URL
        self.supabase_key = config.SUPABASE_KEY
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("⚠️ Supabase 접속 정보가 없습니다. .env 파일을 확인하세요.")
            
        self.supabase_client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # 2. 임베딩 모델 로드
        print(f"🔌 임베딩 모델 로딩 중... ({config.EMBEDDING_MODEL_NAME})")
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ 임베딩 모델 로드 완료!")

    def add_documents(self, documents: List[dict], category: str = "general"):
        """
        [업로드용] 문서 리스트를 임베딩하여 Supabase에 저장합니다.
        """
        data_to_insert = []
        
        print(f"📦 데이터 임베딩 변환 중... ({len(documents)}개)")
        texts = [doc['content'] for doc in documents]
        embeddings = self.embedding_model.embed_documents(texts)
        
        for i, doc in enumerate(documents):
            data_to_insert.append({
                "content": doc['content'],
                "metadata": {
                    "title": doc['title'],
                    "source": doc.get("source", "unknown"),
                    "category": category,
                    "video_url": doc.get("video_url", "")
                },
                "embedding": embeddings[i]
            })
            
        try:
            self.supabase_client.table("documents").insert(data_to_insert).execute()
            print(f"✅ {len(data_to_insert)}개 문서 저장 완료!")
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")

    def search(self, query: str, top_k: int = 5, category: str = None) -> List[Tuple[Document, float]]:
        """
        [검색용] Supabase RPC 직접 호출 (버전 충돌 방지)
        """
        try:
            # 1. 질문을 벡터로 변환
            query_vector = self.embedding_model.embed_query(query)
            
            # 2. Supabase RPC 함수 호출
            params = {
                "query_embedding": query_vector,
                "match_threshold": 0.1, 
                "match_count": top_k
            }
            
            response = self.supabase_client.rpc("match_documents", params).execute()
            
            results = []
            for item in response.data:
                # 카테고리 필터링
                if category:
                    item_category = item.get("metadata", {}).get("category", "")
                    if item_category != category:
                        continue
                
                doc = Document(
                    page_content=item['content'],
                    metadata=item['metadata']
                )
                results.append((doc, item['similarity']))
                
            return results[:top_k]

        except Exception as e:
            print(f"⚠️ 검색 중 오류 발생: {e}")
            return []

    def clear(self):
        """데이터 초기화"""
        try:
            self.supabase_client.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            print("🗑️ 지식베이스 초기화 완료")
        except Exception as e:
            print(f"⚠️ 초기화 오류 (무시 가능): {e}")