# 学习日志 - 文档解析模块

## 2026-02

### 学习到的内容

1. **Streamlit文件上传和解析流程**：

   用户上传 -> st.file_uploader接收 -> 检查文件大小和类型 -> tempfile.NamedTemporaryFile创建临时文件 -> 调用文件解析器 -> txt文档 -> chardet.detect获取编码 -> 解码读取 -> pdf文档 -> pdfplumber.extract_text提取文本
2. **tempfile:**

   使用tempfile库创建临时文件可以保证每个文件的唯一性，就算不同时刻上传同一个文件，文件名都会不同
3. **chardet:**

   chardet库用于检测文本文件编码，detect方法返回的检测结果是一个字典，包含编码、置信度等
