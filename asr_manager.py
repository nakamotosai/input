"""
ASR管理模块 - 专注于 Sherpa-ONNX 引擎的极简驱动
不再包含冗余的标点模型逻辑和复杂的正则启发式算法

修复：在主进程中解析模型路径后传递给子进程，避免子进程路径解析问题
"""

import os
import re
import gc
import sys
import numpy as np
import multiprocessing
import traceback
import threading
from abc import ABC, abstractmethod
from typing import Optional, List
from PyQt6.QtCore import QObject, pyqtSignal, QThread, pyqtSlot

from model_config import (
    get_model_config, 
    ASREngineType, 
    ASROutputMode
)

# 设置环境变量，解决可能的OpenMP库冲突
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def clean_asr_output(text: str, mode: str = "raw", is_insertion: bool = False) -> str:
    """
    清理ASR输出文本
    mode: "raw" 仅基础清理标签; "cleaned" 额外执行正则净化
    is_insertion: 如果为 True，则剥离末尾句号；如果为 False，则保留。
    """
    if not text:
        return ""
        
    # [Fix] 1. 预处理：去除首尾空白
    text = text.strip()
    if not text:
        return ""
        
    # [Fix] 2. 内容效验：必须包含至少一个有效字符 (中文、日文、韩文、字母、数字)
    # 防止 Sherpa-ONNX 幻觉输出纯标点 (如 "。" 或 "..." 或 "?")
    has_content = re.search(r'[\u4e00-\u9fa5\u3040-\u30ff\u31f0-\u31ff\uac00-\ud7af\w]', text)
    if not has_content:
        return ""
        
    # 3. 基础清理：移除所有模型内置标签 <|xxx|> 和 [xxx]
    text = re.sub(r'<\|.*?\|>', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # 2. 基础标点优化 (无论什么模式都执行)
    # A. 智能标点处理 (Smart Punctuation)
    # [Removed] 废弃“所以/但是”等后缀不加句号的逻辑
    incomplete_markers = r'$^' # 永远不匹配

    # 逻辑 1: 处理多句逻辑 - “留逗去句”
    # 如果检测到内部句号，将其替换为逗号 (用户反馈：两句话之间的逗号还是需要)
    if text:
        # A. 查找所有句号，如果后面还有文字，则将其替换为逗号
        text = re.sub(r'。(?!$)', '，', text)
        
        # B. 处理末尾句号
        # B. 处理末尾句号
        if is_insertion:
            # 插入模式：彻底剥离末尾句号 (包括全角和半角)
            text = text.rstrip('。！？.?!')
        else:
            # 非插入模式 (新起一段 或 追加)：
            # 如果识别结果本来没有句号，强制补全
            # 必须检查全角和半角标点，防止 "test." 变成 "test.。"
            if text and not (text.endswith(('。', '！', '？', '.', '!', '?'))):
                # 只有当它不像是一个未完成的句子时才加
                if not re.search(incomplete_markers, text):
                    text += "。"

    # 逻辑 2: 处理显式的“未完成”标识词 (无论是否插入都去掉标点)
    if re.search(incomplete_markers, text):
        text = text.rstrip('。！？')
        
    # 逻辑 3: 短文本片段深度保护 (如果是插入模式且短语，更倾向于去掉所有结尾标点)
    if is_insertion:
        core_text = text.rstrip('。！？')
        if core_text and len(core_text) <= 5:
            sentence_particles = r'.*[了吗吧呢啊呀哇嘛哒喔喽哩]$|.*[。，！？]$|.*[0-9a-zA-Z]$'
            if not re.match(sentence_particles, core_text):
                text = core_text

    # 强制移除连续重复标点 (例如 "。。" -> "。" 或 ".。" -> "。")
    text = re.sub(r'([。，！？.?!])\1+', r'\1', text)

    # 2. 如果是"正则表达 (Cleaned)"模式，执行更激进的净化
    if mode == ASROutputMode.CLEANED.value:
        # C. (已移除) 强制中日英文混排空格优化 - 响应用户反馈移除
        # text = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9])', r'\1 \2', text)
        # text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fa5])', r'\1 \2', text)
        
        # D. 移除句首句尾的空白字符
        text = text.strip()
    
    # E. Emoji 模式
    try:
        from model_config import EmojiMode, get_model_config
        # 重新获取配置以确保最新
        cfg = get_model_config()
        mode = cfg.emoji_mode
        
        if mode == EmojiMode.TRIGGER.value:
            # 语音触发模式：检测句末关键词并替换
            triggers = {
                "笑哭": "😂", "哈哈": "😄", "开心": "😊", 
                "点赞": "👍", "星星": "🌟", "爱心": "❤️", 
                "疑问": "❓", "生气": "😠", "流泪": "😭",
                "鼓掌": "👏", "庆祝": "🎉", "合十": "🙏",
                "加油": "💪", "滑稽": "🤪", "思考": "🤔"
            }
            # 检查句末 (忽略最后的标点)
            # 先剥离标点
            content = text
            suffix = ""
            if content and content[-1] in "。，！？":
                suffix = content[-1]
                content = content[:-1]
                
            for k, v in triggers.items():
                if content.endswith(k):
                    # 移除关键词
                    prefix = content[:-len(k)]
                    # 移除关键词前面的标点 (如 "有道理，" -> "有道理")
                    if prefix.endswith(("，", "。")):
                        prefix = prefix[:-1]
                    
                    content = prefix + v
                    # 触发模式下，Emoji 视作句末，不再追加原有的句尾标点
                    text = content 
                    break

        elif mode == EmojiMode.AUTO.value:
            # 自动模式：根据语气词添加，默认笑哭
            # 情感关键词映射（简化的关键词列表）
            sentiment_map = {
                "😄": ["哈哈", "嘿嘿", "开心", "高兴", "快乐", "好笑"],
                "😊": ["你好", "谢谢", "收到", "好的", "没问题", "喜欢"],
                "👍": ["不错", "厉害", "牛", "赞", "支持", "顺利"],
                "😭": ["难过", "伤心", "呜呜", "惨", "痛苦"],
                "😠": ["讨厌", "烦", "滚", "气死"],
                "🙏": ["拜托", "麻烦", "感谢", "辛苦"],
                "🤔": ["觉得", "想", "可能", "是否", "为什么"],
                "😂": [] # Default fallback
            }
            
            found_emoji = None
            for emoji, keywords in sentiment_map.items():
                for kw in keywords:
                    if kw in text:
                        found_emoji = emoji
                        break
                if found_emoji: break
            
            if not found_emoji:
                found_emoji = "😂"
            
            # 如果原文以句号或逗号结尾，先移除，再加 Emoji
            if text.endswith(("。", "，")):
                text = text[:-1]
            text += found_emoji
            
    except Exception as e:
        print(f"[ASRManager] Emoji error: {e}")

    # [Task] 语言敏感型空格处理
    # 如果包含中文或日文字符，则强制移除所有内部空格（中日文分词残留）
    # 如果是纯英文/西文，则保留单空格（保护英文单词间距）
    has_cjk = re.search(r'[\u4e00-\u9fa5\u3040-\u30ff\u31f0-\u31ff]', text)
    if has_cjk:
        text = re.sub(r'\s+', '', text)
    else:
        # 纯英文模式：仅将多重空格压缩为单空格
        text = re.sub(r'\s+', ' ', text)
        
    return text.strip()

# ===== 核心引擎代理 (重构为进程内线程安全模式) =====
class OnnxASREngine:
    def __init__(self):
        self.is_loaded = False
        self.recognizer = None
        self._lock = threading.Lock()
    
    def load(self, model_path: str) -> bool:
        """
        加载 ASR 模型 (在主进程中执行，规避多进程权限及环境冲突)
        """
        try:
            import os
            import sherpa_onnx
            
            # 验证模型路径
            if not model_path or not os.path.exists(model_path):
                print(f"[ASR-Engine] 模型路径无效: {model_path}")
                return False
            
            print(f"[ASR-Engine] 正在主进程加载 Sherpa-ONNX 模型: {model_path}")

            # 定义核心文件
            model_file = os.path.join(model_path, "model.int8.onnx")
            if not os.path.exists(model_file):
                model_file = os.path.join(model_path, "model.onnx")
                
            tokens_file = os.path.join(model_path, "tokens.txt")
            
            if not os.path.exists(model_file) or not os.path.exists(tokens_file):
                print(f"[ASR-Engine] 核心文件缺失: {model_file} 或 {tokens_file}")
                return False

            # 初始化识别器
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=model_file,
                tokens=tokens_file,
                use_itn=True,
                language="auto",
                num_threads=4
            )
            
            self.is_loaded = True
            print(f"[ASR-Engine] 模型加载成功")
            return True
                
        except Exception as e:
            print(f"[ASR-Engine] 加载异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def transcribe(self, audio_data) -> str:
        if not self.is_loaded or not self.recognizer:
            return ""
        try:
            # 转换数据为数组
            import numpy as np
            audio_array = np.array(audio_data, dtype=np.float32)
            
            with self._lock:
                stream = self.recognizer.create_stream()
                stream.accept_waveform(16000, audio_array)
                self.recognizer.decode_stream(stream)
                text = stream.result.text
            return text
        except Exception as e:
            print(f"[ASR-Engine] 转写失败: {e}")
            return ""

    def unload(self):
        with self._lock:
            self.recognizer = None
            self.is_loaded = False

# ===== ASR Worker & Manager =====
class ASRWorker(QObject):
    model_ready = pyqtSignal()
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.config = get_model_config()
        self.engine = OnnxASREngine()
    
    @pyqtSlot()
    def load_model(self):
        # 在主进程中解析模型路径
        model_path = self.config.get_asr_model_path()
        
        if not model_path:
            self.error_occurred.emit("未找到语音识别模型")
            return
            
        if not os.path.exists(model_path):
            self.error_occurred.emit(f"模型路径不存在: {model_path}")
            return
        
        self.status_changed.emit(f"正在启动语音引擎...")
        print(f"[ASRWorker] 解析的模型路径: {model_path}")
        
        if self.engine.load(model_path):
            self.status_changed.emit("语音引擎已就绪")
            self.model_ready.emit()
        else:
            self.error_occurred.emit("语音引擎加载失败")
    
    @pyqtSlot(object, bool)
    def transcribe(self, audio_data, is_insertion=False):
        if not self.engine.is_loaded: return
        try:
            raw_text = self.engine.transcribe(audio_data)
            if raw_text:
                mode = self.config.asr_output_mode
                cleaned_text = clean_asr_output(raw_text, mode=mode, is_insertion=is_insertion)
                self.result_ready.emit(cleaned_text)
        except:
            pass

class ASRManager(QObject):
    _instance = None
    _initialized = False
    
    model_ready = pyqtSignal()
    result_ready = pyqtSignal(str)
    error = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    _sig_load_model = pyqtSignal()
    _sig_transcribe = pyqtSignal(object, bool)
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ASRManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ASRManager._initialized:
            super().__init__()
            ASRManager._initialized = True
            self.worker = ASRWorker()
            self.thread = QThread()
            self.worker.moveToThread(self.thread)
            
            self.worker.model_ready.connect(self.model_ready.emit)
            self.worker.result_ready.connect(self.result_ready.emit)
            self.worker.error_occurred.connect(self.error.emit)
            self.worker.status_changed.connect(self.status_changed.emit)
            self._sig_load_model.connect(self.worker.load_model)
            self._sig_transcribe.connect(self.worker.transcribe)
            self.thread.start()

    def start(self): self._sig_load_model.emit()
    
    def transcribe_async(self, audio_data, is_insertion=False):
        data = audio_data.tolist() if isinstance(audio_data, np.ndarray) else audio_data
        self._sig_transcribe.emit(data, is_insertion)
    
    def cleanup(self):
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        if self.worker.engine: self.worker.engine.unload()
