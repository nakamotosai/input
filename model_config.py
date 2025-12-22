"""
模型配置管理模块
管理 ASR 和翻译模型的配置、路径、可用性检测
"""

import os
import sys
import zipfile
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List


class ASREngineType(Enum):
    """ASR引擎类型 (目前仅支持内置 Sherpa 版)"""
    SENSEVOICE_ONNX = "sensevoice_onnx"


class ASROutputMode(Enum):
    """ASR输出模式 (目前默认原始输出即可，Sherpa 自带标点)"""
    RAW = "raw"
    CLEANED = "cleaned"


class TranslatorEngineType(Enum):
    """翻译引擎类型"""
    NLLB_1_2B_CT2 = "nllb_1_2b_ct2"     # 1.2B高质量版(ctranslate2)
    NLLB_600M_CT2 = "nllb_600m_ct2"     # 600M标准版(ctranslate2)
    NLLB_ORIGINAL = "nllb_original"     # 原始版(transformers)
    GOOGLE = "online"                   # Google 在线翻译


@dataclass
class ModelInfo:
    """模型信息数据类"""
    name: str           # 显示名称
    path: str           # 模型路径
    engine_type: str    # 引擎类型枚举值
    loader: str         # 加载方式
    is_zip: bool = False # 是否为压缩包
    available: bool = False # 是否可用

class PersonalityManager:
    """个性化提示词管理类"""
    def __init__(self, config_path):
        self.config_path = config_path
        self.data = {"schemes": [], "current_scheme": "default"}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except: pass

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except: pass

    @property
    def current_scheme(self):
        sid = self.data.get("current_scheme", "default")
        for s in self.data["schemes"]:
            if s["id"] == sid: return s
        return self.data["schemes"][0] if self.data["schemes"] else None

    def get_prompt(self, key):
        scheme = self.current_scheme
        return scheme["prompts"].get(key, "") if scheme else ""

    def set_scheme(self, scheme_id):
        self.data["current_scheme"] = scheme_id
        self.save()

    def get_all_schemes(self):
        return [(s["id"], s["name"]) for s in self.data["schemes"]]

    def is_any_placeholder(self, text):
        if not text: return True
        for s in self.data["schemes"]:
            if text in s["prompts"].values(): return True
        return False


