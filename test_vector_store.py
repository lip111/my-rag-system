# test_vector_store.py
"""
测试向量数据库与真实向量
"""

import sys
import os
sys.path.append('.')
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

def test_with_real_embeddings():
    """使用真实向量测试"""
    print("🧪 测试向量数据库（真实向量）")
    print("=" * 60)
    
    try:
        from src.embedder import TextEmbedder
        from src.vector_store import VectorStore
        
        # 1. 创建向量化器
        print("1. 初始化向量化器...")
        embedder = TextEmbedder()
        embedder.load_model()
        
        # 2. 创建向量数据库
        print("2. 初始化向量数据库...")
        vector_store = VectorStore(collection_name="test_real")
        
        # 3. 准备测试数据
        test_texts = [
            "机器学习是人工智能的重要分支",
            "深度学习使用神经网络进行特征学习",
            "Python是数据科学和机器学习的主要语言",
            "向量数据库可以高效存储和检索向量",
            "自然语言处理是AI的重要应用领域"
        ]
        
        # 4. 向量化文本
        print("3. 向量化文本...")
        vectors = embedder.embed_batch(test_texts)
        vectors_list = [v.tolist() for v in vectors]
        
        # 5. 添加到向量数据库
        print("4. 添加到向量数据库...")
        result = vector_store.add_documents(
            texts=test_texts,
            vectors=vectors_list,
            metadatas=[{"index": i} for i in range(len(test_texts))]
        )
        
        print(f"   添加结果: {result}")
        
        # 6. 搜索测试
        print("\n5. 搜索测试...")
        query_text = "什么是机器学习？"
        print(f"   查询: '{query_text}'")
        
        # 向量化查询
        query_vector = embedder.embed_text(query_text).tolist()
        
        # 搜索
        results = vector_store.search(query_vector, n_results=3)
        
        print(f"   搜索结果:")
        for i, r in enumerate(results):
            print(f"     {i+1}. 相似度: {r['score']:.3f}")
            print(f"        文本: {r['text'][:50]}...")
        
        # 7. 清理
        print("\n6. 清理测试数据...")
        vector_store.delete_collection()
        
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_with_real_embeddings()