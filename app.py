# app.py
import streamlit as st
import tempfile
import os
import time
from src.document_parser import DocumentParser
from src.text_splitter import TextSplitter

# 初始化session state
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "parse_result" not in st.session_state:
    st.session_state.parse_result = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None
if "show_chunks" not in st.session_state:
    st.session_state.show_chunks = False
if "chunk_analysis" not in st.session_state:
    st.session_state.chunk_analysis = None
 
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
        value=20,
        help="限制上传文件的最大大小"
    )
    
    st.subheader("✂️ 文本分块设置")
    
    chunk_method = st.radio(
        "分块方法:",
        ["paragraph", "fixed_size", "sentence"],
        index=0,
        help="paragraph: 按段落分割（推荐）\nfixed_size: 固定大小分割\nsentence: 按句子分割"
    )
    
    chunk_size = st.slider("块大小（字符数）", 100, 2000, 500, 50)
    chunk_overlap = st.slider("块重叠（字符数）", 0, 200, 50, 10)
    
    if chunk_overlap >= chunk_size:
        st.warning("⚠️ 重叠大小应小于块大小")

    # 显示选项
    show_raw = st.checkbox("显示原始内容", value=True)
    show_metadata = st.checkbox("显示元信息", value=True)
    
    st.divider()

    # 清除按钮
    if st.button("🗑️ 清除所有数据", type="secondary"):
        for key in ["uploaded_file", "parse_result", "chunks", "show_chunks", "chunk_analysis"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    st.caption("**状态**: 已保存数据将在此会话中保留")
    
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

    # 保存上传的文件到session state
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
    elif st.session_state.uploaded_file is not None:
        # 从session state恢复
        uploaded_file = st.session_state.uploaded_file
    
    if uploaded_file is not None:
        # 文件信息展示
        #print(f"[1] 用户选择了文件: {uploaded_file.name}")
        #print(f"[2] 文件大小: {len(uploaded_file.getvalue())} 字节")
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
                        #print(f"[3] 保存到临时文件: {tmp_path}")
                    
                    try:
                        # 添加进度条
                        progress_bar = st.progress(0)
                        
                        # 模拟解析进度
                        for i in range(100):
                            time.sleep(0.01)  # 稍微延迟，让进度条可见
                            progress_bar.progress(i + 1)
                        
                        # 解析文档
                        #print(f"[4] 调用解析器: {parser.parse_document.__name__}")
                        result = parser.parse_document(tmp_path)
                        #print(f"[5] 解析结果: success={result.get('success')}")

                        # 保存结果到session state
                        st.session_state.parse_result = result
                        st.session_state.show_chunks = False
                        st.session_state.chunks = None
                        st.session_state.chunk_analysis = None
                        
                        # 显示解析结果（从session state读取）
                        if st.session_state.parse_result is not None:
                            result = st.session_state.parse_result

                        if result['success']:
                            st.success("✅ 文档解析成功！")
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
                    
            # 显示解析结果（从session state读取）
            if st.session_state.parse_result is not None:
                result = st.session_state.parse_result                   
                            
                if result['success']:
                    # 显示文档元信息
                    if show_metadata:
                        with st.expander("📊 文档元信息", expanded=True):
                            meta_col1, meta_col2, meta_col3 = st.columns(3)
                            
                            #print(f"[6] 显示在界面: {result.get('char_count', 0)} 字符")
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
                                    height=400,
                                    key="content_area"
                                )
                    
                    st.download_button(
                        label="💾 下载解析内容",
                        data=result['content'],
                        file_name=f"{os.path.splitext(uploaded_file.name)[0]}_解析.txt",
                        mime="text/plain"
                    )

                    
                    # 添加分块分析部分
                    st.divider()
                    st.subheader("✂️ 文本分块分析")
                    
                    # 分析文本
                    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                    analysis = splitter.analyze_text(result['content'])
                    
                    # 显示分析结果
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("字符数", analysis.get('char_count', 0))
                    with col2:
                        st.metric("段落数", analysis.get('paragraph_count', 1))
                    with col3:
                        st.metric("推荐方法", analysis.get('recommended_method', 'paragraph'))
                    
                    # 分块按钮
                    if st.button("🚀 执行文本分块", type="primary", use_container_width=True):
                        with st.spinner(f"正在使用'{chunk_method}'方法分割文本..."):
                            chunks = splitter.split_text(result['content'], method=chunk_method)
                            
                            # 保存到session state
                            st.session_state.chunks = chunks
                            st.session_state.show_chunks = True
                            st.session_state.chunk_analysis = {
                                'total_chunks': len(chunks),
                                'method': chunk_method,
                                'avg_size': sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0
                            }

                            st.success(f"✅ 成功分割为 {len(chunks)} 个文本块")
                    
                    # 显示分块结果（如果存在）
                    if st.session_state.show_chunks and st.session_state.chunks is not None:
                        chunks = st.session_state.chunks
                        analysis = st.session_state.chunk_analysis

                        # 显示分块统计
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总块数", len(chunks))
                        with col2:
                            avg_size = sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0
                            st.metric("平均块大小", f"{avg_size:.0f} 字符")
                        with col3:
                            st.metric("分块方法", chunk_method)
                        
                        # 分页显示
                        if len(chunks) > 20:  # 只有块数多时才启用分页
                            st.info("📄 分块数量较多，已启用分页显示")
                            
                            # 分页设置
                            chunks_per_page = st.slider("每页显示块数", 5, 50, 10, 5)
                            total_pages = (len(chunks) + chunks_per_page - 1) // chunks_per_page
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                page_number = st.number_input(
                                    "页码",
                                    min_value=1,
                                    max_value=total_pages,
                                    value=1,
                                    step=1
                                )
                            with col2:
                                st.markdown(f"**第 {page_number}/{total_pages} 页**")
                            
                            # 计算当前页的块
                            start_idx = (page_number - 1) * chunks_per_page
                            end_idx = min(start_idx + chunks_per_page, len(chunks))
                            
                            # 显示当前页
                            with st.expander(f"查看第 {page_number} 页的分块", expanded=True):
                                for i in range(start_idx, end_idx):
                                    chunk = chunks[i]
                                    with st.container():
                                        st.markdown(f"**块 #{i+1}**")
                                        st.code(chunk.text[:300] + ("..." if len(chunk.text) > 300 else ""), language='text')
                                        st.divider()
                        else:
                            # 块数少时直接显示
                            with st.expander("查看全部分块", expanded=True):
                                for i, chunk in enumerate(chunks):
                                    with st.container():
                                        st.markdown(f"**块 #{i+1}**")
                                        st.code(chunk.text[:300] + ("..." if len(chunk.text) > 300 else ""), language='text')
                                        st.divider()
                        
                        
                        # ==================== 下载部分 ====================
                        st.divider()
                        st.markdown("#### 📤 文本分块结果导出选项")
                        
                        tab1, tab2, tab3 = st.tabs(["📊 快速统计", "🔽 按需下载", "⚠️ 完整下载"])
                        
                        with tab1:
                            st.write("**轻量导出，快速生成**")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # 1. JSON统计
                                import json
                                stats = {
                                    "document": uploaded_file.name,
                                    "total_chunks": len(chunks),
                                    "chunk_method": analysis['method'],
                                    "avg_chunk_size": analysis['avg_size'],
                                    "chunks": [
                                        {
                                            "id": i+1,
                                            "start": chunk.start_char,
                                            "end": chunk.end_char,
                                            "size": len(chunk.text),
                                            "preview": chunk.text[:100] + ("..." if len(chunk.text) > 100 else "")
                                        }
                                        for i, chunk in enumerate(chunks[:100])  # 只包含前100个块的预览
                                    ]
                                }
                                
                                st.download_button(
                                    label="📈 下载统计(JSON)",
                                    data=json.dumps(stats, ensure_ascii=False, indent=2),
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_stats.json",
                                    mime="application/json",
                                    use_container_width=True
                                )
                            
                            with col2:
                                # 2. CSV索引
                                import pandas as pd
                                import io
                                
                                data = {
                                    "chunk_id": list(range(1, len(chunks) + 1)),
                                    "start_char": [chunk.start_char for chunk in chunks],
                                    "end_char": [chunk.end_char for chunk in chunks],
                                    "size_chars": [len(chunk.text) for chunk in chunks],
                                    "has_content": ["是" if chunk.text.strip() else "否" for chunk in chunks]
                                }
                                
                                df = pd.DataFrame(data)
                                csv_buffer = io.StringIO()
                                df.to_csv(csv_buffer, index=False)
                                
                                st.download_button(
                                    label="📋 下载索引(CSV)",
                                    data=csv_buffer.getvalue(),
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_index.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                        
                        with tab2:
                            st.write("**选择下载部分块的内容**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                start = st.number_input("起始块", 1, len(chunks), 1, key="start_chunk")
                            with col2:
                                end = st.number_input("结束块", 1, len(chunks), min(10, len(chunks)), key="end_chunk")
                            
                            if end < start:
                                st.error("结束块必须大于起始块")
                            else:
                                total_selected = end - start + 1
                                
                                if total_selected > 1000:
                                    st.warning(f"选择了 {total_selected} 个块，生成可能需要较长时间")
                                
                                if st.button(f"生成块 {start}-{end} 的内容", type="primary"):
                                    with st.spinner(f"正在生成 {total_selected} 个块的内容..."):
                                        download_parts = []
                                        progress_bar = st.progress(0)
                                        
                                        for i in range(start-1, end):
                                            chunk = chunks[i]
                                            download_parts.append(f"【块 #{i+1}】\n")
                                            download_parts.append(f"位置: {chunk.start_char}-{chunk.end_char}\n")
                                            download_parts.append(f"字符数: {len(chunk.text)}\n\n")
                                            download_parts.append(chunk.text[:1000])  # 限制每个块最多1000字符
                                            download_parts.append("\n\n" + "="*50 + "\n\n")
                                            
                                            if (i - (start-1)) % 10 == 0:
                                                progress = (i - (start-1) + 1) / total_selected
                                                progress_bar.progress(progress)
                                        
                                        final_content = "".join(download_parts)
                                        
                                        st.download_button(
                                            label=f"💾 下载块 {start}-{end}",
                                            data=final_content,
                                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_chunks_{start}-{end}.txt",
                                            mime="text/plain",
                                            use_container_width=True
                                        )
                        
                        with tab3:
                            st.warning("⚠️ 完整下载会生成非常大的文件，可能导致浏览器卡顿")
                            
                            if len(chunks) > 1000:
                                st.error(f"文档有 {len(chunks)} 个块，完整下载不推荐")
                                st.info("建议使用'按需下载'选择部分块，或下载统计信息")
                            else:
                                if st.button("🚨 生成完整分块文件", type="secondary"):
                                    with st.spinner("正在生成完整文件..."):
                                        # 使用临时文件避免内存问题
                                        import tempfile
                                        
                                        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', 
                                                                        suffix='_full.txt') as tmp_file:
                                            tmp_path = tmp_file.name
                                            
                                            tmp_file.write("=== 完整分块结果 ===\n\n")
                                            
                                            progress_bar = st.progress(0)
                                            for i, chunk in enumerate(chunks):
                                                tmp_file.write(f"【块 #{i+1}】\n")
                                                tmp_file.write(f"位置: {chunk.start_char}-{chunk.end_char}\n")
                                                tmp_file.write(f"字符数: {len(chunk.text)}\n\n")
                                                tmp_file.write(chunk.text)
                                                tmp_file.write("\n\n" + "="*50 + "\n\n")
                                                
                                                if i % 100 == 0:
                                                    progress_bar.progress((i + 1) / len(chunks))
                                        
                                        # 读取并提供下载
                                        with open(tmp_path, 'r', encoding='utf-8') as f:
                                            file_content = f.read()
                                        
                                        st.download_button(
                                            label="📥 下载完整文件",
                                            data=file_content,
                                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_full_chunks.txt",
                                            mime="text/plain",
                                            use_container_width=True
                                        )
                                        
                                        # 清理
                                        os.unlink(tmp_path)

                    

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