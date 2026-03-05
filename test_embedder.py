# test_embedder.py
from src.embedder import TextEmbedder

# 测试函数
def test_embedder():
    """测试向量化器"""
    print("🧪 测试文本向量化器")
    print("=" * 60)
    
    # 创建向量化器
    embedder = TextEmbedder()
    
    # 测试文本
    test_texts = [
        "什么是TCP协议？",
        "TCP是传输控制协议",
        "今天天气真好",
        "我喜欢编程"
    ]
    
    print("测试文本:")
    for i, text in enumerate(test_texts):
        print(f"  {i+1}. {text}")
    
    print("\n向量化结果:")
    
    # 单个文本向量化
    print("\n1. 单个文本向量化:")
    vector = embedder.embed_text(test_texts[0])
    info = embedder.get_vector_info(vector)
    print(f"   向量形状: {info['shape']}")
    print(f"   向量范围: [{info['min']:.3f}, {info['max']:.3f}]")
    print(f"   前5个值: {info['sample']}")
    
    # 批量向量化
    print("\n2. 批量向量化:")
    vectors = embedder.embed_batch(test_texts)
    print(f"   批量形状: {vectors.shape}")
    print(f"   处理了 {len(test_texts)} 个文本")
    
    # 计算相似度
    print("\n3. 计算相似度:")
    from sklearn.metrics.pairwise import cosine_similarity
    
    # 计算第一个文本与其他文本的相似度
    similarities = cosine_similarity([vectors[0]], vectors[1:])[0]
    
    for i, (text, sim) in enumerate(zip(test_texts[1:], similarities)):
        print(f"   '{test_texts[0]}' 与 '{text}' 的相似度: {sim:.3f}")
    
    print("\n" + "=" * 60)
    print("✅ 向量化测试完成")

if __name__ == "__main__":
    test_embedder()