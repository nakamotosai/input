import sys
import threading
import time
from typing import Optional, Set, Callable
import win32gui

class SystemHandler:
    def __init__(self):
        self._last_active_window = None
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._my_window_hwnds: Set[int] = set()  # 支持多个窗口句柄
        self._tracking_started = False
        self._pending_paste_text = None  # 等待粘贴的文本
        self._pending_paste_callback = None  # 粘贴完成后的回调

    def add_my_window_handle(self, hwnd):
        """Register an application window handle to ignore during tracking."""
        if hwnd:
            self._my_window_hwnds.add(int(hwnd))

    def set_my_window_handle(self, hwnd):
        """Legacy method - adds a window handle."""
        self.add_my_window_handle(hwnd)

    def start_focus_tracking(self):
        """Start a background thread to track the actively focused window."""
        if self._tracking_started:
            return  # 防止重复启动
        self._tracking_started = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._track_focus_loop, daemon=True)
        self._monitor_thread.start()

    def stop_focus_tracking(self):
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join()
        self._tracking_started = False

    def _track_focus_loop(self):
        while not self._stop_event.is_set():
            hwnd = win32gui.GetForegroundWindow()
            # 只有当焦点窗口不是我们自己的任何窗口时才记录
            if hwnd and hwnd not in self._my_window_hwnds:
                # 如果有等待粘贴的文本，且检测到新的外部窗口获得焦点
                if self._pending_paste_text:
                    text = self._pending_paste_text
                    self._pending_paste_text = None  # 清除，防止重复粘贴
                    time.sleep(0.2)  # 等待窗口完全激活
                    self._do_paste(text, should_send=False)
                    if self._pending_paste_callback:
                        try:
                            self._pending_paste_callback()
                        except:
                            pass
                        self._pending_paste_callback = None
                
                self._last_active_window = hwnd
            time.sleep(0.1)

    def get_last_active_window(self) -> Optional[int]:
        return self._last_active_window

    def has_target_window(self) -> bool:
        """检查是否有有效的目标窗口"""
        return self._last_active_window is not None and win32gui.IsWindow(self._last_active_window)

    def restore_focus_to_last_window(self) -> bool:
        """Switch focus back to the last separate application window. Returns True if successful."""
        if self._last_active_window and win32gui.IsWindow(self._last_active_window):
            try:
                win32gui.SetForegroundWindow(self._last_active_window)
                return True
            except Exception as e:
                print(f"Failed to restore focus: {e}")
        return False

    def set_pending_paste(self, text: str, callback: Callable = None):
        """设置等待粘贴的文本，当下一个外部窗口获得焦点时自动粘贴"""
        self._pending_paste_text = text
        self._pending_paste_callback = callback

    def clear_pending_paste(self):
        """清除等待粘贴的文本"""
        self._pending_paste_text = None
        self._pending_paste_callback = None

    def copy_to_clipboard(self, text: str):
        """只复制文本到剪贴板，不粘贴"""
        if not text: return
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception as e:
            print(f"Copy error: {e}")

    def _do_paste(self, text, should_send=False):
        """执行粘贴操作"""
        try:
            import pyperclip
            from pynput.keyboard import Controller, Key
            pyperclip.copy(text)
            time.sleep(0.05)
            keyboard = Controller()
            with keyboard.pressed(Key.ctrl):
                keyboard.press('v')
                keyboard.release('v')
            
            if should_send:
                time.sleep(0.05)
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)
        except Exception as e:
            print(f"Paste error: {e}")

    def paste_text(self, text, should_send=False):
        if not text: return
        try:
            import pyperclip
            from pynput.keyboard import Controller, Key
            pyperclip.copy(text)
            self.restore_focus_to_last_window()
            time.sleep(0.1)
            keyboard = Controller()
            with keyboard.pressed(Key.ctrl):
                keyboard.press('v')
                keyboard.release('v')
            
            if should_send:
                # 仅在需要时（文字翻译模式）发送 Enter 键
                time.sleep(0.05)
                keyboard.press(Key.enter)
                keyboard.release(Key.enter)
        except Exception as e:
            print(f"Paste error: {e}")
