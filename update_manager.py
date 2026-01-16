"""
自动更新管理器
负责检查远程版本并提示用户更新
"""
import requests
import json
from packaging import version
from PyQt6.QtWidgets import QMessageBox
from locales import t # [New]

class UpdateManager:
    CURRENT_VERSION = "1.0.0"
    # 使用 GitHub 的 raw 地址，国内用户建议使用 Gitee 镜像或 jsDelivr CDN
    VERSION_URL = "https://raw.githubusercontent.com/caisiyang/input/main/version.json"
    
    @classmethod
    def check_for_updates(cls, parent=None, silent=True):
        """
        检查更新
        :param parent: 父窗口，用于弹出提示框
        :param silent: 是否静默检查（如果无更新是否提示）
        """
        try:
            response = requests.get(cls.VERSION_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("latest_version")
                
                if version.parse(latest_version) > version.parse(cls.CURRENT_VERSION):
                    cls.show_update_dialog(data, parent)
                elif not silent:
                    QMessageBox.information(parent, t("update_title"), t("update_latest"))
        except Exception as e:
            print(f"[UpdateManager] 检查更新失败: {e}")
            if not silent:
                QMessageBox.warning(parent, t("update_title"), f"{t('update_error')}: {e}")

    @classmethod
    def show_update_dialog(cls, data, parent=None):
        """显示更新提示对话框"""
        msg = QMessageBox(parent)
        msg.setWindowTitle(t("update_new_version"))
        msg.setIcon(QMessageBox.Icon.Information)
        
        text = f"{t('update_new_version')}: {data['latest_version']}\n"
        text += f"{t('update_release_date')}: {data['release_date']}\n\n"
        text += f"{t('update_changelog')}:\n{data['changelog']}\n\n"
        text += t("update_ask_download")
        
        msg.setText(text)
        btn_download = msg.addButton(t("update_btn_download"), QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(t("update_btn_later"), QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == btn_download:
            import webbrowser
            webbrowser.open(data["download_url"])

if __name__ == "__main__":
    # 简单测试
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    UpdateManager.check_for_updates(silent=False)
