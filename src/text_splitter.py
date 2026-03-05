# src/text_splitter.py
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import tiktoken  # 用于计算token数，但我们可以先用字符数


@dataclass
class TextChunk:
    """文本块的数据类"""
    text: str
    chunk_id: int
    start_char: int
    end_char: int
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TextSplitter:
    """文本分割器，支持多种分割策略"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化文本分割器
        
        参数:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 确保重叠小于块大小
        if chunk_overlap >= chunk_size:
            raise ValueError(f"重叠大小({chunk_overlap})不能大于或等于块大小({chunk_size})")
    
    def split_by_fixed_size(self, text: str) -> List[TextChunk]:
        """
        按固定大小分割文本（最基础的方法）
        """
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # 计算块结束位置
            end = min(start + self.chunk_size, len(text))
            
            # 获取块文本
            chunk_text = text[start:end]
            
            # 创建块对象
            chunk = TextChunk(
                text=chunk_text,
                chunk_id=chunk_id,
                start_char=start,
                end_char=end,
                metadata={
                    'split_method': 'fixed_size',
                    'chunk_size': len(chunk_text),
                    'has_overlap': chunk_id > 0
                }
            )
            
            chunks.append(chunk)
            
            # 更新位置（考虑重叠），但确保向前移动
            new_start = end - self.chunk_overlap
            
            # 防止无限循环：确保start至少前进1个字符
            if new_start <= start:
                new_start = start + 1
            
            # 如果已经到文本末尾，退出循环
            if new_start >= len(text):
                break
                
            start = new_start
            chunk_id += 1
        
        return chunks
    
    def split_by_paragraph(self, text: str) -> List[TextChunk]:
        """
        按段落分割文本
        """
        # 按换行符分割段落
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        char_count = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # 如果当前段落已经超过块大小，单独成块
            if para_size > self.chunk_size:
                # 如果当前块有内容，先保存
                if current_chunk:
                    chunks.append(self._create_paragraph_chunk(current_chunk, chunk_id, char_count))
                    chunk_id += 1
                    current_chunk = []
                    current_size = 0
                
                # 大段落需要进一步分割
                sub_chunks = self.split_by_fixed_size(para)
                for sub_chunk in sub_chunks:
                    # 调整子块的起始位置
                    sub_chunk.start_char += char_count
                    sub_chunk.end_char += char_count
                    chunks.append(sub_chunk)
                    chunk_id += 1
                char_count += para_size
                continue
            
            # 如果添加这个段落会超过块大小，保存当前块
            if current_size + para_size > self.chunk_size and current_chunk:
                chunks.append(self._create_paragraph_chunk(current_chunk, chunk_id, char_count))
                chunk_id += 1
                char_count += current_size
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(self._create_paragraph_chunk(current_chunk, chunk_id, char_count))
        
        return chunks
    
    def _create_paragraph_chunk(self, paragraphs: List[str], chunk_id: int, start_char: int) -> TextChunk:
        """创建段落块"""
        chunk_text = '\n'.join(paragraphs)
        return TextChunk(
            text=chunk_text,
            chunk_id=chunk_id,
            start_char=start_char,
            end_char=start_char + len(chunk_text),
            metadata={
                'split_method': 'paragraph',
                'paragraph_count': len(paragraphs),
                'avg_paragraph_length': sum(len(p) for p in paragraphs) / len(paragraphs)
            }
        )
    
    def split_by_sentence(self, text: str) -> List[TextChunk]:
        """
        按句子分割文本（简单实现）
        """
        # 简单的中文句子分割：按句号、问号、感叹号分割
        sentence_endings = r'[。！？!?]'
        sentences = re.split(sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        char_count = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(self._create_sentence_chunk(current_chunk, chunk_id, char_count))
                chunk_id += 1
                char_count += current_size
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(self._create_sentence_chunk(current_chunk, chunk_id, char_count))
        
        return chunks
    
    def _create_sentence_chunk(self, sentences: List[str], chunk_id: int, start_char: int) -> TextChunk:
        """创建句子块"""
        chunk_text = '。'.join(sentences) + '。'  # 添加句号
        return TextChunk(
            text=chunk_text,
            chunk_id=chunk_id,
            start_char=start_char,
            end_char=start_char + len(chunk_text),
            metadata={
                'split_method': 'sentence',
                'sentence_count': len(sentences)
            }
        )
    
    def split_text(self, text: str, method: str = "paragraph") -> List[TextChunk]:
        """
        分割文本的主要入口函数
        """
        if not text or not text.strip():
            return []
        
        if method == "fixed_size":
            return self.split_by_fixed_size(text)
        elif method == "paragraph":
            return self.split_by_paragraph(text)
        elif method == "sentence":
            return self.split_by_sentence(text)
        else:
            raise ValueError(f"不支持的分割方法: {method}，可选: fixed_size, paragraph, sentence")
    
    def analyze_text(self, text: str) -> Dict:
        """
        分析文本，提供分割建议
        """
        if not text:
            return {}
        
        # 基础统计
        char_count = len(text)
        word_count = len(text.split())  # 简单分词
        line_count = text.count('\n') + 1
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # 估计分块数量
        if char_count > 0 and self.chunk_size - self.chunk_overlap > 0:
            estimated_chunks_fixed = max(1, char_count // (self.chunk_size - self.chunk_overlap))
        else:
            estimated_chunks_fixed = 1
            
        estimated_chunks_paragraph = max(1, paragraph_count)
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'line_count': line_count,
            'paragraph_count': paragraph_count,
            'estimated_chunks_fixed': estimated_chunks_fixed,
            'estimated_chunks_paragraph': estimated_chunks_paragraph,
            'recommended_method': 'paragraph' if paragraph_count > 1 else 'fixed_size'
        }