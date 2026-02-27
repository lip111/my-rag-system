# src/document_parser.py
import pdfplumber
import chardet
from typing import Dict, List, Optional
import os
from datetime import datetime


class DocumentParser:
    """文档解析器，支持PDF和TXT格式"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt']
    
    def parse_document(self, file_path: str) -> Dict:
        """
        解析文档的主要入口函数
        
        参数:
            file_path: 文件路径
            
        返回:
            Dict: 包含解析结果和元信息的字典
        """

        result = {
            'success': False,
            'content': '',
            'error': None,
            'metadata': {},
            'char_count': 0,
            'file_size': 0,
            'file_name': os.path.basename(file_path),
            'file_type': os.path.splitext(file_path)[1].lower()
        }
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                result['error'] = f"文件不存在: {file_path}"
                return result
            
            # 检查文件格式是否支持
            file_ext = result['file_type']
            if file_ext not in self.supported_formats:
                result['error'] = f"不支持的文件格式: {file_ext}，支持格式: {', '.join(self.supported_formats)}"
                return result
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            result['file_size'] = file_size
            result['metadata']['file_size_mb'] = round(file_size / (1024 * 1024), 2)
            
            # 根据文件类型调用相应的解析函数
            if file_ext == '.pdf':
                parse_result = self.parse_pdf(file_path)
            elif file_ext == '.txt':
                parse_result = self.parse_txt(file_path)
            else:
                parse_result = {'success': False, 'content': '', 'error': '未知文件格式'}
            
            # 合并解析结果
            if parse_result.get('success', False):
                result['success'] = True
                result['content'] = parse_result.get('content', '')
                result['char_count'] = len(result['content'])
                
                # 合并元数据
                if 'metadata' in parse_result:
                    result['metadata'].update(parse_result['metadata'])
                
                # 添加解析时间
                result['metadata']['parsed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                result['metadata']['encoding'] = parse_result.get('encoding', 'unknown')
            else:
                result['error'] = parse_result.get('error', '解析失败')
                
        except Exception as e:
            result['error'] = f"解析过程中发生异常: {str(e)}"
            import traceback
            result['error_detail'] = traceback.format_exc()
        
        return result
    
    def parse_pdf(self, file_path: str) -> Dict:
        """解析PDF文件"""
        result = {'success': False, 'content': '', 'error': None, 'metadata': {}}
        pages_content = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                # 提取文本
                for i, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        # print(f"text: {text}")
                        if text and text.strip():
                            pages_content.append(f"--- 第 {i} 页 ---\n{text}")
                    except Exception as e:
                        print(f"警告: 提取第 {i} 页时出错: {e}")
                        pages_content.append(f"--- 第 {i} 页 [提取失败] ---")
                
                # 尝试提取表格
                tables_content = []
                for i, page in enumerate(pdf.pages, 1):
                    try:
                        tables = page.extract_tables()
                        if tables:
                            for table in tables:
                                if table:
                                    tables_content.append(f"第 {i} 页表格: {table}")
                    except:
                        pass

                result['metadata']['page_count'] = len(pdf.pages)
                result['metadata']['has_tables'] = len(tables_content) > 0
                
                # 合并内容和表格
                all_content = '\n\n'.join(pages_content)
                if tables_content:
                    all_content += '\n\n--- 表格数据 ---\n' + '\n'.join(tables_content)
                
                result['success'] = True
                result['content'] = all_content
                
        except Exception as e:
            result['error'] = f"PDF解析失败: {str(e)}"
        
        return result
    
    def parse_txt(self, file_path: str) -> Dict:
        """解析TXT文件，自动检测编码"""
        result = {'success': False, 'content': '', 'error': None, 'metadata': {}}
        
        try:
            # 检测文件编码
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # 读取前10000字节来检测编码
            
            # 使用chardet检测编码
            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)

            # 如果置信度低，尝试常见编码
            if confidence < 0.7:
                encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'ascii']
            else:
                encodings_to_try = [encoding, 'utf-8', 'gbk']
            
            # 尝试用不同编码读取文件
            content = None
            used_encoding = None
            
            for enc in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                        content = f.read()
                    used_encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                result['error'] = f"无法解码文件，尝试的编码: {encodings_to_try}"
                return result
            
            result['success'] = True
            result['content'] = content
            result['encoding'] = used_encoding

            lines = result.get("content", "").split("\n")
            non_empty_lines = [line for line in lines if line.strip()]

            result['metadata']['total_lines'] = len(lines)
            result['metadata']['non_empty_lines'] = len(non_empty_lines)
            result['metadata']['detected_encoding'] = encoding
            result['metadata']['confidence'] = confidence
            result['metadata']['tried_encodings'] = encodings_to_try
            
        except Exception as e:
            result['error'] = f"TXT解析失败: {str(e)}"
        
        return result
    
    def validate_file(self, file_bytes: bytes, file_name: str, max_size_mb: int = 10) -> Dict:
        """
        验证上传的文件
        
        参数:
            file_bytes: 文件字节
            file_name: 文件名
            max_size_mb: 最大文件大小(MB)
            
        返回:
            Dict: 验证结果
        """
        result = {
            'valid': False,
            'error': None,
            'file_size_mb': 0,
            'file_type': ''
        }
        
        try:
            # 检查文件大小
            file_size = len(file_bytes)
            file_size_mb = file_size / (1024 * 1024)
            result['file_size_mb'] = file_size_mb
            
            if file_size_mb > max_size_mb:
                result['error'] = f"文件过大: {file_size_mb:.2f}MB (最大: {max_size_mb}MB)"
                return result
            
            # 检查文件格式
            file_ext = os.path.splitext(file_name)[1].lower()
            result['file_type'] = file_ext
            
            if file_ext not in self.supported_formats:
                result['error'] = f"不支持的文件格式: {file_ext}，支持格式: {', '.join(self.supported_formats)}"
                return result
            
            result['valid'] = True
            
        except Exception as e:
            result['error'] = f"文件验证失败: {str(e)}"
        
        return result