# src/vector_store.py
"""
向量数据库模块
使用ChromaDB存储和检索向量
"""

import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
import os
import json
from datetime import datetime


class VectorStore:
    """向量数据库管理器"""
    
    def __init__(self, collection_name: str = "documents", persist_dir: str = "./chroma_db"):
        """
        初始化向量数据库
        
        参数:
            collection_name: 集合名称
            persist_dir: 数据持久化目录
        """
        
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        
        # 确保目录存在
        os.makedirs(persist_dir, exist_ok=True)
        
        # 创建ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,  # 关闭匿名遥测
                allow_reset=True
            )
        )
        
        # 获取或创建集合
        self.collection = self._get_or_create_collection()
        
        print(f"✅ 向量数据库初始化完成")
        print(f"   集合: {collection_name}")
        print(f"   存储路径: {persist_dir}")
    
    def _get_or_create_collection(self):
        """获取或创建集合"""
        try:
            # 尝试获取现有集合
            collection = self.client.get_collection(self.collection_name)
            print(f"   加载现有集合: {self.collection_name}")
            return collection
        except:
            # 创建新集合
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )
            print(f"   创建新集合: {self.collection_name}")
            return collection
    
    def add_documents(
        self, 
        texts: List[str], 
        vectors: List[List[float]], 
        metadatas: List[Dict] = None,
        ids: List[str] = None
    ) -> Dict:
        """
        添加文档到向量数据库
        
        参数:
            texts: 文本列表
            vectors: 向量列表
            metadatas: 元数据列表
            ids: 文档ID列表（不提供则自动生成）
            
        返回:
            添加结果统计
        """
        if not texts or not vectors:
            return {"success": False, "error": "文本或向量为空"}
        
        if len(texts) != len(vectors):
            return {"success": False, "error": f"文本数({len(texts)})和向量数({len(vectors)})不匹配"}
        
        # 生成ID
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # 准备元数据
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        elif len(metadatas) != len(texts):
            metadatas = [{} for _ in range(len(texts))]
        
        # 添加时间戳
        for i, meta in enumerate(metadatas):
            if meta is None:
                meta = {}
            meta["added_at"] = datetime.now().isoformat()
            metadatas[i] = meta
        
        try:
            # 添加到集合
            self.collection.add(
                embeddings=vectors,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "count": len(texts),
                "collection": self.collection_name
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_chunks(
        self, 
        chunks, 
        vectors: List[List[float]]
    ) -> Dict:
        """
        添加文本块到向量数据库
        
        参数:
            chunks: TextChunk 对象列表
            vectors: 对应的向量列表
            
        返回:
            添加结果统计
        """
        texts = []
        metadatas = []
        
        for chunk in chunks:
            texts.append(chunk.text)
            
            metadata = {
                "chunk_id": chunk.chunk_id,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "char_count": len(chunk.text),
            }
            
            # 添加分块元数据
            if hasattr(chunk, 'metadata') and chunk.metadata:
                metadata.update(chunk.metadata)
            
            metadatas.append(metadata)
        
        return self.add_documents(texts, vectors, metadatas)
    
    def search(
        self, 
        query_vector: List[float], 
        n_results: int = 5
    ) -> List[Dict]:
        """
        搜索相似文档
        
        参数:
            query_vector: 查询向量
            n_results: 返回结果数量
            
        返回:
            搜索结果列表
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None,
                        "score": 1 - (results['distances'][0][i] if results['distances'] else 0)  # 相似度分数
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
    
    def search_by_text(
        self, 
        query_text: str, 
        embedder,  # 需要向量化器
        n_results: int = 5
    ) -> List[Dict]:
        """
        用文本进行搜索（内部会向量化）
        
        参数:
            query_text: 查询文本
            embedder: 向量化器实例
            n_results: 返回结果数量
            
        返回:
            搜索结果列表
        """
        # 向量化查询文本
        query_vector = embedder.embed_text(query_text).tolist()
        
        # 搜索
        return self.search(query_vector, n_results)
    
    def get_collection_info(self) -> Dict:
        """获取集合信息"""
        try:
            count = self.collection.count()
            return {
                "collection": self.collection_name,
                "count": count,
                "path": self.persist_dir
            }
        except:
            return {"collection": self.collection_name, "count": 0}
    
    def delete_collection(self) -> bool:
        """删除当前集合"""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"✅ 已删除集合: {self.collection_name}")
            return True
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False
    
    def reset(self) -> bool:
        """重置向量数据库"""
        try:
            self.client.reset()
            print("✅ 向量数据库已重置")
            return True
        except Exception as e:
            print(f"❌ 重置失败: {e}")
            return False


# 测试函数
def test_vector_store():
    """测试向量数据库"""
    print("🧪 测试向量数据库")
    print("=" * 60)
    
    # 创建向量数据库
    vector_store = VectorStore(collection_name="test_docs")
    
    # 测试数据
    texts = [
        "机器学习是人工智能的一个分支",
        "深度学习是机器学习的一种方法",
        "Python是一种流行的编程语言",
        "向量数据库用于存储和检索向量"
    ]
    
    # 模拟向量（实际使用时需要真实向量）
    vectors = [
        [0.1] * 384,  # 384维向量
        [0.2] * 384,
        [0.3] * 384,
        [0.4] * 384
    ]
    
    metadatas = [
        {"source": "test", "type": "definition"},
        {"source": "test", "type": "definition"},
        {"source": "test", "type": "language"},
        {"source": "test", "type": "database"}
    ]
    
    # 添加文档
    print("\n1. 添加文档到向量数据库...")
    result = vector_store.add_documents(texts, vectors, metadatas)
    print(f"   结果: {result}")
    
    # 获取集合信息
    print("\n2. 获取集合信息...")
    info = vector_store.get_collection_info()
    print(f"   信息: {info}")
    
    # 搜索测试
    print("\n3. 搜索测试...")
    query_vector = [0.15] * 384  # 接近第一个文档
    results = vector_store.search(query_vector, n_results=2)
    
    print(f"   搜索结果 ({len(results)} 个):")
    for i, r in enumerate(results):
        print(f"     结果 {i+1}: 相似度={r['score']:.3f}")
        print(f"        文本: {r['text'][:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ 向量数据库测试完成")


if __name__ == "__main__":
    test_vector_store()