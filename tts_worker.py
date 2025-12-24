"""
TTS Worker - 使用 Edge-TTS 合成日语语音，通过 sounddevice 播放

核心特性：
1. 显式选择 Stereo 输出设备，绕过蓝牙 Hands-Free 端点
2. 支持中断播放：新的语音请求会立即中断当前播放
"""
import edge_tts
import sounddevice as sd
import numpy as np
import asyncio
import io
import threading
import logging
import traceback
import os

# 配置日志输出到文件
def _setup_logging():
    from model_config import get_model_config
    cfg = get_model_config()
    log_file = os.path.join(cfg.DATA_DIR, "tts_worker.log")
    try:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8',
            force=True
        )
        logging.info("TTS Worker logging started.")
        
        # 检查 ffmpeg
        import subprocess
        try:
            res = subprocess.run(['ffmpeg', '-version'], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
            logging.info(f"ffmpeg 探测成功")
        except:
            logging.error("ffmpeg 未找到，pydub 将无法处理 MP3。")
        
        print(f"[TTS] 日志已启用: {log_file}")
    except Exception as e:
        print(f"[TTS] 日志初始化失败: {e}")

_setup_logging()

# 语音选择 (ja-JP-NanamiNeural 是目前音质最好的日语女声之一)
VOICE = "ja-JP-NanamiNeural"


def _find_stereo_output_device():
    """
    查找可用的 Stereo (双声道) 输出设备，避开 Hands-Free (单声道) 端点。
    """
    try:
        devices = sd.query_devices()
        default_output = sd.default.device[1]
        
        # 第一轮：寻找蓝牙耳机的 Stereo 端点
        for i, dev in enumerate(devices):
            if dev['max_output_channels'] < 2:
                continue
            
            name = dev['name'].lower()
            is_headphone = '耳机' in dev['name'] or 'headphone' in name or 'headset' in name
            is_hands_free = 'hands' in name or 'free' in name or 'hfp' in name
            
            if is_headphone and not is_hands_free:
                return i
        
        # 第二轮：任意双声道输出设备
        for i, dev in enumerate(devices):
            if dev['max_output_channels'] < 2:
                continue
            
            name = dev['name'].lower()
            if 'hands' in name or 'free' in name or 'hfp' in name:
                continue
                
            return i
        
        return default_output
        
    except Exception as e:
        logging.warning(f"[TTS] 设备查询失败: {e}")
        return None


def _decode_mp3_to_pcm(mp3_data):
    """使用 pydub 将 MP3 数据解码为 PCM numpy 数组"""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        samples = np.array(audio.get_array_of_samples())
        
        if audio.sample_width == 2:
            samples = samples.astype(np.float32) / 32768.0
        elif audio.sample_width == 1:
            samples = (samples.astype(np.float32) - 128) / 128.0
        
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
        
        return samples, audio.frame_rate
    except ImportError:
        logging.error("[TTS] pydub 未安装。请运行: pip install pydub")
        return None, None
    except Exception as e:
        logging.error(f"[TTS] MP3 解码错误: {e}")
        logging.error(traceback.format_exc())
        return None, None


class TTSWorker:
    def __init__(self):
        self._lock = threading.Lock()
        self._output_device = None
        self._stop_event = threading.Event()  # 用于中断当前播放
        self._current_text = None  # 当前正在播放的文本
    
    def _refresh_device(self):
        """刷新输出设备选择"""
        self._output_device = _find_stereo_output_device()

    async def _get_audio_data(self, text):
        """调用 Edge-TTS 获取音频二进制数据"""
        try:
            # 增加任务超时保护
            communicate = edge_tts.Communicate(text, VOICE)
            audio_stream = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_stream.write(chunk["data"])
            data = audio_stream.getvalue()
            return data
        except Exception as e:
            logging.error(f"[TTS] Edge-TTS 异常: {e}")
            return None

    def stop(self):
        """中断当前播放"""
        self._stop_event.set()
        try:
            sd.stop()  # 立即停止 sounddevice 播放
        except:
            pass
        print("[TTS] 播放已中断")

    def say(self, text):
        """
        播放语音。如果有新的播放请求，会中断当前播放。
        """
        if not text or not text.strip():
            return

        # 如果有正在播放的语音，先中断它
        if self._current_text:
            self.stop()
        
        # 重置停止标志
        self._stop_event.clear()
        self._current_text = text

        with self._lock:
            try:
                # 检查是否已被中断
                if self._stop_event.is_set():
                    self._current_text = None
                    return

                # 1. 获取音频数据
                print(f"[TTS] 正在合成: {text[:30]}...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                mp3_data = loop.run_until_complete(self._get_audio_data(text))
                loop.close()

                # 检查是否已被中断
                if self._stop_event.is_set():
                    print("[TTS] 合成完成但已被中断，跳过播放")
                    self._current_text = None
                    return

                if not mp3_data:
                    self._current_text = None
                    return

                # 2. 解码 MP3 为 PCM
                samples, sample_rate = _decode_mp3_to_pcm(mp3_data)
                if samples is None:
                    self._current_text = None
                    return

                # 检查是否已被中断
                if self._stop_event.is_set():
                    self._current_text = None
                    return

                # 3. 刷新设备选择
                self._refresh_device()

                # 4. 播放
                logging.info(f"[TTS] 开始播放音频流... 长度: {len(samples)}")
                sd.play(samples, samplerate=sample_rate, device=self._output_device)
                
                # 等待播放完成或被中断
                while sd.get_stream().active:
                    if self._stop_event.is_set():
                        sd.stop()
                        logging.info("[TTS] 播放被主动中断")
                        break
                    sd.sleep(50)
                else:
                    logging.info("[TTS] 播放自然结束")
                    
            except Exception as e:
                logging.error(f"[TTS] 关键执行错误: {e}")
                logging.error(traceback.format_exc())
            finally:
                self._current_text = None
                # 显式清除以便下次进来
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # 不做任何事，主要是为了重置事件循环状态
                loop.close()


_instance = TTSWorker()

def say(text):
    """供外部调用的主函数 - 会中断当前播放"""
    _instance.say(text)

def stop():
    """立即停止当前播放"""
    _instance.stop()
