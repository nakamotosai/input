"""
多语言支持模块
提供中文(zh)和日文(jp)的文本资源
"""
from model_config import get_model_config

# 翻译字典
# key: (zh_text, jp_text)
# 为了方便开发，这里使用简单的键值对，实际使用时可以通过 key 来索引
TRANSLATIONS = {
    # --- 通用 ---
    "app_name": {
        "zh": "中日说",
        "jp": "日中トーク"
    },
    "confirm": {
        "zh": "确定",
        "jp": "OK"
    },
    "cancel": {
        "zh": "取消",
        "jp": "キャンセル"
    },
    "loading": {
        "zh": "加载中...",
        "jp": "読み込み中..."
    },
    "ready": {
        "zh": "就绪",
        "jp": "準備完了"
    },
    "error": {
        "zh": "错误",
        "jp": "エラー"
    },
    
    # --- 首次启动向导 setup_wizard.py ---
    "wizard_title": {
        "zh": "中日说 - 初始化向导",
        "jp": "日中トーク - 初期設定"
    },
    "wizard_prev": {
        "zh": "上一步",
        "jp": "戻る"
    },
    "wizard_next": {
        "zh": "下一步",
        "jp": "次へ"
    },
    "wizard_start": {
        "zh": "开始使用",
        "jp": "始める"
    },
    "wizard_welcome_title": {
        "zh": "欢迎使用 中日说",
        "jp": "日中トークへようこそ"
    },
    "wizard_welcome_desc": {
        "zh": "这是一款基于 AI 的日语语音输入与实时翻译工具。\n\n在开始之前，我们需要下载一些必要的 AI 模型组件。\n这些模型将运行在您的本地电脑上，确保隐私安全和低延迟。\n\n请点击“下一步”继续。",
        "jp": "本ソフトは、AI ベースの音声入力およびリアルタイム翻訳ツールです。\n\n開始する前に、必要な AI モデルコンポーネントをダウンロードする必要があります。\nこれらのモデルはローカル PC 上で動作し、プライバシーの保護と低遅延を保証します。\n\n「次へ」をクリックして続行してください。"
    },
    "wizard_model_title": {
        "zh": "下载核心组件",
        "jp": "コアコンポーネントのダウンロード"
    },
    "wizard_model_desc": {
        "zh": "以下模型是程序运行所必须的，请确保下载安装完成。",
        "jp": "以下のモデルはプログラムの実行に必須です。ダウンロードとインストールを完了してください。"
    },
    "wizard_model_hint": {
        "zh": "提示: 如果下载速度较慢，请检查网络连接。支持断点续传。",
        "jp": "ヒント: ダウンロード速度が遅い場合は、ネットワーク接続を確認してください。レジューム機能をサポートしています。"
    },
    "wizard_finish_title": {
        "zh": "准备就绪",
        "jp": "準備完了"
    },
    "wizard_finish_desc": {
        "zh": "初始设置已完成！\n\n您可以通过托盘图标右键菜单进入「详细设置」调整更多选项，\n如更换翻译模型、修改快捷键或界面主题。\n\n默认快捷键：\n• 语音输入: Ctrl + Win (按住说话)\n• 显示/隐藏: Alt + Win",
        "jp": "初期設定が完了しました！\n\nトレイアイコンの右クリックメニューから「詳細設定」に入り、\n翻訳モデルの変更、ショートカットキー、テーマなどを調整できます。\n\nデフォルトのショートカットキー：\n• 音声入力: Ctrl + Win (長押しして話す)\n• 表示/非表示: Alt + Win"
    },

    # --- 设置窗口 settings_window.py ---
    "settings_title": {
        "zh": "设置",
        "jp": "設定"
    },
    "settings_check_update": {
        "zh": "检查版本更新",
        "jp": "アップデートを確認"
    },
    "settings_section_general": { # New section for language
        "zh": "常规设置",
        "jp": "一般設定"
    },
    "settings_lang_label": {
        "zh": "界面语言 / Language",
        "jp": "表示言語 / Language"
    },
    "settings_section_asr": {
        "zh": "语音识别",
        "jp": "音声認識"
    },
    "settings_asr_desc": {
        "zh": "高性能离线识别，支持中/英/日/韩/粤语，内置智能标点",
        "jp": "高性能オフライン認識、中/英/日/韓/広東語対応、スマート句読点内蔵"
    },
    "settings_output_mode": {
        "zh": "输出模式",
        "jp": "出力モード"
    },
    "settings_output_raw": {
        "zh": "原始输出",
        "jp": "そのまま出力"
    },
    "settings_output_cleaned": {
        "zh": "正则表达",
        "jp": "正規表現"
    },
    "settings_emoji_mode": {
        "zh": "Emoji 模式",
        "jp": "絵文字モード"
    },
    "settings_emoji_off": {
        "zh": "关闭",
        "jp": "オフ"
    },
    "settings_emoji_auto": {
        "zh": "自动(默认😂)",
        "jp": "自動(デフォルト😂)"
    },
    "settings_emoji_trigger": {
        "zh": "语音触发",
        "jp": "音声トリガー"
    },
    "settings_emoji_tip": {
        "zh": "<b>💡 语音触发使用说明：</b><br>在每句话最后说出关键词即可触发：<br>笑哭、哈哈、开心、点赞、星星、爱心、疑问、生气、流泪、鼓掌、庆祝、合十、加油、滑稽、思考",
        "jp": "<b>💡 音声トリガーの使用方法：</b><br>文末にキーワードを言うとトリガーされます（中国語のみ）：<br>笑哭、哈哈、开心、点赞、星星、爱心、疑问、生气、流泪、鼓掌、庆祝、合十、加油、滑稽、思考"
    },
    "settings_section_trans": {
        "zh": "翻译引擎",
        "jp": "翻訳エンジン"
    },
    "settings_section_tts": {
        "zh": "语音合成",
        "jp": "音声合成"
    },
    "settings_auto_tts": {
        "zh": "翻译后自动朗读日语（需联网）",
        "jp": "翻訳後に日本語を自動読み上げ（要ネット）"
    },
    "settings_tts_delay": {
        "zh": "朗读延迟 (如果被hands-free影响请选5秒)",
        "jp": "読み上げ遅延 (ハンズフリーに影響する場合は5秒を選択)"
    },
    "settings_section_startup": {
        "zh": "默认启动模式",
        "jp": "デフォルト起動モード"
    },
    "settings_mode_asr": {
        "zh": "中文直出",
        "jp": "中→中(ASR)"
    },
    "settings_mode_asr_jp": {
        "zh": "日文直出",
        "jp": "日→日(ASR)"
    },
    "settings_mode_translation": {
        "zh": "中日双显",
        "jp": "中→日(翻訳)"
    },
    "settings_section_hotkey": {
        "zh": "快捷键",
        "jp": "ショートカット"
    },
    "settings_hotkey_asr": {
        "zh": "语音输入 (按住)",
        "jp": "音声入力 (長押し)"
    },
    "settings_hotkey_toggle": {
        "zh": "显示 / 隐藏窗口",
        "jp": "ウィンドウ表示切替"
    },
    "settings_section_other": {
        "zh": "其他",
        "jp": "その他"
    },
    "settings_autostart": {
        "zh": "开机自动启动",
        "jp": "PC起動時に自動実行"
    },
    "settings_show_start": {
        "zh": "启动时显示主窗口",
        "jp": "起動時にメインウィンドウを表示"
    },
    "settings_author_link": {
        "zh": "作者个人主页",
        "jp": "作者ホームページ"
    },
    "settings_official_link": {
        "zh": "中日说官方主页",
        "jp": "公式サイト"
    },
    "settings_custom_placeholder": {
        "zh": "自定义默认显示文字",
        "jp": "待機テキストのカスタマイズ"
    },
    "settings_add_text": {
        "zh": "添加文案",
        "jp": "テキストを追加"
    },
    "settings_delete": {
        "zh": "删除",
        "jp": "削除"
    },

    # --- 右键菜单 ui_manager.py ---
    "menu_opacity": {
        "zh": "透明度",
        "jp": "不透明度"
    },
    "menu_settings": {
        "zh": "详细设置面板",
        "jp": "詳細設定パネル"
    },
    "menu_mode_asr": {
        "zh": "中文识别模式",
        "jp": "中国語認識モード"
    },
    "menu_mode_trans": {
        "zh": "中日双显模式",
        "jp": "中日翻訳モード"
    },
    "menu_theme_dark": {
        "zh": "深色主题",
        "jp": "ダークテーマ"
    },
    "menu_theme_light": {
        "zh": "浅色主题",
        "jp": "ライトテーマ"
    },
    "menu_font_song": {
        "zh": "思源宋体",
        "jp": "Source Han Serif"
    },
    "menu_font_hei": {
        "zh": "思源黑体",
        "jp": "Source Han Sans"
    },
    "menu_autostart": {
        "zh": "开机自启",
        "jp": "自動起動"
    },
    "menu_tip": {
        "zh": "快捷键提示",
        "jp": "ショートカットガイド"
    },
    "menu_restart": {
        "zh": "重启中日说",
        "jp": "再起動"
    },
    "menu_website": {
        "zh": "中日说官网",
        "jp": "公式サイト"
    },
    "menu_quit": {
        "zh": "彻底退出",
        "jp": "終了"
    },

    # --- UI 组件 ui_components.py ---
    "comp_download_ready": {
        "zh": "待安装 (点击开始)",
        "jp": "未インストール (クリックして開始)"
    },
    "comp_installed": {
        "zh": "已安装",
        "jp": "インストール済み"
    },
    "comp_downloading": {
        "zh": "准备下载...",
        "jp": "ダウンロード準備中..."
    },
    "comp_extracting": {
        "zh": "正在解压...",
        "jp": "解凍中..."
    },
    "comp_failed": {
        "zh": "下载失败",
        "jp": "失敗"
    },
    
    "trans_engine_active": {
        "zh": "当前活动引擎:",
        "jp": "現在のエンジン:"
    },
    "trans_engine_status": {
        "zh": "运行状态:",
        "jp": "ステータス:"
    },
    "trans_status_offline": {
        "zh": "离线",
        "jp": "オフライン"
    },
    "trans_status_run": {
        "zh": "运行中 (Ready)",
        "jp": "準備完了 (Ready)"
    },
    "trans_status_load": {
        "zh": "加载中 (Loading...)",
        "jp": "読み込み中..."
    },
    "trans_google": {
        "zh": "Google 在线翻译",
        "jp": "Google オンライン翻訳"
    },
    "trans_nllb": {
        "zh": "本地 AI 翻译引擎 (已暂停)",
        "jp": "ローカル AI 翻訳 (一時停止中)"
    },
    
    "tip_hotkeys": {
        "zh": "<b>快捷指令</b><br><br>• <b>Win + Ctrl</b><br>&nbsp;&nbsp;&nbsp;按住说话<br><br>• <b>Win + Alt</b><br>&nbsp;&nbsp;&nbsp;显隐窗口<br><br>• <b>界面右键</b><br>&nbsp;&nbsp;&nbsp;唤出菜单",
        "jp": "<b>ショートカット</b><br><br>• <b>Win + Ctrl</b><br>&nbsp;&nbsp;&nbsp;長押しで入力<br><br>• <b>Win + Alt</b><br>&nbsp;&nbsp;&nbsp;表示切替<br><br>• <b>右クリック</b><br>&nbsp;&nbsp;&nbsp;メニュー"
    },
    
    # --- ASR 状态 asr_mode.py ---
    "asr_placeholder_idle": {
        "zh": "按住说话",
        "jp": "長押しで話す"
    },
    "asr_listening": {
        "zh": "正在聆听...",
        "jp": "聞いています..."
    },
    
    # --- 更新管理器 update_manager.py ---
    "update_title": {
        "zh": "检查更新",
        "jp": "アップデート確認"
    },
    "update_latest": {
        "zh": "当前已是最新版本！",
        "jp": "最新バージョンです！"
    },
    "update_error": {
        "zh": "检查更新失败",
        "jp": "確認に失敗しました"
    },
    "update_new_version": {
        "zh": "发现新版本",
        "jp": "新しいバージョンがあります"
    },
    "update_release_date": {
        "zh": "发布日期",
        "jp": "公開日"
    },
    "update_changelog": {
        "zh": "更新内容",
        "jp": "更新内容"
    },
    "update_ask_download": {
        "zh": "是否前往下载？",
        "jp": "ダウンロードしますか？"
    },
    "update_btn_download": {
        "zh": "立即下载",
        "jp": "今すぐダウンロード"
    },
    "update_btn_later": {
        "zh": "稍后再说",
        "jp": "後で"
    },
    # --- 新增 ---
    "app_welcome": {
        "zh": "欢迎使用中日说",
        "jp": "日中トークへようこそ"
    },
    "menu_tip_win_ctrl": {
        "zh": "Win+Ctrl",
        "jp": "Win+Ctrl"
    },
    "translating": {
        "zh": "正在翻译...",
        "jp": "翻訳中..."
    }
}

class LocaleManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocaleManager, cls).__new__(cls)
            cls._instance.config = get_model_config()
        return cls._instance

    @property
    def lang(self):
        # 默认 zh
        return getattr(self.config, 'language', 'zh')

    def get(self, key, default=None):
        if key not in TRANSLATIONS:
            return default if default is not None else key
        
        lang_dict = TRANSLATIONS[key]
        return lang_dict.get(self.lang, lang_dict.get('zh', key))

# 全局快捷访问单例
_mgr = LocaleManager()

def t(key, default=None):
    """获取翻译文本"""
    return _mgr.get(key, default)
