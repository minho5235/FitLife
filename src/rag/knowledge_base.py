"""
FitLife AI - KnowledgeBase (하이브리드 검색 엔진 탑재)
"""
import os
from typing import List, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_community.embeddings import HuggingFaceEmbeddings
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
                    "video_url": doc.get("video_url", ""),
                    "tags": doc.get("tags", [])  # [Update] 태그 필드 추가
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
        [하이브리드 검색 구현]
        벡터 유사도(Semantic) + 키워드 매칭(Lexical) 점수를 합산하여 재정렬합니다.
        """
        try:
            # 1. 벡터 검색 (의미 기반) - 넉넉하게 2배수(top_k * 2)를 가져옵니다.
            query_vector = self.embedding_model.embed_query(query)
            
            params = {
                "query_embedding": query_vector,
                "match_threshold": 0.1, 
                "match_count": top_k * 2 
            }
            
            response = self.supabase_client.rpc("match_documents", params).execute()
            
            # 2. 파이썬 레벨에서 하이브리드 리랭킹 (Reranking)
            raw_results = []
            query_tokens = set(query.split()) # 검색어 토큰화
            
            for item in response.data:
                # 카테고리 필터링
                meta = item.get("metadata", {})
                if category and meta.get("category") != category:
                    continue
                
                content = item.get("content", "")
                title = meta.get("title", "")
                vector_score = item['similarity']
                
                # [Hybrid Logic] 키워드 가산점 로직
                keyword_bonus = 0.0
                matched_count = 0
                
                for token in query_tokens:
                    if len(token) < 2: continue # 1글자는 무시
                    if token in title:
                        keyword_bonus += 0.05 # 제목에 있으면 큰 가산점
                        matched_count += 1
                    elif token in content:
                        keyword_bonus += 0.02 # 본문에 있으면 작은 가산점
                        matched_count += 1
                
                # 너무 과한 가산점 방지 (최대 0.15점 제한)
                final_score = vector_score + min(keyword_bonus, 0.15)
                
                doc = Document(page_content=content, metadata=meta)
                raw_results.append((doc, final_score))
            
            # 3. 최종 점수 기준 내림차순 정렬
            raw_results.sort(key=lambda x: x[1], reverse=True)
            
            return raw_results[:top_k]

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