"""
设置窗口
完整的设置界面，包含所有配置选项
"""
import os
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QRadioButton, QCheckBox, QButtonGroup,
    QGroupBox, QGridLayout, QDialog, QProgressBar, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QColor, QKeySequence, QKeyEvent

from model_config import get_model_config, ASREngineType, TranslatorEngineType, ASROutputMode
from startup_manager import StartupManager
from model_downloader import get_downloader, DownloadStatus
from ui_components import HotkeyButton, ModelOptionWidget
from font_manager import FontManager
from locales import t # [New]

# 应用信息
APP_VERSION = "1.0.0"
APP_NAME = "中日说"
OFFICIAL_SITE_URL = "https://input.saaaai.com/"
AUTHOR_URL = "https://saaaai.com/"

class SettingsWindow(QDialog):
    """设置窗口"""
    
    settingsChanged = pyqtSignal()
    engineChangeRequested = pyqtSignal(str)  # 引擎切换请求
    
    def __init__(self, tr_engine, parent=None):
        super().__init__(parent)
        self.m_cfg = get_model_config()
        self.tr_engine = tr_engine
        self.downloader = get_downloader()
        
        # 拖动窗口逻辑
        self._drag_pos = None
        self._resize_edge = None  # 边缘调整大小
        self._edge_margin = 8  # 边缘调整区域宽度
        
        self._setup_ui()
        self._update_all_styles() # Apply current theme
        self._init_engine_status() # 初始化引擎显示状态

    def refresh_ui(self):
        """刷新所有文本"""
        self.setWindowTitle(t("settings_title"))
        self.title_label.setText(t("settings_title"))
        self.update_btn.setText(t("settings_check_update"))
        
        # Sections
        self.lbl_gen.setText(t("settings_section_general"))
        self.lbl_lang.setText(t("settings_lang_label"))
        self.lbl_custom.setText(t("settings_custom_placeholder"))
        self.btn_add_custom.setText(t("settings_add_text"))
        self.lbl_asr.setText(t("settings_section_asr"))
        
        # ASR Info
        self.asr_desc.setText(t("settings_asr_desc"))
        
        # Output Mode
        self.lbl_out.setText(t("settings_output_mode"))
        self.output_buttons[ASROutputMode.RAW.value].setText(t("settings_output_raw"))
        self.output_buttons[ASROutputMode.CLEANED.value].setText(t("settings_output_cleaned"))
        
        # Emoji
        self.lbl_emoji.setText(t("settings_emoji_mode"))
        from model_config import EmojiMode
        self.emoji_buttons[EmojiMode.OFF.value].setText(t("settings_emoji_off"))
        self.emoji_buttons[EmojiMode.AUTO.value].setText(t("settings_emoji_auto"))
        self.emoji_buttons[EmojiMode.TRIGGER.value].setText(t("settings_emoji_trigger"))
        self.emoji_tip.setText(t("settings_emoji_tip"))
        
        # Translate
        self.lbl_trans.setText(t("settings_section_trans"))
        
        # TTS
        self.lbl_tts.setText(t("settings_section_tts"))
        self.auto_tts_check.setText(t("settings_auto_tts"))
        self.lbl_delay.setText(t("settings_tts_delay"))
        
        # Startup
        self.lbl_start.setText(t("settings_section_startup"))
        self.mode_buttons["asr"].setText(t("settings_mode_asr"))
        self.mode_buttons["translation"].setText(t("settings_mode_translation"))
        
        # Hotkey
        self.lbl_hot.setText(t("settings_section_hotkey"))
        self.lbl_hk_asr.setText(t("settings_hotkey_asr"))
        self.lbl_hk_tog.setText(t("settings_hotkey_toggle"))
        
        # Other
        self.lbl_other.setText(t("settings_section_other"))
        self.autostart_check.setText(t("settings_autostart"))
        self.show_check.setText(t("settings_show_start"))
        self.author_btn.setText(f"{t('settings_author_link')} {AUTHOR_URL}")
        self.official_btn.setText(f"{t('settings_official_link')} {OFFICIAL_SITE_URL}")

    def _setup_ui(self):
        self.setWindowTitle(t("settings_title"))
        # 无边框窗口
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)
        
        self.setMinimumSize(480, 500)
        self.resize(650, 650)
        
        # 主容器
        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_container)
        
        # 容器内布局
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 1. 自定义标题栏 (整合进布局)
        self.title_bar = QWidget()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(45)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        self.title_label = QLabel(t("settings_title"))
        self.title_label.setObjectName("WindowTitle")
        
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_btn)
        
        container_layout.addWidget(self.title_bar)
        
        # 2. 滚动区域
        self.scroll = QScrollArea()
        self.scroll.setObjectName("MainScrollArea")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMouseTracking(True)  # 启用鼠标跟踪
        
        # 内容容器
        self.content = QWidget()
        self.content.setObjectName("ContentWidget")
        self.content.setMouseTracking(True)  # 启用鼠标跟踪
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(25, 10, 20, 25)
        self.content_layout.setSpacing(20)
        
        # 1. 更新按钮
        self.update_btn = QPushButton(t("settings_check_update"))
        self.update_btn.clicked.connect(self._check_update)
        self.content_layout.addWidget(self.update_btn)
        
        # [New] 常规设置 (语言)
        self.lbl_gen = self._add_section(t("settings_section_general"))
        
        self.lbl_lang = self._create_label(t("settings_lang_label"))
        self.content_layout.addWidget(self.lbl_lang)
        lang_layout = QHBoxLayout()
        self.lang_group, self.lang_buttons = self._create_option_group(
            [("zh", "简体中文"), ("jp", "日本語")],
            self.m_cfg.language,
            self._on_language_changed,
            horizontal=True
        )
        for btn in self.lang_buttons.values(): lang_layout.addWidget(btn)
        lang_layout.addStretch()
        self.content_layout.addLayout(lang_layout)

        # 2. 自定义默认显示文字 (Custom Idle Texts)
        self.lbl_custom = self._add_section(t("settings_custom_placeholder"))
        
        self.custom_rows_layout = QVBoxLayout()
        self.custom_rows_layout.setSpacing(10)
        self.content_layout.addLayout(self.custom_rows_layout)
        
        self.custom_rows = [] # List of (layout, edit, btn)
        
        # Get current texts
        current_texts = self.m_cfg.custom_idle_texts
        if not current_texts:
            current_texts = [t("asr_placeholder_idle"), t("menu_tip_win_ctrl"), t("app_welcome")]
        
        for txt in current_texts:
            self._add_idle_text_row(txt)
            
        self.btn_add_custom = QPushButton(t("settings_add_text"))
        self.btn_add_custom.setStyleSheet("""
            QPushButton { 
                background: #0e639c; color: white; border-radius: 4px; padding: 5px; 
                font-size: 11px; margin-top: 5px;
            }
            QPushButton:hover { background: #1177bb; }
        """)
        self.btn_add_custom.clicked.connect(lambda: self._add_idle_text_row(""))
        self.content_layout.addWidget(self.btn_add_custom)

        # 2. 语音识别
        self.lbl_asr = self._add_section(t("settings_section_asr"))
        
        # 只要简单显示当前模型状态即可，无需可点击的 Widget
        asr_status_layout = QHBoxLayout()
        asr_status_icon = QLabel("✓")
        asr_status_icon.setStyleSheet("color: #10b981; font-weight: bold; font-size: 16px;")
        
        asr_info_layout = QVBoxLayout()
        asr_name = QLabel("内置 AI 语音引擎 (Sherpa-ONNX)")
        asr_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.asr_desc = QLabel(t("settings_asr_desc"))
        self.asr_desc.setStyleSheet("color: #888888; font-size: 12px;")
        
        asr_info_layout.addWidget(asr_name)
        asr_info_layout.addWidget(self.asr_desc)
        
        asr_status_layout.addWidget(asr_status_icon)
        asr_status_layout.addLayout(asr_info_layout)
        asr_status_layout.addStretch()
        
        # 包装在一个容器中以便统一边距
        asr_container = QWidget()
        asr_container.setLayout(asr_status_layout)
        self.content_layout.addWidget(asr_container)
        
        # 3. 输出模式 (分开布局)
        self.lbl_out = self._create_label(t("settings_output_mode"))
        self.content_layout.addWidget(self.lbl_out)
        output_layout = QHBoxLayout()
        self.output_group, self.output_buttons = self._create_option_group(
            [
                (ASROutputMode.RAW.value, t("settings_output_raw")),
                (ASROutputMode.CLEANED.value, t("settings_output_cleaned")),
            ],
            self.m_cfg.asr_output_mode,
            self._on_output_mode_changed,
            horizontal=True
        )
        for btn in self.output_buttons.values(): output_layout.addWidget(btn)
        output_layout.addStretch()
        self.content_layout.addLayout(output_layout)
        
        # Emoji 模式 (单独一行)
        self.lbl_emoji = self._create_label(t("settings_emoji_mode"))
        self.content_layout.addWidget(self.lbl_emoji)
        emoji_layout = QHBoxLayout()
        from model_config import EmojiMode
        self.emoji_group, self.emoji_buttons = self._create_option_group(
            [
                (EmojiMode.OFF.value, t("settings_emoji_off")),
                (EmojiMode.AUTO.value, t("settings_emoji_auto")),
                (EmojiMode.TRIGGER.value, t("settings_emoji_trigger")),
            ],
            self.m_cfg.emoji_mode,
            self._on_emoji_mode_changed,
            horizontal=True
        )
        for btn in self.emoji_buttons.values(): emoji_layout.addWidget(btn)
        emoji_layout.addStretch()
        self.content_layout.addLayout(emoji_layout)

        # Emoji 触发词说明
        self.emoji_tip = QLabel(t("settings_emoji_tip"))
        self.emoji_tip.setStyleSheet("color: #888888; font-size: 11px; margin-left: 5px; line-height: 1.4;")
        self.emoji_tip.setWordWrap(True)
        self.content_layout.addWidget(self.emoji_tip)

        # 4. 翻译引擎
        self.lbl_trans = self._add_section(t("settings_section_trans"))
        
        from ui_components import TranslatorSelectorWidget
        self.tr_selector = TranslatorSelectorWidget(self.tr_engine)
        self.tr_selector.engineChangeRequested.connect(self.engineChangeRequested.emit)
        self.content_layout.addWidget(self.tr_selector)
        
        # 5. 语音合成
        self.lbl_tts = self._add_section(t("settings_section_tts"))
        
        self.auto_tts_check = QCheckBox(t("settings_auto_tts"))
        self.auto_tts_check.setChecked(self.m_cfg.auto_tts)
        self.auto_tts_check.stateChanged.connect(self._on_auto_tts_changed)
        self.content_layout.addWidget(self.auto_tts_check)
        
        self.lbl_delay = self._create_label(t("settings_tts_delay"))
        self.content_layout.addWidget(self.lbl_delay)
        delay_layout = QHBoxLayout()
        delays = [(0, "0s"), (1000, "1s"), (3000, "3s"), (5000, "5s"), (7000, "7s")]
        self.delay_group, self.delay_buttons = self._create_option_group(
            delays,
            self.m_cfg.tts_delay_ms,
            self._on_delay_changed,
            horizontal=True
        )
        for btn in self.delay_buttons.values(): delay_layout.addWidget(btn)
        delay_layout.addStretch()
        self.content_layout.addLayout(delay_layout)
        
        # 6. 默认启动模式
        self.lbl_start = self._add_section(t("settings_section_startup"))
        mode_select_layout = QHBoxLayout()
        modes = [
            ("asr", t("settings_mode_asr")), 
            ("translation", t("settings_mode_translation"))
        ]
        self.mode_group, self.mode_buttons = self._create_option_group(
            modes,
            self.m_cfg.app_mode,
            self._on_mode_changed,
            horizontal=True
        )
        for btn in self.mode_buttons.values(): mode_select_layout.addWidget(btn)
        mode_select_layout.addStretch()
        self.content_layout.addLayout(mode_select_layout)
        
        # 7. 快捷键
        self.lbl_hot = self._add_section(t("settings_section_hotkey"))
        
        # 语音输入
        asr_hotkey_layout = QHBoxLayout()
        self.lbl_hk_asr = QLabel(t("settings_hotkey_asr"))
        asr_hotkey_layout.addWidget(self.lbl_hk_asr)
        asr_hotkey_layout.addStretch()
        asr_key_lbl = QLabel(self.m_cfg.hotkey_asr.upper().replace("+", " + "))
        asr_key_lbl.setObjectName("HotkeyDisplay")
        asr_hotkey_layout.addWidget(asr_key_lbl)
        self.content_layout.addLayout(asr_hotkey_layout)
        
        # 显示/隐藏
        toggle_hotkey_layout = QHBoxLayout()
        self.lbl_hk_tog = QLabel(t("settings_hotkey_toggle"))
        toggle_hotkey_layout.addWidget(self.lbl_hk_tog)
        toggle_hotkey_layout.addStretch()
        toggle_key_lbl = QLabel(self.m_cfg.hotkey_toggle_ui.upper().replace("+", " + "))
        toggle_key_lbl.setObjectName("HotkeyDisplay")
        toggle_hotkey_layout.addWidget(toggle_key_lbl)
        self.content_layout.addLayout(toggle_hotkey_layout)
        
        # 8. 启动与关于
        self.lbl_other = self._add_section(t("settings_section_other"))
        
        self.autostart_check = QCheckBox(t("settings_autostart"))
        self.autostart_check.setChecked(StartupManager.is_enabled())
        self.autostart_check.stateChanged.connect(self._on_autostart_changed)
        self.content_layout.addWidget(self.autostart_check)
        
        self.show_check = QCheckBox(t("settings_show_start"))
        self.show_check.setChecked(self.m_cfg.get_show_on_start())
        self.show_check.stateChanged.connect(self._on_show_start_changed)
        self.content_layout.addWidget(self.show_check)
        
        self.author_btn = QPushButton(f"{t('settings_author_link')} {AUTHOR_URL}")
        self.author_btn.setFlat(True)
        self.author_btn.clicked.connect(lambda: webbrowser.open(AUTHOR_URL))
        self.content_layout.addWidget(self.author_btn)

        self.official_btn = QPushButton(f"{t('settings_official_link')} {OFFICIAL_SITE_URL}")
        self.official_btn.setFlat(True)
        self.official_btn.clicked.connect(lambda: webbrowser.open(OFFICIAL_SITE_URL))
        self.official_btn.clicked.connect(lambda: webbrowser.open(OFFICIAL_SITE_URL))
        self.content_layout.addWidget(self.official_btn)

        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        container_layout.addWidget(self.scroll)

    # === 样式管理 ===
    
    def _update_all_styles(self):
        is_light = self.m_cfg.theme_mode == "Light"
        
        # Premium Palette
        if is_light:
            bg_color = "#ffffff"
            text_color = "#111827"
            sub_text = "#4b5563"
            border_color = "#e5e7eb"
            accent = "#0078d4" # Premium Blue
            item_bg = "#f9fafb"
            title_color = "#111827"
            title_bg = "#f3f4f6"
            label_color = "#6b7280"
        else:
            bg_color = "#1e1e1e"
            text_color = "#cccccc"
            sub_text = "#aaaaaa"
            border_color = "#3d3d3d"
            accent = "#0e639c"
            item_bg = "#2d2d2d"
            title_color = "#ffffff"
            title_bg = "transparent"
            label_color = "#aaaaaa"
            
        # 显式创建并设置 QFont 对象，增强兼容性
        font_family = FontManager.get_correct_family(self.m_cfg.font_name)
        font = QFont(font_family)
        self.setFont(font)
        
        style = f"""
            QDialog {{ background: transparent; }}
            
            #MainContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
            }}
            
            #TitleBar {{
                background-color: {bg_color};
            }}
            
            #WindowTitle {{
                color: {title_color};
                font-size: 14px;
                font-weight: bold;
                background-color: {bg_color};
            }}
            
            #CloseButton {{
                background-color: {bg_color};
                color: {sub_text};
                font-size: 20px;
                border: none;
            }}
            #CloseButton:hover {{
                background-color: #e81123;
                color: white;
            }}
            
            #MainScrollArea {{ 
                border: none; 
                background-color: {bg_color}; 
            }}
            #ContentWidget {{ 
                background-color: {bg_color}; 
            }}
            
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 4px 2px 4px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {border_color};
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {accent};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
            
            QCheckBox {{ color: {text_color}; spacing: 8px; font-size: 13px; background: transparent; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {border_color}; border-radius: 4px; background: {item_bg}; }}
            QCheckBox::indicator:checked {{ background: {accent}; border: 2px solid {accent}; }}
            
            QRadioButton {{ color: {text_color}; spacing: 8px; font-size: 13px; background: transparent; }}
            QRadioButton::indicator {{ width: 18px; height: 18px; border: 2px solid {border_color}; border-radius: 10px; background: {item_bg}; }}
            QRadioButton::indicator:checked {{ background: {accent}; border: 2px solid {accent}; }}
            
            QLabel {{ color: {text_color}; background: transparent; }}
            
            QLabel#SectionTitle {{
                color: {title_color};
                font-size: 14px;
                font-weight: 800;
                font-family: '{font_family}', 'Segoe UI', system-ui, sans-serif;
                border-left: 4px solid {accent};
                padding: 4px 12px;
                background-color: {title_bg};
                border-radius: 2px;
            }}
            
            QLabel#SectionLabel {{
                color: {label_color}; 
                font-size: 12px; 
                font-weight: 600; 
                font-family: '{font_family}', 'Segoe UI', system-ui, sans-serif; 
                margin-top: 8px; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;
            }}

            QPushButton[flat="true"] {{ color: {accent}; text-align: left; border: none; background: transparent; font-weight: bold; }}
            QPushButton {{ font-family: '{font_family}', 'Segoe UI', system-ui, sans-serif; }}
            
            QLabel#HotkeyDisplay {{
                background-color: {item_bg};
                color: {accent};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 4px 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: bold;
                font-size: 12px;
            }}
        """
        self.setStyleSheet(style)
        
        # 更新特殊的按钮组样式
        for btn in self.output_buttons.values(): self._update_btn_style(btn, is_light)
        for btn in self.delay_buttons.values(): self._update_btn_style(btn, is_light)
        for btn in self.mode_buttons.values(): self._update_btn_style(btn, is_light)
        for btn in self.lang_buttons.values(): self._update_btn_style(btn, is_light)
        # for btn in self.theme_buttons.values(): self._update_btn_style(btn, is_light)
        # for btn in self.scale_buttons.values(): self._update_btn_style(btn, is_light)
        # for btn in self.font_buttons.values(): self._update_btn_style(btn, is_light)
        
        # 更新自定义组件的主题
        # self.asr_item.update_theme(is_light) # 已移除对象
        self.tr_selector.update_theme(is_light)
        # self.hotkey_asr_btn.update_theme(is_light)
        # self.hotkey_toggle_btn.update_theme(is_light)
        self.update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#0078d4" if is_light else "#0e639c"};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                font-family: '{font_family}';
            }}
            QPushButton:hover {{
                background-color: {"#106ebe" if is_light else "#1177bb"};
            }}
        """)

    def _update_btn_style(self, btn, is_light):
        checked = btn.isChecked()
        accent_color = "#0078d4" if is_light else "#0e639c"
        if is_light:
            btn_bg = "#ffffff"
            btn_hover = "#f9fafb"
            border = "#e5e7eb"
            text = "#4b5563"
            checked_bg = accent_color
            checked_fg = "white"
            checked_bd = accent_color
        else:
            btn_bg = "#2d2d2d"
            btn_hover = "#3d3d3d"
            border = "#3d3d3d"
            text = "#cccccc"
            checked_bg = accent_color
            checked_fg = "white"
            checked_bd = accent_color
        
        if checked:
            bg = checked_bg
            fg = checked_fg
            bd = checked_bd
        else:
            bg = btn_bg
            fg = text
            bd = border
            
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {bd};
                padding: 6px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-family: '{FontManager.get_correct_family(self.m_cfg.font_name)}', 'Segoe UI', system-ui, sans-serif;
            }}
            QPushButton:hover {{
                background-color: {checked_bg if checked else btn_hover};
                border-color: {checked_bd if checked else accent_color if is_light else "#555555"};
            }}
        """)

    def _add_section(self, title):
        self.content_layout.addSpacing(15)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        self.content_layout.addWidget(label)
        return label

    def _create_label(self, text):
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

    def _create_option_group(self, options, current_value, callback, horizontal=False):
        group = QButtonGroup(self)
        buttons = {}
        
        # 定义通用处理函数，确保所有相关按钮样式都更新
        def on_toggled(checked, btn_ref, val_ref):
            # 获取最新的主题状态
            is_light = self.m_cfg.theme_mode == "Light"
            # 更新该按钮样式
            self._update_btn_style(btn_ref, is_light)
            # 如果是选中状态，触发回调
            if checked:
                callback(val_ref)

        for val, label in options:
            btn = QPushButton(label)
            btn.setCheckable(True)
            # 处理浮点数比较精度问题
            if isinstance(val, float) and isinstance(current_value, float):
                is_checked = abs(val - current_value) < 0.001
            else:
                is_checked = (val == current_value)
                
            btn.setChecked(is_checked)
            # 初始样式
            self._update_btn_style(btn, self.m_cfg.theme_mode == "Light")
            
            # 连接信号 使用默认参数绑定变量
            btn.toggled.connect(lambda c, b=btn, v=val: on_toggled(c, b, v))
            
            group.addButton(btn)
            buttons[val] = btn
        
        return group, buttons

    # === 信号处理 ===
    def _on_asr_engine_changed(self, val):
        pass # 单选项，暂不需要操作
        
    def _on_output_mode_changed(self, val):
        self.m_cfg.asr_output_mode = val
        self.m_cfg.save_config()

    def _on_language_changed(self, val):
        self.m_cfg.language = val
        self.refresh_ui()
        self.settingsChanged.emit() # 可能会通知其他窗口更新

    def _on_emoji_mode_changed(self, val):
        self.m_cfg.emoji_mode = val
        self.m_cfg.save_config()
        
    def on_engine_loaded(self, status: str):
        """引擎加载完成或状态变更的回调"""
        self.tr_selector.update_engine_status(status)

    def _init_engine_status(self):
        """初始化面板时同步引擎状态"""
        self.tr_selector.sync_status()

    def _on_auto_tts_changed(self, state):
        self.m_cfg.auto_tts = bool(state)
        self.m_cfg.save_config()
        self.settingsChanged.emit()

    def _on_delay_changed(self, val):
        self.m_cfg.tts_delay_ms = val
        self.m_cfg.save_config()
        
    def _on_mode_changed(self, val):
        self.m_cfg.app_mode = val
        self.m_cfg.save_config()
        self.settingsChanged.emit()
        
    def _on_theme_changed(self, val):
        self.m_cfg.theme_mode = val
        self.m_cfg.save_config()
        self._update_all_styles()
        self.settingsChanged.emit()
        
    def _on_scale_changed(self, val):
        self.m_cfg.window_scale = val
        self.m_cfg.save_config()
        self.settingsChanged.emit()
        
    def _on_font_changed(self, val):
        self.m_cfg.font_name = val
        self.m_cfg.save_config()
        self._update_all_styles() # 立即更新本窗口字体
        self.settingsChanged.emit()
        
    def _on_hotkey_changed(self, type_, val):
        if type_ == "asr":
            self.m_cfg.hotkey_asr = val
        else:
            self.m_cfg.hotkey_toggle_ui = val
        self.m_cfg.save_config()
        self.settingsChanged.emit()

    def _on_personality_changed(self, val):
        self.m_cfg.set_personality_scheme(val)
        self.m_cfg.save_config()

    def _on_autostart_changed(self, state):
        StartupManager.set_enabled(bool(state))
        
    def _on_show_start_changed(self, state):
        self.m_cfg.set_show_on_start(bool(state))
        
    def _check_update(self):
        import webbrowser
        webbrowser.open(OFFICIAL_SITE_URL)

    def _on_custom_text_changed(self):
        """保存自定义文案"""
        new_texts = [row[1].text() for row in self.custom_rows if row[1].text().strip()]
        if not new_texts:
            new_texts = [t("asr_placeholder_idle")] # Prevent empty list
        self.m_cfg.custom_idle_texts = new_texts
        self.m_cfg.save_config()
        self.settingsChanged.emit() # Notify ASRModeWindow

    def _add_idle_text_row(self, text=""):
        """添加一行文案输入"""
        layout = QHBoxLayout()
        edit = QLineEdit(text)
        edit.setMaxLength(10)
        edit.setPlaceholderText("请输入闲置提示词...")
        edit.editingFinished.connect(self._on_custom_text_changed)
        
        btn_del = QPushButton("×")
        btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet("""
            QPushButton { border: none; color: #ff4d4d; font-size: 16px; font-weight: bold; background: transparent; }
            QPushButton:hover { color: #ff0000; background: rgba(255,0,0,0.1); border-radius: 4px; }
        """)
        
        row_data = (layout, edit, btn_del)
        btn_del.clicked.connect(lambda: self._remove_idle_text_row(row_data))
        
        layout.addWidget(edit, 1)
        layout.addWidget(btn_del)
        self.custom_rows_layout.addLayout(layout)
        self.custom_rows.append(row_data)

    def _remove_idle_text_row(self, row_data):
        """移除一行并保存"""
        if len(self.custom_rows) <= 1:
            return # Keep at least one
        
        layout, edit, btn = row_data
        # Remove from UI
        edit.deleteLater()
        btn.deleteLater()
        layout.deleteLater()
        self.custom_rows.remove(row_data)
        self._on_custom_text_changed()

    # --- 窗口拖动与调整大小实现 ---
    def _get_resize_edge(self, pos):
        """ 检测鼠标是否在边缘调整区域 """
        m = self._edge_margin
        rect = self.rect()
        x, y = pos.x(), pos.y()
        edge = ""
        if y < m: edge += "N"
        elif y > rect.height() - m: edge += "S"
        if x < m: edge += "W"
        elif x > rect.width() - m: edge += "E"
        return edge if edge else None
    
    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._resize_edge = None
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._resize_edge = edge
                self._drag_pos = event.globalPosition().toPoint()
            else:
                self._resize_edge = None
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not event.buttons():
            # 更新鼠标样式
            edge = self._get_resize_edge(event.pos())
            if edge in ("N", "S"): self.setCursor(Qt.CursorShape.SizeVerCursor)
            elif edge in ("E", "W"): self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif edge in ("NE", "SW"): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif edge in ("NW", "SE"): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else: self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._resize_edge and self._drag_pos:
                # 调整大小
                delta = event.globalPosition().toPoint() - self._drag_pos
                self._drag_pos = event.globalPosition().toPoint()
                geo = self.geometry()
                min_w, min_h = self.minimumWidth(), self.minimumHeight()
                
                if "E" in self._resize_edge:
                    geo.setWidth(max(min_w, geo.width() + delta.x()))
                if "S" in self._resize_edge:
                    geo.setHeight(max(min_h, geo.height() + delta.y()))
                if "W" in self._resize_edge:
                    new_w = max(min_w, geo.width() - delta.x())
                    if new_w != geo.width():
                        geo.setLeft(geo.left() + (geo.width() - new_w))
                        geo.setWidth(new_w)
                if "N" in self._resize_edge:
                    new_h = max(min_h, geo.height() - delta.y())
                    if new_h != geo.height():
                        geo.setTop(geo.top() + (geo.height() - new_h))
                        geo.setHeight(new_h)
                
                self.setGeometry(geo)
            elif self._drag_pos is not None:
                # 拖动窗口
                self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_edge = None
