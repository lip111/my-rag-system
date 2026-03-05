# src/embedder.py
import os
import time
from typing import List, Dict, Optional
import numpy as np

# 设置环境变量（在文件顶部）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 使用国内镜像
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'  # 超时时间300秒

class TextEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_local: bool = True):
        self.model_name = model_name
        self.model = None
        self.use_local = use_local
        
        # 本地模型路径
        self.local_path = f"./models/{model_name}"
        
    def load_model(self):
        if self.model is not None:
            return self.model
        
        print(f"🔧 正在加载模型: {self.model_name}")
        
        try:
            from sentence_transformers import SentenceTransformer
            
            # 优先尝试本地路径
            if self.use_local and os.path.exists(self.local_path):
                print(f"   从本地加载: {self.local_path}")
                self.model = SentenceTransformer(self.local_path)
            else:
                print(f"   从网络下载，使用镜像源...")
                # 确保使用镜像
                if 'HF_ENDPOINT' not in os.environ:
                    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                
                self.model = SentenceTransformer(
                    self.model_name,
                    cache_folder="./models"  # 保存到项目目录
                )
            
            # 测试模型
            test_vector = self.model.encode("test")
            print(f"✅ 模型加载成功，维度: {len(test_vector)}")
            
        except ImportError:
            print("❌ 未安装 sentence-transformers，使用随机向量")
            self.model = None
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            print("   将使用随机向量进行测试")
            self.model = None
        
        return self.model
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        将单个文本转换为向量
        
        参数:
            text: 要向量化的文本
            
        返回:
            numpy数组，形状为 (维度,)
        """
        model = self.load_model()
        # 这里就是核心：文本 → 向量
        vector = model.encode(text)
        return vector
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        批量向量化文本
        
        参数:
            texts: 文本列表
            
        返回:
            numpy数组，形状为 (文本数, 维度)
        """
        model = self.load_model()
        # 批量处理，效率更高
        vectors = model.encode(texts)
        return vectors
    
    def get_vector_info(self, vector: np.ndarray) -> Dict:
        """
        获取向量信息
        
        返回:
            包含向量信息的字典
        """
        return {
            "shape": vector.shape,
            "dtype": str(vector.dtype),
            "min": float(vector.min()),
            "max": float(vector.max()),
            "mean": float(vector.mean()),
            "sample": vector[:5].tolist()  # 前5个值
        }
