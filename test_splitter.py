# test_splitter.py
import sys
sys.path.append('.')

from src.text_splitter import TextSplitter

def test_splitter():
    """测试文本分割器"""
    print("🧪 测试文本分割器")
    print("=" * 60)
    
    # 创建测试文本
    test_text = """这是一个测试文档。

它包含多个段落。

每个段落都有不同的内容。

这是第一个段落，内容比较简单。
这是第二个段落，内容稍微长一些，用于测试分割功能。
这是第三个段落，也用于测试。

技术文档通常包含代码片段：
def hello_world():
    print("Hello, World!")
    
以及配置信息：
server {
    listen 80;
    server_name example.com;
}
"""
    
    # 创建分割器
    splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
    
    # 分析文本
    print("1. 文本分析:")
    analysis = splitter.analyze_text(test_text)
    for key, value in analysis.items():
        print(f"   {key}: {value}")
    
    print("\n2. 按固定大小分割:")
    chunks = splitter.split_text(test_text, method="fixed_size")
    print(f"   分割成 {len(chunks)} 个块")
    for i, chunk in enumerate(chunks[:3]):  # 只显示前3个
        print(f"   块 {i}: 字符数={len(chunk.text)}, 起始={chunk.start_char}, 结束={chunk.end_char}")
        print(f"   内容: {chunk.text[:50]}...")
    
    print("\n3. 按段落分割:")
    chunks = splitter.split_text(test_text, method="paragraph")
    print(f"   分割成 {len(chunks)} 个块")
    for i, chunk in enumerate(chunks):
        print(f"   块 {i}: 段落数={chunk.metadata.get('paragraph_count', 1)}")
        print(f"   内容: {chunk.text[:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ 文本分割器测试完成！")

if __name__ == "__main__":
    test_splitter()