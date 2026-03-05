# test_parser.py
import sys
import os

# 添加当前目录到Python路径
sys.path.append('.')

from src.document_parser import DocumentParser

def test_parser():
    """测试文档解析器"""
    print("🧪 测试文档解析器")
    print("=" * 60)
    
    parser = DocumentParser()
    
    # 1. 测试TXT文件解析
    print("\n1. 测试TXT文件解析...")
    
    # 创建测试TXT文件
    test_content = """这是一个测试文档
用于验证解析器功能

技术要点：
1. Python编程
2. 文档解析
3. 编码处理
4. 错误处理

示例配置：
interface GigabitEthernet0/1
  description "测试接口"
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30
"""
    
    with open("test_document.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    result = parser.parse_document("test_document.txt")
    
    if result['success']:
        print("✅ TXT解析成功！")
        print(f"   文件名: {result['file_name']}")
        print(f"   文件类型: {result['file_type']}")
        print(f"   文件大小: {result['file_size']} 字节")
        print(f"   字符数: {result['char_count']}")
        print(f"   编码: {result['metadata'].get('encoding', '未知')}")
        print(f"   内容预览: {result['content'][:100]}...")
    else:
        print(f"❌ TXT解析失败: {result['error']}")
    
    # 清理测试文件
    if os.path.exists("test_document.txt"):
        os.remove("test_document.txt")
    
    # 2. 测试文件验证功能
    print("\n2. 测试文件验证...")
    
    # 模拟上传的文件
    test_bytes = b"This is a test file content for validation."
    
    validation_result = parser.validate_file(
        file_bytes=test_bytes,
        file_name="test.txt",
        max_size_mb=10
    )
    
    if validation_result['valid']:
        print("✅ 文件验证通过")
        print(f"   文件类型: {validation_result['file_type']}")
        print(f"   文件大小: {validation_result['file_size_mb']:.2f} MB")
    else:
        print(f"❌ 文件验证失败: {validation_result['error']}")
    
    # 3. 测试不支持格式
    print("\n3. 测试不支持格式...")
    
    validation_result = parser.validate_file(
        file_bytes=test_bytes,
        file_name="test.zip",
        max_size_mb=10
    )
    
    if not validation_result['valid']:
        print(f"✅ 正确拒绝不支持格式: {validation_result['error']}")
    
    # 4. 测试大文件验证
    print("\n4. 测试大文件验证...")
    
    # 创建11MB的大文件数据
    large_file = b"x" * 11 * 1024 * 1024  # 11MB
    
    validation_result = parser.validate_file(
        file_bytes=large_file,
        file_name="large.txt",
        max_size_mb=10
    )
    
    if not validation_result['valid']:
        print(f"✅ 正确拒绝大文件: {validation_result['error']}")
    
    # 5. 测试PDF解析（如果系统有PDF库）
    print("\n5. 测试PDF解析能力...")
    try:
        import pdfplumber
        print("✅ PDF解析库已安装，可以解析PDF文件")
    except ImportError:
        print("⚠️ PDF解析库未安装，运行 'pip install pdfplumber' 安装")
    
    print("\n" + "=" * 60)
    print("✅ 文档解析器测试完成！")
    
    # 返回测试总结
    return {
        "txt_parsed": result['success'] if 'result' in locals() else False,
        "validation_works": validation_result.get('valid', False) if 'validation_result' in locals() else False
    }

if __name__ == "__main__":
    test_parser()