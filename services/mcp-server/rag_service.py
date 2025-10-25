"""
Enterprise RAG Service
Handles document processing, vectorization, and semantic search
"""

import logging
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import PyPDF2
import docx
import io
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, qdrant_host: str = "qdrant", qdrant_port: int = 6333):
        """Initialize RAG service with embedding model and vector DB"""
        self.embedding_model = None
        self.qdrant_client = None
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.vector_size = 384  # all-MiniLM-L6-v2 dimension
        self.collection_name = "documents"

    async def initialize(self):
        """Lazy initialization of models"""
        if self.embedding_model is None:
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")

        if self.qdrant_client is None:
            logger.info(f"Connecting to Qdrant at {self.qdrant_host}:{self.qdrant_port}")
            self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)

            # Create collection if it doesn't exist
            try:
                self.qdrant_client.get_collection(self.collection_name)
                logger.info(f"Collection '{self.collection_name}' already exists")
            except:
                logger.info(f"Creating collection '{self.collection_name}'")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc_file = io.BytesIO(file_content)
            doc = docx.Document(doc_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            raise

    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extract text based on file type"""
        filename_lower = filename.lower()

        if filename_lower.endswith('.pdf'):
            return self.extract_text_from_pdf(file_content)
        elif filename_lower.endswith('.docx'):
            return self.extract_text_from_docx(file_content)
        elif filename_lower.endswith('.txt'):
            return file_content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {filename}")

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        await self.initialize()
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()

    async def process_document(
        self,
        doc_id: int,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None,
        chunk_size: int = 500
    ) -> int:
        """Process and store document with embeddings"""
        await self.initialize()

        # Chunk the document
        chunks = self.chunk_text(content, chunk_size=chunk_size)
        logger.info(f"Document {doc_id} split into {len(chunks)} chunks")

        # Generate embeddings for each chunk
        points = []
        for idx, chunk in enumerate(chunks):
            embedding = await self.generate_embedding(chunk)

            point_id = f"{doc_id}_{idx}"
            # Use hash to create a consistent numeric ID
            numeric_id = int(hashlib.md5(point_id.encode()).hexdigest()[:8], 16)

            point = PointStruct(
                id=numeric_id,
                vector=embedding,
                payload={
                    "doc_id": doc_id,
                    "chunk_id": idx,
                    "title": title,
                    "content": chunk,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat()
                }
            )
            points.append(point)

        # Store in Qdrant
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        logger.info(f"Stored {len(points)} vectors for document {doc_id}")
        return len(chunks)

    async def semantic_search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        await self.initialize()

        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Build filter if provided
        search_filter = None
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{key}",
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                search_filter = Filter(must=conditions)

        # Search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit * 2,  # Get more results to filter by score
            query_filter=search_filter
        )

        # Filter by score and format results
        results = []
        seen_docs = set()

        for hit in search_results:
            if hit.score < score_threshold:
                continue

            doc_id = hit.payload.get("doc_id")

            # Avoid duplicate documents in results
            if doc_id in seen_docs:
                continue
            seen_docs.add(doc_id)

            results.append({
                "doc_id": doc_id,
                "title": hit.payload.get("title"),
                "content": hit.payload.get("content"),
                "score": hit.score,
                "metadata": hit.payload.get("metadata", {}),
                "chunk_id": hit.payload.get("chunk_id")
            })

            if len(results) >= limit:
                break

        logger.info(f"Semantic search for '{query}' returned {len(results)} results")
        return results

    async def delete_document_vectors(self, doc_id: int):
        """Delete all vectors associated with a document"""
        await self.initialize()

        # Delete by filter
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )
        )

        logger.info(f"Deleted vectors for document {doc_id}")

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        await self.initialize()

        collection_info = self.qdrant_client.get_collection(self.collection_name)

        return {
            "collection_name": self.collection_name,
            "vectors_count": collection_info.vectors_count,
            "points_count": collection_info.points_count,
            "status": collection_info.status,
            "vector_size": self.vector_size,
            "distance": "cosine"
        }

# Global instance
rag_service = RAGService()
