import os, json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, 
    QApplication, QLabel, QPushButton, QFrame, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QIcon, QFontMetrics, QPen, QBrush, QFont

from font_manager import FontManager
from ui_manager import LOGO_PATH, HotkeyDialog, VoiceWaveform, ScaledTextEdit, ClearButton, SlotMachineLabel
from model_config import get_model_config, ASREngineType, TranslatorEngineType, ASROutputMode
from startup_manager import StartupManager
from asr_manager import ASRManager

# Default fallbacks if needed
DEFAULT_PLACEHOLDER = "说中文，出日文"
DEFAULT_LISTENING = "正在聆听..."
DEFAULT_TRANSLATING = "翻译中..."

class ASRIconButton(QPushButton):
    def __init__(self, parent=None, icon_type="mic"):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_type = icon_type
        self._is_recording = False
        self._pulse_radius = 0
        self._pulse_max = 20
        self.scale = 1.0
        self.bg_color = QColor(255, 255, 255, 25)
        self.icon_color = QColor(200, 200, 200)
        self.pulse_color = QColor(255, 60, 60, 100)
        
        self.pulse_anim = QPropertyAnimation(self, b"pulse_radius")
        self.pulse_anim.setDuration(1200)
        self.pulse_anim.setLoopCount(-1)
        self.pulse_anim.setStartValue(0)
        self.pulse_anim.setEndValue(20) 
        self.pulse_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def apply_scale(self, scale):
        self.scale = scale
        size = int(50 * scale)
        self.setFixedSize(size, size)
        self._pulse_max = 20 * scale
        self.pulse_anim.stop()
        self.pulse_anim.setEndValue(self._pulse_max)
        if self._is_recording:
            self.pulse_anim.start()
        self.update()

    def set_recording(self, recording):
        self._is_recording = recording
        if recording:
            self.pulse_anim.start()
        else:
            self.pulse_anim.stop()
            self._pulse_radius = 0
        self.update()

    def get_pulse_radius(self): return self._pulse_radius
    def set_pulse_radius(self, r): 
        self._pulse_radius = r
        self.update()
    pulse_radius = pyqtProperty(float, fget=get_pulse_radius, fset=set_pulse_radius)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        
        if self._is_recording and self.icon_type == "mic":
            painter.setPen(Qt.PenStyle.NoPen)
            alpha = int(100 * (1.0 - self._pulse_radius / self._pulse_max if self._pulse_max > 0 else 0))
            c = QColor(self.pulse_color.red(), self.pulse_color.green(), self.pulse_color.blue(), alpha)
            painter.setBrush(QBrush(c))
            r = int(self._pulse_radius + 5 * self.scale)
            painter.drawEllipse(center, r, r)
            
        painter.setPen(Qt.PenStyle.NoPen)
        if self._is_recording and self.icon_type == "mic":
            painter.setBrush(QBrush(self.pulse_color))
        else:
            painter.setBrush(QBrush(self.bg_color))
        r_inner = int(12 * self.scale)
        painter.drawEllipse(center, r_inner, r_inner)
        
        icon_c = QColor("white") if (self._is_recording and self.icon_type == "mic") else self.icon_color
        
        if self.icon_type == "clear":
            pen = QPen(icon_c, max(1, int(2 * self.scale)))
            painter.setPen(pen)
            off = int(4 * self.scale)
            painter.drawLine(center.x()-off, center.y()-off, center.x()+off, center.y()+off)
            painter.drawLine(center.x()+off, center.y()-off, center.x()-off, center.y()+off)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(icon_c))
            iw = int(6 * self.scale)
            ih = int(10 * self.scale)
            painter.drawRoundedRect(center.x()-iw//2, center.y()-int(7*self.scale), iw, ih, int(3*self.scale), int(3*self.scale))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(icon_c.red(), icon_c.green(), icon_c.blue(), 200), max(1, int(1.5*self.scale))))
            aw = int(10 * self.scale)
            ah = int(8 * self.scale)
            painter.drawArc(center.x()-aw//2, center.y()-int(3*self.scale), aw, ah, 180*16, 180*16)
            painter.drawLine(center.x(), center.y()+int(5*self.scale), center.x(), center.y()+int(7*self.scale))
            painter.drawLine(center.x()-int(3*self.scale), center.y()+int(7*self.scale), center.x()+int(3*self.scale), center.y()+int(7*self.scale))
        


class ASRJpModeWindow(QWidget):
    """Japanese ASR Mode - recognizes Chinese, translates to Japanese, displays Japanese."""
    requestSend = pyqtSignal()
    requestRecordStart = pyqtSignal()
    requestRecordStop = pyqtSignal()
    
    # Unified Menu Signals
    requestAppModeChange = pyqtSignal(str)
    requestASREngineChange = pyqtSignal(str)
    requestTranslatorEngineChange = pyqtSignal(str)
    requestASROutputModeChange = pyqtSignal(str)
    requestThemeChange = pyqtSignal(str)
    requestScaleChange = pyqtSignal(float)
    requestFontChange = pyqtSignal(str)
    requestFontSizeChange = pyqtSignal(float)
    requestQuit = pyqtSignal()
    requestAutoTTSChange = pyqtSignal(bool)
    requestTTSDelayChange = pyqtSignal(int)
    requestPersonalityChange = pyqtSignal(str)
    requestHotkeyChange = pyqtSignal(str, str)
    requestRestart = pyqtSignal()
    requestOpenSettings = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # [Fix] 确保内容始终顶部对齐

        self.container = QFrame()
        self.container.setObjectName("asr_jp_container")
        
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 0, 5, 0)
        self.container_layout.setSpacing(0)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)
        
        self.main_layout.addWidget(self.container)

        from model_config import get_model_config
        self.m_cfg = get_model_config()
        
        # Display - using ScaledTextEdit for coordinate tracking
        self.display = ScaledTextEdit(self, self.m_cfg.get_prompt("idle_jp"), "white", hide_cursor=True)
        self.display.setReadOnly(True)
        self.display.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        # self.display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # [Fix] Removed override to allow auto-centering with Fixed height
        
        # Waveform
        self.waveform = VoiceWaveform(self)
        self.waveform.setVisible(False)
        
        # Clear button - parented to container for absolute positioning
        self.clear_btn = ClearButton(self.container)
        self.clear_btn.clicked.connect(self.clear_input)
        
        self.voice_btn = ASRIconButton(self, "mic")
        self.voice_btn.pressed.connect(self.requestRecordStart.emit)
        self.voice_btn.released.connect(self.requestRecordStop.emit)

        # Slot machine label for initial animation - 默认使用灰色
        self.slot_label = SlotMachineLabel(self, "说中文，出日文", "rgba(255,255,255,0.5)")
        self.slot_label.set_character_set("jp")
        self.slot_label.setVisible(False)
        self.slot_label.animationFinished.connect(self._on_animation_finished)
        
        # Add to layout
        self.container_layout.addWidget(self.display, 1)
        self.container_layout.addWidget(self.slot_label, 1)
        self.container_layout.addWidget(self.waveform, 1)
        self.container_layout.addWidget(self.voice_btn)

        self.container.installEventFilter(self)
        self.display.installEventFilter(self)

        self.theme_mode = "Dark"
        self.window_scale = 1.0
        self.font_size_factor = 1.0
        self.current_font_name = "思源宋体"
        self._placeholder_color = "rgba(255,255,255,0.5)"
        self._text_color = "white"
        
        self.height_anim = QPropertyAnimation(self, b"geometry")
        self.height_anim.setDuration(1000) # [Task] 再次变慢，1秒
        self.height_anim.setEasingCurve(QEasingCurve.Type.OutQuart) # [Task] 使用 OutQuart 实现丝滑刹车
        
        self.base_height = 50
        self.expanded_height = 100
        self.is_expanded = False

        self._dragging = False
        self._drag_pos = None

        self.auto_clear_timer = QTimer(self)
        self.auto_clear_timer.setSingleShot(True)
        self.auto_clear_timer.setInterval(5000)
        self.auto_clear_timer.timeout.connect(self.clear_input)

        self.apply_theme()
        self._update_size()

    def apply_theme(self, theme="Dark"):
        self.theme_mode = theme
        self.m_cfg.theme_mode = theme # [Fix] Sync config state immediately
        # [Fix] 保证至少 0.01 的不透明度以防止鼠标穿透
        opacity = max(0.01, getattr(self.m_cfg, 'window_opacity', 0.95))
        
        if theme == "Light":
            bg = f"rgba(255, 255, 255, {opacity})"
            self._text_color = "#333333"
            self._placeholder_color = "rgba(0,0,0,0.4)"
        else:
            bg = f"rgba(45, 45, 45, {opacity})"
            self._text_color = "white"
            self._placeholder_color = "rgba(255,255,255,0.5)"
        
        r = int(12 * self.window_scale)
        self.container.setStyleSheet(f"""
            QFrame#asr_jp_container {{
                background-color: {bg};
                border-radius: {r}px;
                border: none;
            }}
        """)
        
        btn_bg = QColor(0,0,0,40) if theme=="Light" else QColor(255,255,255,25)
        btn_icon = QColor(100,100,100) if theme=="Light" else QColor(200,200,200)
        
        self.clear_btn.update_style(theme)
        
        self.voice_btn.bg_color = btn_bg
        self.voice_btn.icon_color = btn_icon
        self.voice_btn.update()
        self.waveform.bar_color = QColor(100, 100, 100) if theme == "Light" else QColor(200, 200, 200)
        self._update_display_style()

    def apply_scaling(self, scale, font_factor, is_serif=False):
        self.window_scale = scale
        self.m_cfg.window_scale = scale # [Fix] Sync config state
        self.font_size_factor = font_factor
        self.voice_btn.apply_scale(scale)
        self.clear_btn.apply_scale(scale)
        self.slot_label.apply_scale(scale, font_factor=font_factor)
        self._update_display_style()
        self._update_size()
        self.apply_theme(self.theme_mode) # Update border radius

    def change_theme(self, theme): self.apply_theme(theme)
    def set_font_name(self, name): 
        self.current_font_name = name
        self._update_display_style()
    def set_scale_factor(self, scale):
        self.apply_scaling(scale, self.font_size_factor)

    def _update_display_style(self):
        family = FontManager.get_correct_family(self.current_font_name)
        font_size = int(14 * self.font_size_factor)
        current_text = self.display.toPlainText()
        loading_msgs = [self.m_cfg.get_prompt("loading"), self.m_cfg.get_prompt("init")]
        # 增加对 "说中文，出日文" 的识别，确保它是灰色
        placeholders = ["说中文，出日文", self.m_cfg.get_prompt("idle_jp"), self.m_cfg.get_prompt("listening"), self.m_cfg.get_prompt("translating")] + loading_msgs
        is_placeholder = current_text in placeholders or current_text == ""
        
        color = self._placeholder_color if is_placeholder else self._text_color
        self.display.set_text_color(color)
        self.display.apply_scale(self.window_scale, family, self.font_size_factor)
        
        # 老虎机在此时也该用占位符颜色
        self.slot_label.set_text_color(self._placeholder_color)
        self.slot_label.apply_scale(self.window_scale, family, self.font_size_factor)

    def _needs_expansion(self, text):
        loading_msgs = [self.m_cfg.get_prompt("loading"), self.m_cfg.get_prompt("init")]
        if text in [self.m_cfg.get_prompt("idle_jp"), self.m_cfg.get_prompt("listening"), self.m_cfg.get_prompt("translating"), ""] + loading_msgs:
            return False
        font = self.display.font()
        fm = QFontMetrics(font)
        available_width = int(300 * self.window_scale) - 100
        text_width = fm.horizontalAdvance(text)
        return text_width > available_width or "\n" in text

    def _update_size(self):
        s = self.window_scale
        fixed_w = int(320 * s)
        if fixed_w < 150: fixed_w = 150
        self.setFixedWidth(fixed_w + int(50 * s))
        self.base_height = int(52 * s)
        self.expanded_height = int(100 * s)
        text = self.display.toPlainText()
        needs_expand = self._needs_expansion(text)
        if needs_expand != self.is_expanded:
            self.is_expanded = needs_expand
            target_container_h = self.expanded_height if needs_expand else self.base_height
            target_window_h = target_container_h + 50
            
            # [Fix] 如果窗口还没显示（初始化阶段），绝对不要启动动画
            # 否则动画会记录错误的 StartValue(0,0)，导致窗口出现后瞬间跳到左上角
            if not self.isVisible():
                self.resize(self.width(), target_window_h)
                self.container.setMinimumHeight(target_container_h)
                self.container.setMaximumHeight(target_container_h)
                # 更新 geometry 
                geo = self.geometry()
                geo.setHeight(target_window_h)
                self.setGeometry(geo)
                return

            try:
                self.height_anim.finished.disconnect()
            except: pass
            
            self.height_anim.stop()
            
            # [Critial Fix] 动画前解锁约束，防止瞬间跳变
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.container.setMinimumHeight(0)
            self.container.setMaximumHeight(16777215)
            
            # 使用 geometry 动画，强制保持 Top-Left 不变
            start_geo = self.geometry()
            end_geo = start_geo.adjusted(0, 0, 0, 0)
            end_geo.setHeight(target_window_h)
            
            self.height_anim.setStartValue(start_geo)
            self.height_anim.setEndValue(end_geo)
            
            def on_anim_finished():
                self.setMinimumHeight(target_window_h)
                self.setMaximumHeight(target_window_h)
                self.container.setMinimumHeight(target_container_h)
                self.container.setMaximumHeight(target_container_h)
                
            self.height_anim.finished.connect(on_anim_finished)
            self.height_anim.start()
        else:
            target_container_h = self.expanded_height if self.is_expanded else self.base_height
            target_window_h = target_container_h + 50
            
            target_geo = self.geometry()
            target_geo.setHeight(target_window_h)
            self.setGeometry(target_geo)
            
            self.setMinimumHeight(target_window_h)
            self.setMaximumHeight(target_window_h)
            self.container.setMinimumHeight(target_container_h)
            self.container.setMaximumHeight(target_container_h)

    def update_segment(self, text):
        # 如果正在进行动画，且现在有真正文本输入，强制停止动画
        if self.slot_label.isVisible():
            self.slot_label.setVisible(False)
            self.display.setVisible(True)
            
        self.display.setPlainText(text)
        self._update_display_style()
        is_real_text = text not in ["说中文，出日文", self.m_cfg.get_prompt("listening"), self.m_cfg.get_prompt("translating"), "识别中...", ""]
        self.clear_btn.setVisible(is_real_text)
        self._update_size()
        self._update_clear_btn_pos()
        if is_real_text: self.auto_clear_timer.start()
        else: self.auto_clear_timer.stop()

    def _update_clear_btn_pos(self):
        """Position X button immediately after text end"""
        if not self.display.toPlainText() or not self.clear_btn.isVisible():
            return
            
        cursor = self.display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        rect = self.display.cursorRect(cursor)
        
        viewport_pos = self.display.viewport().mapTo(self.container, rect.topRight())
        
        s = self.window_scale
        x = viewport_pos.x() + int(10 * s)
        y = viewport_pos.y() + (rect.height() - self.clear_btn.height()) // 2
        
        # Guard against mic button
        max_x = self.container.width() - int(60 * s)
        if x > max_x: x = max_x
            
        self.clear_btn.move(x, y)
        self.clear_btn.raise_()

    def show_translating(self):
        self.display.setPlainText(self.m_cfg.get_prompt("translating"))
        self._update_display_style()

    def update_status(self, status):
        # [FIX] 如果正在录音，绝对不要更新文字状态/显示占位符
        if self.waveform.isVisible():
            return

        current = self.display.toPlainText()
        if status == "idle" or "加载完成" in status or "就绪" in status:
            if self.slot_label.isVisible():
                # 加载完毕，开始逐字归位
                self.slot_label.settle_one_by_one(start_delay=300)
            elif self.m_cfg.is_placeholder_text(current):
                self.update_segment("说中文，出日文")
        elif "加载" in status or status == "loading" or status == "asr_loading":
            # [FIX] 如果当前已经有识别出的文本，不要切换回 Loading 动画
            is_real_text = current not in ["说中文，出日文", self.m_cfg.get_prompt("idle_jp"), ""] and not self.m_cfg.is_placeholder_text(current)
            if is_real_text:
                return

            # 开启老虎机动画
            self.display.setVisible(False)
            self.slot_label.setVisible(True)
            self.slot_label.start_animation()
            self._update_display_style()
            
            if ASRManager().worker.engine.is_loaded:
                QTimer.singleShot(1000, self.slot_label.settle_one_by_one)

    def clear_input(self): self.update_segment("说中文，出日文")
    def focus_input(self): self.display.setFocus()

    def update_recording_status(self, is_recording):
        self.voice_btn.set_recording(is_recording)
        self.waveform.setVisible(is_recording)
        
        if is_recording:
            # 录音开始：隐藏所有文本显示
            self.display.setVisible(False)
            self.slot_label.setVisible(False)
            self.auto_clear_timer.stop()
        else:
            # 录音结束：逻辑与 asr_mode.py 类似
            self.display.setVisible(True)
            current = self.display.toPlainText()
            if current == "识别中...": self.update_segment("")
            elif current not in [self.m_cfg.get_prompt("idle_jp"), ""]: self.auto_clear_timer.start()

            # 恢复占位符逻辑
            if not current or current in ["说中文，出日文", self.m_cfg.get_prompt("idle_jp")]:
                self.display.setVisible(False)
                self.slot_label.setVisible(True)

    def update_audio_level(self, level):
        if self.waveform.isVisible(): self.waveform.set_level(level)

    def _start_drag(self, global_pos):
        self._dragging = True
        self._drag_pos = global_pos - self.pos()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self._start_drag(e.globalPosition().toPoint())
    def mouseMoveEvent(self, e):
        # [Fix] 防粘连：如果移动时左键没按，强制停止拖动
        if not (e.buttons() & Qt.MouseButton.LeftButton):
            self._dragging = False

        if self._dragging and self._drag_pos: self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e): 
        if self._dragging:
            self._dragging = False

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                if obj not in [self.clear_btn, self.voice_btn]:
                    self._start_drag(event.globalPosition().toPoint())
                    if obj == self.display: return True
        elif event.type() == QEvent.Type.MouseMove:
            # [Fix] 防粘连保险丝
            if not (event.buttons() & Qt.MouseButton.LeftButton):
                self._dragging = False
                return False
                
            if self._dragging:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton: 
                if self._dragging:
                    self._dragging = False
        return super().eventFilter(obj, event)

    def setVisible(self, visible):
        # 只有当从隐藏变为显示时，才标记需要重置位置
        if visible and not self.isVisible():
            self._should_reset_pos = True
        super().setVisible(visible)

    def showEvent(self, event):
        super().showEvent(event)
        self._dragging = False 
        
        # [Task] 只有在真正"打开"窗口时才重置位置
        if getattr(self, '_should_reset_pos', False):
            self._should_reset_pos = False
            
            screen = QApplication.primaryScreen().geometry()
            
            # Y轴固定在屏幕上方 15% 处
            target_y = int(screen.height() * 0.15) 
            if target_y < 100: target_y = 100
            
            # X轴居中
            win_w = self.frameGeometry().width()
            target_x = (screen.width() - win_w) // 2
            
            self.move(target_x, target_y)

        # [Cleaned] 移除旧的 is_valid 及位置恢复逻辑
        pass

        self.activateWindow()
        self.raise_()
        
        # 如果当前是占位符（且不是正在识别中），执行动画
        current_text = self.display.toPlainText()
        placeholders = ["说中文，出日文", self.m_cfg.get_prompt("idle_jp")]
        if current_text in placeholders or self.m_cfg.is_placeholder_text(current_text):
            self.update_status("asr_loading")

    def contextMenuEvent(self, event):
        self.show_context_menu(event.globalPos())

    def show_context_menu(self, global_pos):
        # 使用统一的新菜单
        from ui_manager import create_context_menu
        self.activateWindow()
        self.raise_()
        menu = create_context_menu(self, self.m_cfg, self)
        menu.exec(global_pos)

    def update_background_opacity(self, opacity):
        self.m_cfg.window_opacity = opacity
        self.apply_theme(self.theme_mode)

    def _on_animation_finished(self):
        # [Fix] 如果正在录音，动画结束后绝对不要显示 display
        if self.waveform.isVisible():
            return
            
        self.slot_label.setVisible(False)
        self.display.setVisible(True)
        self.update_segment("说中文，出日文")

    def _show_hotkey_dialog(self):
        asr, toggle = self.m_cfg.hotkey_asr, self.m_cfg.hotkey_toggle_ui
        dlg = HotkeyDialog(self, asr, toggle)
        if dlg.exec():
            new_asr, new_toggle = dlg.get_values()
            if new_asr or new_toggle: self.requestHotkeyChange.emit(new_asr, new_toggle)
