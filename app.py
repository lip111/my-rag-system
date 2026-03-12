# app.py
import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import streamlit as st
import tempfile
import os
import time
from src.document_parser import DocumentParser
from src.text_splitter import TextSplitter
from src.embedder import TextEmbedder
import numpy as np
from src.vector_store import VectorStore

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
if "vectors" not in st.session_state:
    st.session_state.vectors = None
if "vector_info" not in st.session_state:
    st.session_state.vector_info = None
 
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


    st.subheader("🧠 向量化设置")
    
    embedding_model = st.selectbox(
        "嵌入模型:",
        ["all-MiniLM-L6-v2", "paraphrase-multilingual-MiniLM-L12-v2"],
        index=0,
        help="all-MiniLM-L6-v2: 英文优化，速度快\nparaphrase-multilingual: 多语言支持，包括中文"
    )
    
    batch_size = st.slider("批处理大小", 8, 64, 16, 8,
                          help="一次处理多少个文本块，越大越快但需要更多内存")
    
    if st.checkbox("显示高级设置", value=False):
        device = st.radio("运行设备", ["cpu", "cuda"], index=0,
                         help="cuda需要GPU支持")


    st.subheader("🗃️ 向量数据库设置")
    
    collection_name = st.text_input(
        "集合名称",
        value="documents",
        help="向量数据库的集合名称"
    )
    
    persist_dir = st.text_input(
        "存储路径",
        value="./chroma_db",
        help="向量数据库文件存储路径"
    )
    
    # 搜索设置
    n_results = st.slider(
        "搜索结果数量",
        min_value=1,
        max_value=20,
        value=5,
        help="每次搜索返回的结果数量"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 清空向量数据库", type="secondary"):
            vector_store = VectorStore(collection_name, persist_dir)
            if vector_store.delete_collection():
                st.success("✅ 向量数据库已清空")
            else:
                st.error("❌ 清空失败")
    
    with col2:
        if st.button("🔄 重置向量数据库", type="secondary"):
            vector_store = VectorStore(collection_name, persist_dir)
            if vector_store.reset():
                st.success("✅ 向量数据库已重置")
            else:
                st.error("❌ 重置失败")



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
                        
                        # 添加向量化部分
                        st.divider()
                        st.subheader("🧠 向量化处理")

                        if st.button("🚀 开始向量化", type="primary", use_container_width=True, key="embed_button"):
                            with st.spinner("正在初始化嵌入模型..."):
                                try:
                                    # 创建嵌入器
                                    embedder = TextEmbedder(model_name=embedding_model)
                                    
                                    # 显示进度
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    # 1. 加载模型
                                    status_text.text("正在加载模型...")
                                    if embedder.load_model() is None:
                                        st.error("❌ 模型加载失败")
                                    else:
                                        progress_bar.progress(20)
                                        
                                        # 2. 准备文本
                                        texts = [chunk.text for chunk in chunks]
                                        total_chunks = len(texts)
                                        
                                        # 3. 分批处理
                                        status_text.text(f"开始向量化 {total_chunks} 个文本块...")
                                        all_vectors = []
                                        
                                        for batch_num, i in enumerate(range(0, total_chunks, batch_size)):
                                            batch_texts = texts[i:i+batch_size]
                                            batch_num += 1
                                            total_batches = (total_chunks + batch_size - 1) // batch_size
                                            
                                            status_text.text(f"处理批次 {batch_num}/{total_batches} ({len(batch_texts)} 个块)")
                                            
                                            # 向量化这一批
                                            batch_vectors = embedder.embed_batch(batch_texts)
                                            all_vectors.extend(batch_vectors)
                                            
                                            # 更新进度
                                            processed = min(i + batch_size, total_chunks)
                                            progress = processed / total_chunks
                                            progress_value = 0.2 + 0.7 * progress  # 20%到90%之间
                                            progress_bar.progress(progress_value)  # 使用0-1的值
                                            status_text.text(f"已处理 {processed}/{total_chunks} 个块")
                                        
                                        # 4. 保存结果
                                        progress_bar.progress(95)
                                        status_text.text("保存结果...")
                                        
                                        st.session_state.vectors = all_vectors
                                        st.session_state.vector_info = {
                                            "model": embedding_model,
                                            "dimension": len(all_vectors[0]) if all_vectors else 0,
                                            "total_vectors": len(all_vectors),
                                            "batch_size": batch_size
                                        }
                                        
                                        progress_bar.progress(100)
                                        status_text.text("✅ 向量化完成！")
                                        
                                        st.success(f"✅ 成功向量化 {len(all_vectors)} 个文本块")
                                        
                                        # 显示统计
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("向量维度", st.session_state.vector_info["dimension"])
                                        with col2:
                                            st.metric("总向量数", st.session_state.vector_info["total_vectors"])
                                        with col3:
                                            st.metric("批处理大小", batch_size)
                                        
                                        # 显示示例向量
                                        with st.expander("查看示例向量", expanded=False):
                                            if all_vectors:
                                                sample = all_vectors[0]
                                                st.code(f"前10个值: {sample[:10]}", language="python")
                                                st.caption(f"向量长度: {len(sample)}")
                                        
                                        st.info("📦 向量已准备就绪，可以进行下一步：存储到向量数据库。")
                                    
                                except Exception as e:
                                    st.error(f"❌ 向量化过程中发生错误: {str(e)}")
                                    import traceback
                                    with st.expander("查看错误详情"):
                                        st.code(traceback.format_exc())
                                finally:
                                    time.sleep(1)
                                    progress_bar.empty()
                                    status_text.empty()
                        
                        if st.button("🔄 清除向量", type="secondary", use_container_width=False, key="clear_vectors"):
                            if "vectors" in st.session_state:
                                del st.session_state.vectors
                            if "vector_info" in st.session_state:
                                del st.session_state.vector_info
                            st.success("✅ 已清除向量数据")
                        
                        # 显示已有的向量化结果
                        if "vectors" in st.session_state and st.session_state.vectors:
                            info = st.session_state.vector_info
                            st.info(f"📊 已有 {info['total_vectors']} 个向量化结果（维度: {info['dimension']}）")  
                        
                            # 在向量化部分之后添加向量数据库存储
                            vectors = st.session_state.vectors
                            chunks = st.session_state.chunks
                            
                            st.divider()
                            st.subheader("🗃️ 向量数据库存储")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("💾 存储到向量数据库", type="primary", use_container_width=True, key="store_vectors"):
                                    with st.spinner("正在存储到向量数据库..."):
                                        try:
                                            # 创建向量数据库
                                            vector_store = VectorStore(collection_name, persist_dir)
                                            
                                            # 转换向量为列表格式
                                            vectors_list = [v.tolist() if hasattr(v, 'tolist') else v for v in vectors]
                                            
                                            # 添加到向量数据库
                                            result = vector_store.add_chunks(chunks, vectors_list)
                                            
                                            if result["success"]:
                                                st.success(f"✅ 成功存储 {result['count']} 个向量")
                                                
                                                # 获取集合信息
                                                info = vector_store.get_collection_info()
                                                st.info(f"📊 向量数据库现有 {info['count']} 个向量")
                                                
                                                # 保存向量数据库实例到session_state
                                                st.session_state.vector_store = vector_store
                                                st.session_state.collection_info = info
                                            else:
                                                st.error(f"❌ 存储失败: {result.get('error', '未知错误')}")
                                                
                                        except Exception as e:
                                            st.error(f"❌ 存储过程中发生错误: {str(e)}")
                                            import traceback
                                            with st.expander("查看错误详情"):
                                                st.code(traceback.format_exc())
                            
                            with col2:
                                if st.button("📊 查看数据库状态", type="secondary", use_container_width=True, key="view_db"):
                                    try:
                                        vector_store = VectorStore(collection_name, persist_dir)
                                        info = vector_store.get_collection_info()
                                        
                                        st.success(f"✅ 向量数据库状态")
                                        st.json(info)
                                        
                                        st.session_state.vector_store = vector_store
                                        st.session_state.collection_info = info
                                        
                                    except Exception as e:
                                        st.error(f"❌ 获取状态失败: {e}") 

                            # 在向量数据库存储后添加搜索功能
                            if "vector_store" in st.session_state and st.session_state.vector_store:
                                vector_store = st.session_state.vector_store
                                
                                st.divider()
                                st.subheader("🔍 向量搜索测试")
                                
                                # 搜索输入
                                search_query = st.text_input(
                                    "输入搜索内容",
                                    placeholder="输入您要搜索的问题...",
                                    key="search_input"
                                )
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    search_clicked = st.button("🔍 开始搜索", type="primary", use_container_width=True, key="search_button")
                                
                                with col2:
                                    if st.button("📋 显示示例", type="secondary", use_container_width=True, key="example_button"):
                                        examples = [
                                            "什么是机器学习？",
                                            "深度学习有什么应用？",
                                            "Python编程语言的特点",
                                            "向量数据库的作用"
                                        ]
                                        import random
                                        st.session_state.example_query = random.choice(examples)
                                        st.rerun()
                                
                                # 如果有示例查询，设置到输入框
                                if "example_query" in st.session_state:
                                    search_query = st.session_state.example_query
                                    del st.session_state.example_query
                                
                                if search_clicked and search_query:
                                    with st.spinner("正在搜索..."):
                                        try:
                                            # 需要向量化器
                                            if "embedder" not in st.session_state:
                                                from src.embedder import TextEmbedder
                                                st.session_state.embedder = TextEmbedder()
                                            
                                            embedder = st.session_state.embedder
                                            
                                            # 执行搜索
                                            results = vector_store.search_by_text(
                                                query_text=search_query,
                                                embedder=embedder,
                                                n_results=n_results
                                            )
                                            
                                            st.success(f"✅ 找到 {len(results)} 个相关结果")
                                            
                                            # 显示结果
                                            for i, result in enumerate(results):
                                                with st.expander(f"结果 {i+1} (相似度: {result['score']:.3f})", expanded=i==0):
                                                    # 显示文本
                                                    st.markdown("**相关内容:**")
                                                    st.write(result["text"])
                                                    
                                                    # 显示元数据
                                                    if result["metadata"]:
                                                        st.markdown("**元数据:**")
                                                        st.json(result["metadata"])
                                                    
                                                    st.divider()
                                            
                                            # 保存搜索结果
                                            st.session_state.last_search_results = results
                                            st.session_state.last_search_query = search_query
                                            
                                        except Exception as e:
                                            st.error(f"❌ 搜索失败: {str(e)}")
                                
                                # 显示历史搜索结果
                                if "last_search_results" in st.session_state and st.session_state.last_search_results:
                                    st.info(f"📄 上次搜索: '{st.session_state.last_search_query}'，找到 {len(st.session_state.last_search_results)} 个结果")                     

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