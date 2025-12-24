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

def clean_asr_output(text: str, mode: str = "raw") -> str:
    """
    清理ASR输出文本
    mode: "raw" 仅基础清理标签; "cleaned" 额外执行正则净化
    """
    if not text:
        return text
        
    # 1. 基础清理：移除所有模型内置标签 <|xxx|> 和 [xxx] (无论哪种模式都必须移除，否则无法阅读)
    text = re.sub(r'<\|.*?\|>', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # 2. 如果是"正则表达 (Cleaned)"模式，执行额外的净化逻辑
    if mode == ASROutputMode.CLEANED.value:
        # A. 移除常见的口癖/无意义填充词 (可选，根据用户反馈调整)
        # fillers = r'(呃|啊|吧|呢|那个|然后)'
        # text = re.sub(fillers, '', text)
        
        # B. 修复重复标点 (例如 "。。" -> "。")
        text = re.sub(r'([。，！？])\1+', r'\1', text)
        
        # C. 强制中日英文混排空格优化 (Sherpa自带一些，这里做增强)
        # 在汉字与英文字母/数字之间增加空格
        text = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fa5])', r'\1 \2', text)
        
        # D. 移除句首句尾的空白字符
        text = text.strip()
    
    # 3. 移除多余的多重空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ===== ONNX 推理独立进程核心函数 =====
def onnx_inference_worker(model_path, input_queue, output_queue, log_file=None):
    """
    独立的 ONNX 推理进程
    
    重要：model_path 必须是在主进程中已解析好的绝对路径
    """
    try:
        import sys
        if log_file:
            try:
                import os
                sys.stdout = open(log_file, "a", encoding="utf-8")
                sys.stderr = sys.stdout
            except: pass

        import sherpa_onnx
        print(f"[ASR-Proc] 正在加载 Sherpa-ONNX 模型: {model_path}")
        print(f"[ASR-Proc] 模型路径存在: {os.path.exists(model_path)}")
        
        # 定义核心文件
        model_file = os.path.join(model_path, "model.int8.onnx")
        if not os.path.exists(model_file):
            model_file = os.path.join(model_path, "model.onnx")
            
        tokens_file = os.path.join(model_path, "tokens.txt")
        
        print(f"[ASR-Proc] 模型文件: {model_file}, 存在: {os.path.exists(model_file)}")
        print(f"[ASR-Proc] Tokens文件: {tokens_file}, 存在: {os.path.exists(tokens_file)}")
        
        if not os.path.exists(model_file) or not os.path.exists(tokens_file):
            raise FileNotFoundError(f"核心模型文件缺失，请检查 {model_path} 目录")

        # 初始化识别器
        recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=model_file,
            tokens=tokens_file,
            use_itn=True,  # 使用内置的标点和文本标准化
            num_threads=4
        )
            
        print(f"[ASR-Proc] 模型加载成功")
        sys.stdout.flush()
        
        # 通知主进程已就绪
        output_queue.put(("ready", True))
        
        while True:
            # 等待任务
            task = input_queue.get()
            if task is None: 
                break
            
            try:
                # 转化数据
                audio_data = np.array(task, dtype=np.float32)
                
                # Sherpa 极简推理流程
                stream = recognizer.create_stream()
                stream.accept_waveform(16000, audio_data)
                recognizer.decode_stream(stream)
                
                # 直接返回识别结果，由主进程根据模式进行次级清理
                text = stream.result.text
                output_queue.put(("result", text))
                
            except Exception as e:
                # 在打包后的无控制台模式下，sys.stdout 可能为 None
                try: print(f"[ASR-Proc] 转写中错误: {e}")
                except: pass
                output_queue.put(("result", ""))
            
    except Exception as e:
        err = f"ASR进程崩溃: {str(e)}"
        try: 
            print(err)
            traceback.print_exc()
        except: pass
        output_queue.put(("fatal", err))
    finally:
        try: print("[ASR-Proc] 进程已退出")
        except: pass


# ===== 核心引擎代理 =====
class OnnxASREngine:
    def __init__(self):
        self.is_loaded = False
        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        self.process = None
    
    def load(self, model_path: str) -> bool:
        """
        加载 ASR 模型
        
        重要：model_path 必须是已解析好的绝对路径
        """
        try:
            if self.process and self.process.is_alive():
                self.unload()
            
            # 验证模型路径
            if not model_path or not os.path.exists(model_path):
                print(f"[ASR-Engine] 模型路径无效: {model_path}")
                return False
            
            # 获取日志目录
            from model_config import get_model_config
            cfg = get_model_config()
            log_file = os.path.join(cfg.DATA_DIR, "asr_process.log")

            print(f"[ASR-Engine] 启动 ASR 进程，模型路径: {model_path}")

            self.process = multiprocessing.Process(
                target=onnx_inference_worker,
                args=(model_path, self.input_queue, self.output_queue, log_file),
                daemon=True
            )
            self.process.start()
            
            # 等待确认信号
            try:
                msg_type, val = self.output_queue.get(timeout=30)
                if msg_type == "ready":
                    self.is_loaded = True
                    print(f"[ASR-Engine] ASR 进程就绪")
                    return True
                elif msg_type == "fatal":
                    print(f"[ASR-Engine] ASR 进程启动失败: {val}")
            except Exception as e:
                print(f"[ASR-Engine] 等待 ASR 进程超时: {e}")
            return False
        except Exception as e:
            print(f"[ASR-Engine] 启动异常: {e}")
            return False
    
    def transcribe(self, audio_data) -> str:
        if not self.is_loaded or not self.process.is_alive():
            return ""
        try:
            audio_list = audio_data.tolist() if isinstance(audio_data, np.ndarray) else audio_data
            self.input_queue.put(audio_list)
            msg_type, val = self.output_queue.get(timeout=30)
            return val
        except:
            return ""

    def unload(self):
        if self.process and self.process.is_alive():
            try:
                self.input_queue.put(None)
                self.process.join(timeout=3)
                if self.process.is_alive(): 
                    self.process.terminate()
                    self.process.join(timeout=1)
            except: pass
            finally:
                try:
                    self.input_queue.close()
                    self.output_queue.close()
                except: pass
        self.process = None
        self.is_loaded = False
        self.input_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()

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
    
    @pyqtSlot(object)
    def transcribe(self, audio_data):
        if not self.engine.is_loaded: return
        try:
            raw_text = self.engine.transcribe(audio_data)
            if raw_text:
                mode = self.config.asr_output_mode
                cleaned_text = clean_asr_output(raw_text, mode=mode)
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
    _sig_transcribe = pyqtSignal(object)
    
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
    
    def transcribe_async(self, audio_data):
        data = audio_data.tolist() if isinstance(audio_data, np.ndarray) else audio_data
        self._sig_transcribe.emit(data)
    
    def cleanup(self):
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        if self.worker.engine: self.worker.engine.unload()
