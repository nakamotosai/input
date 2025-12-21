"""
自动更新管理器
负责检查远程版本并提示用户更新
"""
import requests
import json
from packaging import version
from PyQt6.QtWidgets import QMessageBox

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
                    QMessageBox.information(parent, "检查更新", "当前已是最新版本！")
        except Exception as e:
            print(f"[UpdateManager] 检查更新失败: {e}")
            if not silent:
                QMessageBox.warning(parent, "检查更新", f"检查更新失败: {e}")

    @classmethod
    def show_update_dialog(cls, data, parent=None):
        """显示更新提示对话框"""
        msg = QMessageBox(parent)
        msg.setWindowTitle("发现新版本")
        msg.setIcon(QMessageBox.Icon.Information)
        
        text = f"发现新版本: {data['latest_version']}\n"
        text += f"发布日期: {data['release_date']}\n\n"
        text += f"更新内容:\n{data['changelog']}\n\n"
        text += "是否前往下载？"
        
        msg.setText(text)
        btn_download = msg.addButton("立即下载", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("稍后再说", QMessageBox.ButtonRole.RejectRole)
        
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
