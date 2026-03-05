# vector_concept.py
"""
向量化概念演示
不实际加载模型，只理解概念
"""

print("🧠 向量化概念演示")
print("=" * 60)

# 概念1：文本如何变成向量
print("\n1. 文本 → 向量 的转换")
print("   输入: '什么是TCP协议'")
print("   输出: [0.1, 0.2, 0.3, ..., 0.9]  # 384个数字")
print("   维度: 384 (由模型决定)")

# 概念2：向量的用途
print("\n2. 向量的用途")
print("   - 相似度计算: 向量A 与 向量B 的距离")
print("   - 语义搜索: 找最相似的向量")
print("   - 聚类分析: 相似的向量聚在一起")

# 概念3：在你的项目中的位置
print("\n3. 在你的RAG系统中的位置")
print("   文档 → 分块 → 向量化 → 存储 → 检索 → 回答")
print("             ↑             ↑")
print("       你现在在这里  将要学习这里")

# 概念4：sentence-transformers库的作用
print("\n4. sentence-transformers 库")
print("   - 预训练模型: 已经学会了文本到向量的映射")
print("   - 支持中文: 有专门的中文模型")
print("   - 简单易用: model.encode('文本') → 向量")

print("\n" + "=" * 60)
print("✅ 向量化概念理解完成")
print("\n💡 下一步：实际用sentence-transformers将文本转换为向量")