class ModelConfig:
    """模型配置管理器"""
    
    # 获取基础目录逻辑：支持 PyInstaller 打包后的路径
    if getattr(sys, 'frozen', False):
        # 打包后的运行/资源目录
        BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
        EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # 开发环境
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        EXE_DIR = BASE_DIR

    # 智能确定数据存储目录（需要写权限）
    def _initialize_paths(base_dir, exe_dir):
        # 给用户的配置和下载模型找个能写字的地方
        # 如果 EXE 目录可写（如绿色版），优先用 EXE 目录；
        # 如果不可写（如 Program Files），则用 %LOCALAPPDATA%
        
        test_dir = exe_dir
        is_writable = False
        try:
            test_file = os.path.join(test_dir, '.write_test')
            with open(test_file, 'w') as f: f.write('1')
            os.remove(test_file)
            is_writable = True
        except:
            is_writable = False

        if is_writable:
            data_root = exe_dir
        else:
            # 使用系统标准的用户数据存放目录
            app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', os.path.expanduser('~')))
            data_root = os.path.join(app_data, "CNJP_Input")
        
        os.makedirs(data_root, exist_ok=True)
        
        # 核心路径定义
        config_path = os.path.join(data_root, "config.json")
        user_models_dir = os.path.join(data_root, "models")
        os.makedirs(user_models_dir, exist_ok=True)
        
        # 资源/内置模型目录 (只读)
        bundled_models_dir = os.path.join(base_dir, "models")
        prompts_path = os.path.join(base_dir, "prompts.json")
        
        return config_path, prompts_path, user_models_dir, bundled_models_dir

    CONFIG_PATH, PROMPTS_PATH, MODELS_DIR, BUNDLED_MODELS_DIR = _initialize_paths(BASE_DIR, EXE_DIR)
    
    # ASR模型定义 (固定使用内置模型)
    ASR_MODELS: Dict[str, ModelInfo] = {
        ASREngineType.SENSEVOICE_ONNX.value: ModelInfo(
            name="内置 AI 语音引擎", 
            path="sensevoice_sherpa",
            engine_type=ASREngineType.SENSEVOICE_ONNX.value,
            loader="sherpa_onnx",
            is_zip=False,
            available=True # 默认内置视为可用
        )
    }
    
    # 翻译模型定义
    TRANSLATOR_MODELS: Dict[str, ModelInfo] = {
        TranslatorEngineType.NLLB_1_2B_CT2.value: ModelInfo(
            name="NLLB-200 1.2B (高质量)",
            path="nllb-200_1.2B_int8_ct2.zip",
            engine_type=TranslatorEngineType.NLLB_1_2B_CT2.value,
            loader="ctranslate2",
            is_zip=True
        ),
        TranslatorEngineType.NLLB_600M_CT2.value: ModelInfo(
            name="NLLB-200 600M (标准)",
            path="nllb_600m_v1.zip",
            engine_type=TranslatorEngineType.NLLB_600M_CT2.value,
            loader="ctranslate2",
            is_zip=True
        ),
        TranslatorEngineType.NLLB_ORIGINAL.value: ModelInfo(
            name="NLLB-200 Original (原始)",
            path="nllb-200-distilled-600M",
            engine_type=TranslatorEngineType.NLLB_ORIGINAL.value,
            loader="transformers"
        ),
        TranslatorEngineType.GOOGLE.value: ModelInfo(
            name="Google 在线翻译 (推荐/快速)",
            path="",
            engine_type=TranslatorEngineType.GOOGLE.value,
            loader="online",
            available=True
        ),
    }
    
    def __init__(self):
        self._current_asr_engine = ASREngineType.SENSEVOICE_ONNX.value
        self._current_translator_engine = TranslatorEngineType.GOOGLE.value
        self._asr_output_mode = ASROutputMode.RAW.value
        self._hotkey_asr = "ctrl+windows"
        self._hotkey_toggle_ui = "alt+windows"
        self._auto_tts = False
        self._tts_delay_ms = 1000
        self._wizard_completed = True # 默认已完成
        self._theme_mode = "Dark"
        self._window_scale = 1.0
        self._font_name = "思源宋体"
        self._app_mode = "asr"
        self._tip_shown = False
        self.data = {}
        self._load_config()
        self._scan_models()
        self.personality = PersonalityManager(self.PROMPTS_PATH)
    
    def _load_config(self):
        try:
            if os.path.exists(self.CONFIG_PATH):
                with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    self._current_asr_engine = ASREngineType.SENSEVOICE_ONNX.value # 强制固定
                    self._current_translator_engine = self.data.get('translator_engine', self._current_translator_engine)
                    self._asr_output_mode = self.data.get('asr_output_mode', self._asr_output_mode)
                    self._hotkey_asr = self.data.get('hotkey_asr', self._hotkey_asr)
                    self._hotkey_toggle_ui = self.data.get('hotkey_toggle_ui', self._hotkey_toggle_ui)
                    self._auto_tts = self.data.get('auto_tts', self._auto_tts)
                    self._tts_delay_ms = self.data.get('tts_delay_ms', self._tts_delay_ms)
                    self._wizard_completed = True 
                    self._theme_mode = self.data.get('theme_mode', self._theme_mode)
                    self._window_scale = self.data.get('window_scale', self._window_scale)
                    self._font_name = self.data.get('font_name', self._font_name)
                    self._app_mode = self.data.get('app_mode', self._app_mode)
                    self._tip_shown = self.data.get('tip_shown', self._tip_shown)
        except Exception as e:
            # 最小化日志记录，便于调试打包后的问题
            try:
                log_path = os.path.join(os.path.dirname(self.CONFIG_PATH), "error.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[load_config] {e}\n")
            except: pass
    
    def save_config(self):
        try:
            config = {}
            if os.path.exists(self.CONFIG_PATH):
                with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['asr_engine'] = self._current_asr_engine
            config['translator_engine'] = self._current_translator_engine
            config['asr_output_mode'] = self._asr_output_mode
            config['hotkey_asr'] = self._hotkey_asr
            config['hotkey_toggle_ui'] = self._hotkey_toggle_ui
            config['auto_tts'] = self._auto_tts
            config['tts_delay_ms'] = self._tts_delay_ms
            config['wizard_completed'] = True
            config['theme_mode'] = self._theme_mode
            config['window_scale'] = self._window_scale
            config['font_name'] = self._font_name
            config['app_mode'] = self._app_mode
            config['tip_shown'] = self._tip_shown
            self.data = config
            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            try:
                log_path = os.path.join(os.path.dirname(self.CONFIG_PATH), "error.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"[save_config] {e}\n")
            except: pass
    
    def _scan_models(self):
        # ASR 始终由于内置而可用
        self.ASR_MODELS[ASREngineType.SENSEVOICE_ONNX.value].available = True
        
        # 扫描翻译模型 (同时检查用户目录和内置目录)
        for key, model in self.TRANSLATOR_MODELS.items():
            found = False
            for root in [self.MODELS_DIR, self.BUNDLED_MODELS_DIR]:
                if not os.path.exists(root): continue
                
                if model.is_zip:
                    zip_path = os.path.join(root, model.path)
                    extracted_path = os.path.join(root, model.path.replace('.zip', ''))
                    if os.path.exists(zip_path) or os.path.exists(extracted_path):
                        found = True; break
                else:
                    full_path = os.path.join(root, model.path)
                    if os.path.exists(full_path):
                        found = True; break
            model.available = found
    
    def ensure_model_extracted(self, engine_type: str) -> Optional[str]:
        model = self.TRANSLATOR_MODELS.get(engine_type) or self.ASR_MODELS.get(engine_type)
        if not model: return None
        
        # 查找路径
        search_roots = [self.MODELS_DIR, self.BUNDLED_MODELS_DIR]
        
        # 1. 先看有没有解压好的
        for root in search_roots:
            if not os.path.exists(root): continue
            extracted_path = os.path.join(root, model.path.replace('.zip', '') if model.is_zip else model.path)
            if os.path.exists(extracted_path): return extracted_path
            
        # 2. 没有解压好的，看有没有 zip 到处找
        if not model.is_zip: return None
        
        zip_path = None
        for root in search_roots:
            p = os.path.join(root, model.path)
            if os.path.exists(p):
                zip_path = p; break
        
        if not zip_path: return None
        
        # 3. 准备解压。注意：如果 zip 在只读目录，解压目标必须去用户可写目录
        target_extract_root = self.MODELS_DIR if not self._is_path_writable(os.path.dirname(zip_path)) else os.path.dirname(zip_path)
        final_extract_path = os.path.join(target_extract_root, model.path.replace('.zip', ''))
        
        if os.path.exists(final_extract_path): return final_extract_path
        
        try:
            os.makedirs(target_extract_root, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(final_extract_path)
            return final_extract_path
        except: return None

    def _is_path_writable(self, path):
        try:
            test_file = os.path.join(path, '.test')
            with open(test_file, 'w') as f: f.write('1')
            os.remove(test_file)
            return True
        except: return False
    
    def get_model_path(self, engine_type: str) -> Optional[str]:
        return self.ensure_model_extracted(engine_type)
    
    @property
    def current_asr_engine(self) -> str: return self._current_asr_engine
    
    @current_asr_engine.setter
    def current_asr_engine(self, value: str): pass # 不再允许修改
    
    def get_asr_model_path(self) -> Optional[str]:
        # 不要写死路径，要使用统一的搜索逻辑（支持查找内置目录）
        return self.get_model_path(ASREngineType.SENSEVOICE_ONNX.value)
    
    @property
    def current_translator_engine(self) -> str: return self._current_translator_engine
    
    @current_translator_engine.setter
    def current_translator_engine(self, value: str):
        if value in self.TRANSLATOR_MODELS:
            self._current_translator_engine = value
            self.save_config()
    
    def get_translator_model_path(self, engine_type: str = None) -> Optional[str]:
        engine = engine_type or self._current_translator_engine
        return self.get_model_path(engine)
    
    @property
    def asr_output_mode(self) -> str: return self._asr_output_mode
    
    @asr_output_mode.setter
    def asr_output_mode(self, value: str):
        if value in [m.value for m in ASROutputMode]:
            self._asr_output_mode = value
            self.save_config()

    @property
    def hotkey_asr(self) -> str: return self._hotkey_asr
    @hotkey_asr.setter
    def hotkey_asr(self, value: str):
        self._hotkey_asr = value
        self.save_config()

    @property
    def hotkey_toggle_ui(self) -> str: return self._hotkey_toggle_ui
    @hotkey_toggle_ui.setter
    def hotkey_toggle_ui(self, value: str):
        self._hotkey_toggle_ui = value
        self.save_config()

    @property
    def auto_tts(self) -> bool: return self._auto_tts
    @auto_tts.setter
    def auto_tts(self, value: bool):
        self._auto_tts = value
        self.save_config()

    @property
    def tts_delay_ms(self) -> int: return getattr(self, '_tts_delay_ms', 5000)
    @tts_delay_ms.setter
    def tts_delay_ms(self, value: int):
        self._tts_delay_ms = max(0, int(value))
        self.save_config()

    @property
    def theme_mode(self) -> str: return self._theme_mode
    @theme_mode.setter
    def theme_mode(self, value: str):
        self._theme_mode = value
        self.save_config()

    @property
    def window_scale(self) -> float: return float(self._window_scale)
    @window_scale.setter
    def window_scale(self, value: float):
        self._window_scale = float(value)
        self.save_config()

    @property
    def font_name(self) -> str: return self._font_name
    @font_name.setter
    def font_name(self, value: str):
        self._font_name = value
        self.save_config()

    @property
    def wizard_completed(self) -> bool: return True
    @wizard_completed.setter
    def wizard_completed(self, value: bool): pass

    @property
    def app_mode(self) -> str: return self._app_mode
    @app_mode.setter
    def app_mode(self, value: str):
        self._app_mode = value
        self.save_config()

    @property
    def tip_shown(self) -> bool: return self._tip_shown
    @tip_shown.setter
    def tip_shown(self, value: bool):
        self._tip_shown = value
        self.save_config()

    def get_available_translator_engines(self) -> List[ModelInfo]:
        return [m for m in self.TRANSLATOR_MODELS.values() if m.available]
    
    def get_prompt(self, key) -> str: return self.personality.get_prompt(key)
    def set_personality_scheme(self, scheme_id): self.personality.set_scheme(scheme_id)
    def get_personality_schemes(self): return self.personality.get_all_schemes()
    def is_placeholder_text(self, text): return self.personality.is_any_placeholder(text)

# 全局单例
_model_config_instance: Optional[ModelConfig] = None
def get_model_config() -> ModelConfig:
    global _model_config_instance
    if _model_config_instance is None: _model_config_instance = ModelConfig()
    return _model_config_instance
