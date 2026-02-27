# app.py
import streamlit as st
import tempfile
import os
import time
from src.document_parser import DocumentParser

# 设置页面配置
st.set_page_config(
    page_title="parser",
    page_icon="📤",
    layout="wide"
)

# 初始化解析器
@st.cache_resource
def get_parser():
    return DocumentParser()

parser = get_parser()

# 应用标题
st.title("📤 文档上传与解析工具")
st.markdown("上传PDF或TXT格式的技术文档，解析并预览内容")

# 侧边栏 - 设置
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 文件大小限制
    max_size_mb = st.slider(
        "最大文件大小 (MB)",
        min_value=1,
        max_value=100,
        value=10,
        help="限制上传文件的最大大小"
    )
    
    # 显示选项
    show_raw = st.checkbox("显示原始内容", value=True)
    show_metadata = st.checkbox("显示元信息", value=True)
    
    st.divider()
    
    # 应用信息
    st.info("""
    ### 📋 支持格式
    - PDF (.pdf)
    - 文本 (.txt)
    
    ### ⚠️ 注意事项
    1. 确保文件编码正确
    2. PDF中的扫描图片无法提取文字
    3. 大文件可能需要更长时间解析
    """)

# 主区域
tab1, tab2 = st.tabs(["📤 上传解析", "📊 批量处理"])

with tab1:
    # 文件上传区域
    st.subheader("单文件上传")
    
    uploaded_file = st.file_uploader(
        "选择PDF或TXT文件",
        type=['pdf', 'txt'],
        help="支持PDF和TXT格式，最大{}MB".format(max_size_mb)
    )
    
    if uploaded_file is not None:
        # 文件信息展示
        print(f"[1] 用户选择了文件: {uploaded_file.name}")
        print(f"[2] 文件大小: {len(uploaded_file.getvalue())} 字节")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("文件名", uploaded_file.name)
        with col2:
            file_size = len(uploaded_file.getvalue())
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.2f} KB"
            else:
                size_str = f"{file_size/(1024 * 1024):.2f} MB"
            st.metric("文件大小", size_str)
        with col3:
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            st.metric("文件类型", file_ext.upper())
        
        # 验证文件
        validation = parser.validate_file(
            file_bytes=uploaded_file.getvalue(),
            file_name=uploaded_file.name,
            max_size_mb=max_size_mb
        )
        
        if not validation['valid']:
            st.error(f"❌ 文件验证失败: {validation['error']}")
        else:
            # 解析按钮
            if st.button("🚀 开始解析", type="primary", use_container_width=True):
                with st.spinner("正在解析文档，请稍候..."):
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=uploaded_file.name
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                        print(f"[3] 保存到临时文件: {tmp_path}")
                    
                    try:
                        # 添加进度条
                        progress_bar = st.progress(0)
                        
                        # 模拟解析进度
                        for i in range(100):
                            time.sleep(0.01)  # 稍微延迟，让进度条可见
                            progress_bar.progress(i + 1)
                        
                        # 解析文档
                        print(f"[4] 调用解析器: {parser.parse_document.__name__}")
                        result = parser.parse_document(tmp_path)
                        print(f"[5] 解析结果: success={result.get('success')}")
                        
                        if result['success']:
                            st.success("✅ 文档解析成功！")
                            
                            # 显示元信息
                            if show_metadata:
                                with st.expander("📊 文档元信息", expanded=True):
                                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                                    
                                    print(f"[6] 显示在界面: {result.get('char_count', 0)} 字符")
                                    with meta_col1:
                                        st.metric("字符数", result['char_count'])
                                        st.metric("文件大小", f"{result['metadata']['file_size_mb']} MB")
                                    
                                    with meta_col2:
                                        if 'page_count' in result['metadata']:
                                            st.metric("页数", result['metadata']['page_count'])
                                        if 'encoding' in result['metadata']:
                                            st.metric("编码", result['metadata']['encoding'])
                                        if 'total_lines' in result['metadata']:
                                            st.metric("总行数", result["metadata"]["total_lines"])
                                    
                                    with meta_col3:
                                        st.metric("解析时间", result['metadata']['parsed_at'])
                                        
                                        if 'has_tables' in result['metadata']:
                                            table_status = "是" if result['metadata']['has_tables'] else "否"
                                            st.metric("包含表格", table_status)
                                        if 'total_lines' in result['metadata']:
                                            st.metric("非空行", result["metadata"]["non_empty_lines"])
                            
                            # 显示文档内容
                            st.subheader("📄 文档内容")
                            
                            # 内容统计
                            col1, col2 = st.columns(2)
                            with col1:
                                if result['content']:
                                    lines = result['content'].count('\n') + 1
                                    st.metric("行数", lines)
                            with col2:
                                if result['content']:
                                    words = len(result['content'].split())
                                    st.metric("单词数", words)
                            
                            # 内容显示区域
                            if show_raw:
                                with st.expander("查看完整内容", expanded=True):
                                    # 显示前5000字符，避免页面卡顿
                                    if len(result['content']) > 5000:
                                        st.text_area(
                                            "文档内容（前5000字符）",
                                            result['content'][:5000] + "...\n\n[内容过长，已截断]",
                                            height=400
                                        )
                                        st.info(f"文档内容共 {result['char_count']} 字符，已显示前5000字符")
                                    else:
                                        st.text_area(
                                            "文档内容",
                                            result['content'],
                                            height=400
                                        )
                            
                            # 添加下载按钮
                            st.download_button(
                                label="💾 下载解析内容",
                                data=result['content'],
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_解析.txt",
                                mime="text/plain"
                            )
                            
                        else:
                            st.error(f"❌ 解析失败: {result['error']}")
                            if 'error_detail' in result:
                                with st.expander("查看错误详情"):
                                    st.code(result['error_detail'])
                    
                    except Exception as e:
                        st.error(f"❌ 解析过程中发生错误: {str(e)}")
                    
                    finally:
                        # 清理临时文件
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                        
                        # 完成进度条
                        progress_bar.progress(100)
                        time.sleep(0.5)
                        progress_bar.empty()

with tab2:
    st.subheader("批量文件处理")
    st.info("批量处理功能开发中...")
    
    # 多文件上传
    uploaded_files = st.file_uploader(
        "选择多个文件",
        type=['pdf', 'txt'],
        accept_multiple_files=True,
        help="可同时选择多个PDF或TXT文件"
    )
    
    if uploaded_files:
        st.write(f"已选择 {len(uploaded_files)} 个文件")
        
        # 文件列表
        for i, file in enumerate(uploaded_files, 1):
            file_size = len(file.getvalue()) / 1024  # KB
            st.write(f"{i}. {file.name} ({file_size:.1f} KB)")
        
        if st.button("批量解析", type="secondary"):
            st.warning("批量解析功能正在开发中...")

# 页脚
st.divider()
st.caption("""
使用说明：
1. 在左侧设置文件大小限制和显示选项
2. 上传单个文件或批量上传多个文件
3. 点击"开始解析"按钮处理文档
4. 查看解析结果和文档内容
""")

# 运行说明
with st.expander("🛠️ 如何运行此应用"):
    st.code("""
# 1. 安装依赖
pip install streamlit pdfplumber chardet

# 2. 运行应用
streamlit run app.py

# 3. 在浏览器中打开显示的URL（通常是 http://localhost:8501）
""")