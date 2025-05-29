import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pickle
import hashlib

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import fitz  # PyMuPDF for image extraction
from PIL import Image
import io

# OpenAI for embeddings
from openai import OpenAI

# ChromaDB for vector storage
import chromadb
from chromadb.config import Settings

# For text processing
import re
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """
    운동 및 건강 관련 전문 문서를 위한 Vector Database 클래스
    텍스트와 이미지 임베딩을 모두 지원
    """
    
    def __init__(self, 
                 collection_name: str = "fitness_knowledge_base",
                 persist_directory: str = "./chroma_db",
                 openai_api_key: Optional[str] = None):
        """
        VectorStore 초기화
        
        Args:
            collection_name: ChromaDB 컬렉션 이름
            persist_directory: 데이터베이스 저장 경로
            openai_api_key: OpenAI API 키
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # OpenAI 클라이언트 설정
        self.openai_client = OpenAI(
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # ChromaDB 클라이언트 설정
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        
        # 컬렉션 생성 또는 가져오기
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"기존 컬렉션 '{collection_name}' 로드됨")
        except:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Fitness and health knowledge base"}
            )
            logger.info(f"새 컬렉션 '{collection_name}' 생성됨")
        
        # Sentence Transformer 모델 (다국어 지원)
        self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # 메타데이터 저장소 초기화
        self.metadata_store = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """저장된 메타데이터 로드"""
        metadata_path = Path(self.persist_directory) / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata_store = json.load(f)
                logger.info("메타데이터 로드 완료")
            except Exception as e:
                logger.warning(f"메타데이터 로드 실패: {e}")
    
    def _save_metadata(self):
        """메타데이터 저장"""
        metadata_path = Path(self.persist_directory) / "metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_store, f, ensure_ascii=False, indent=2)
            logger.info("메타데이터 저장 완료")
        except Exception as e:
            logger.error(f"메타데이터 저장 실패: {e}")
    
    def get_text_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """
        텍스트 임베딩 생성 (OpenAI)
        
        Args:
            text: 임베딩할 텍스트
            model: 사용할 임베딩 모델
            
        Returns:
            임베딩 벡터
        """
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI 임베딩 실패, Sentence Transformer 사용: {e}")
            # Fallback to Sentence Transformer
            return self.sentence_model.encode(text).tolist()
    
    def get_image_embedding(self, image_path: str) -> List[float]:
        """
        이미지 임베딩 생성 (CLIP 모델 사용)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            이미지 임베딩 벡터
        """
        try:
            # OpenAI CLIP API 사용 (향후 지원 시)
            # 현재는 Sentence Transformer의 CLIP 모델 사용
            from sentence_transformers import SentenceTransformer
            
            clip_model = SentenceTransformer('clip-ViT-B-32')
            
            # 이미지 로드 및 전처리
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 이미지 임베딩 생성
            embedding = clip_model.encode(image)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"이미지 임베딩 생성 실패: {e}")
            # 기본 임베딩 반환 (1536 차원)
            return [0.0] * 1536
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDF에서 텍스트 추출 및 청크 분할
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            텍스트 청크 리스트
        """
        chunks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    if text.strip():
                        # 텍스트 전처리
                        text = self._preprocess_text(text)
                        
                        # 청크 분할 (1000자 단위)
                        text_chunks = self._split_text(text, chunk_size=1000, overlap=200)
                        
                        for i, chunk in enumerate(text_chunks):
                            chunks.append({
                                'content': chunk,
                                'source': pdf_path,
                                'page': page_num + 1,
                                'chunk_id': f"{Path(pdf_path).stem}_p{page_num + 1}_c{i + 1}",
                                'type': 'text'
                            })
        
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
        
        return chunks
    def _get_file_hash(self, file_path: str) -> str:
        """파일의 해시값(MD5) 반환"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


    def extract_images_from_pdf(self, pdf_path: str, output_dir: str = "./extracted_images") -> List[Dict[str, Any]]:
        """
        PDF에서 이미지 추출
        
        Args:
            pdf_path: PDF 파일 경로
            output_dir: 이미지 저장 디렉토리
            
        Returns:
            이미지 정보 리스트
        """
        images = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_document, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_filename = f"{Path(pdf_path).stem}_p{page_num + 1}_img{img_index + 1}.png"
                        img_path = output_path / img_filename
                        
                        pix.save(str(img_path))
                        
                        images.append({
                            'image_path': str(img_path),
                            'source': pdf_path,
                            'page': page_num + 1,
                            'image_id': f"{Path(pdf_path).stem}_p{page_num + 1}_img{img_index + 1}",
                            'type': 'image'
                        })
                    
                    pix = None
            
            pdf_document.close()
        
        except Exception as e:
            logger.error(f"PDF 이미지 추출 실패: {e}")
        
        return images
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        # 특수 문자 정리
        text = re.sub(r'[^\w\s가-힣.,!?-]', '', text)
        return text.strip()
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """텍스트를 청크로 분할"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                # 문장 경계에서 자르기
                for punct in ['. ', '.\n', '? ', '! ', '.\n\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + len(punct)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
            if start >= len(text):
                break
        
        return chunks
    
    def add_documents(self, pdf_paths: List[str], extract_images: bool = True) -> int:
        total_added = 0
        """
        PDF 문서들을 벡터 데이터베이스에 추가
        
        Args:
            pdf_paths: PDF 파일 경로 리스트
            extract_images: 이미지 추출 여부
            
        Returns:
            추가된 문서 수
        """
        total_added = 0
        
        for pdf_path in pdf_paths:
            if not Path(pdf_path).exists():
                logger.warning(f"파일이 존재하지 않음: {pdf_path}")
                continue
            
            file_hash = self._get_file_hash(pdf_path)
            prev_meta = self.metadata_store.get(pdf_path, {})
            if prev_meta.get('file_hash') == file_hash and prev_meta.get('processed', False):
                logger.info(f"이미 처리된 파일(변경 없음): {pdf_path} -> 건너뜀")
                continue    

            logger.info(f"문서 처리 중: {pdf_path}")
            
            # 텍스트 추출 및 임베딩
            text_chunks = self.extract_text_from_pdf(pdf_path)
            
            for chunk in text_chunks:
                try:
                    embedding = self.get_text_embedding(chunk['content'])
                    
                    self.collection.add(
                        embeddings=[embedding],
                        documents=[chunk['content']],
                        metadatas=[{
                            'source': chunk['source'],
                            'page': chunk['page'],
                            'chunk_id': chunk['chunk_id'],
                            'type': 'text'
                        }],
                        ids=[chunk['chunk_id']]
                    )
                    
                    total_added += 1
                    
                except Exception as e:
                    logger.error(f"텍스트 청크 추가 실패: {e}")
            
            # 이미지 추출 및 임베딩 (선택적)
            if extract_images:
                images = self.extract_images_from_pdf(pdf_path)
                
                for img_info in images:
                    try:
                        embedding = self.get_image_embedding(img_info['image_path'])
                        
                        # 이미지는 경로만 저장
                        self.collection.add(
                            embeddings=[embedding],
                            documents=[f"Image: {img_info['image_path']}"],
                            metadatas=[{
                                'source': img_info['source'],
                                'page': img_info['page'],
                                'image_id': img_info['image_id'],
                                'image_path': img_info['image_path'],
                                'type': 'image'
                            }],
                            ids=[img_info['image_id']]
                        )
                        
                        total_added += 1
                        
                    except Exception as e:
                        logger.error(f"이미지 추가 실패: {e}")
            
            # 메타데이터 업데이트
            self.metadata_store[pdf_path] = {
                'processed': True,
                'file_hash': file_hash,
                'text_chunks': len(text_chunks),
                'images': len(images) if extract_images else 0,
                'timestamp': pd.Timestamp.now().isoformat()
            }
        
        self._save_metadata()
        logger.info(f"총 {total_added}개 문서 추가 완료")
        return total_added
    
    def search(self, 
               query: str, 
               n_results: int = 5, 
               filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        유사 문서 검색
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            filter_type: 필터 타입 ('text', 'image', None)
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.get_text_embedding(query)
            
            # 필터 설정
            where_filter = None
            if filter_type:
                where_filter = {"type": filter_type}
            
            # 검색 실행
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter
            )
            
            # 결과 포맷팅
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"검색 실패: {e}")
            return []
    
    def get_relevant_context(self, 
                           query: str, 
                           max_context_length: int = 3000) -> str:
        """
        쿼리와 관련된 컨텍스트 텍스트 생성
        
        Args:
            query: 검색 쿼리
            max_context_length: 최대 컨텍스트 길이
            
        Returns:
            관련 컨텍스트 텍스트
        """
        # 텍스트 문서만 검색
        results = self.search(query, n_results=10, filter_type='text')
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content']
            source = result['metadata'].get('source', 'Unknown')
            page = result['metadata'].get('page', '')
            
            # 컨텍스트 헤더 추가
            header = f"\n[출처: {Path(source).name}, 페이지: {page}]\n"
            full_content = header + content
            
            if current_length + len(full_content) <= max_context_length:
                context_parts.append(full_content)
                current_length += len(full_content)
            else:
                # 남은 공간에 맞춰 자르기
                remaining_space = max_context_length - current_length - len(header)
                if remaining_space > 100:  # 최소 100자는 남겨두기
                    truncated_content = content[:remaining_space] + "..."
                    context_parts.append(header + truncated_content)
                break
        
        return '\n'.join(context_parts)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보 반환"""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.collection_name,
                'metadata_files': len(self.metadata_store)
            }
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {e}")
            return {}
    
    def clear_collection(self):
        """컬렉션 초기화"""
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Fitness and health knowledge base"}
            )
            self.metadata_store = {}
            self._save_metadata()
            logger.info("컬렉션 초기화 완료")
        except Exception as e:
            logger.error(f"컬렉션 초기화 실패: {e}")


# 사용 예시 및 테스트 함수
def main():
    """테스트 및 사용 예시"""
    # VectorStore 인스턴스 생성
    vector_store = VectorStore(
        collection_name="fitness_knowledge_base",
        persist_directory="./chroma_db"
    )
    
    # 문서 추가 예시
    # pdf_files = ["./fitness_research.pdf", "./nutrition_guide.pdf"]
    # vector_store.add_documents(pdf_files, extract_images=True)
    
    # 검색 예시
    query = "근력 운동의 효과와 방법"
    results = vector_store.search(query, n_results=5)
    
    print("검색 결과:")
    for result in results:
        print(f"- {result['content'][:100]}...")
        print(f"  출처: {result['metadata']['source']}")
        print()
    
    # 컨텍스트 생성 예시
    context = vector_store.get_relevant_context(query)
    print("관련 컨텍스트:")
    print(context[:500] + "...")
    
    # 통계 정보
    stats = vector_store.get_collection_stats()
    print(f"컬렉션 통계: {stats}")


if __name__ == "__main__":
    main()