import os
from PyQt6.QtGui import QFontDatabase

# Global Path Constants
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(_BASE_DIR, "fonts")
SERIF_FONT_PATH = os.path.join(FONT_DIR, "NotoSerifSC-Regular.otf")
SANS_FONT_PATH = os.path.join(FONT_DIR, "NotoSansSC-Regular.otf")

class FontManager:
    _serif_family = "Microsoft YaHei"
    _sans_family = "Microsoft YaHei"
    
    @classmethod
    def load_fonts(cls):
        if os.path.exists(SERIF_FONT_PATH):
            id = QFontDatabase.addApplicationFont(SERIF_FONT_PATH)
            if id != -1:
                cls._serif_family = QFontDatabase.applicationFontFamilies(id)[0]
        if os.path.exists(SANS_FONT_PATH):
            id = QFontDatabase.addApplicationFont(SANS_FONT_PATH)
            if id != -1:
                cls._sans_family = QFontDatabase.applicationFontFamilies(id)[0]

    @classmethod
    def get_font(cls, serif=True):
        return cls._serif_family if serif else cls._sans_family

    @classmethod
    def get_correct_family(cls, name):
        """Map user-friendly names to actual loaded font families"""
        if name == "思源宋体":
            return cls._serif_family
        elif name == "思源黑体":
            return cls._sans_family
        return name
