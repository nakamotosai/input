
def create_context_menu(parent_widget=None, config=None, signals_proxy=None):
    """
    通用右键菜单构建器
    parent_widget: QMenu 的父窗口
    config: ModelConfig 对象，用于读取当前状态
    signals_proxy: 包含发射信号方法的对象 (例如 TranslatorWindow 或 Main)
                   需要支持的方法: requestScaleChange, requestThemeChange, requestFontChange, requestOpenSettings, requestRestart, requestQuit
    """
    if config is None: 
        from model_config import get_model_config
        config = get_model_config()

    menu = QMenu(parent_widget)
    
    # --- 样式美化 ---
    is_light = config.theme_mode == "Light"
    menu_bg = "#ffffff" if is_light else "#2d2d2d"
    menu_fg = "#000000" if is_light else "#ffffff"
    menu_sel = "#f0f0f0" if is_light else "#3d3d3d" # 浅色选中背景
    border_col = "#e0e0e0" if is_light else "#454545"

    menu.setStyleSheet(f"""
        QMenu {{ background-color: {menu_bg}; color: {menu_fg}; border: 1px solid {border_col}; border-radius: 8px; padding: 4px; }}
        QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 4px; margin: 2px; }}
        QMenu::item:selected {{ background-color: {menu_sel}; }}
        QMenu::item:checked {{ font-weight: bold; background-color: {menu_sel}; }}
        QMenu::separator {{ height: 1px; background: {border_col}; margin: 4px 8px; }}
    """)
    
    # 标题样式 (Label)
    def make_title(text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: #888888; font-size: 11px; font-weight: bold; padding: 4px 12px;")
        wa = QWidgetAction(menu)
        wa.setDefaultWidget(lbl)
        return wa

    # === 1. 透明度滑块 (0% - 100%) ===
    # menu.addAction(make_title("背景透明度"))
    opacity_action = QWidgetAction(menu)
    opacity_widget = QWidget()
    op_layout = QHBoxLayout(opacity_widget)
    op_layout.setContentsMargins(12, 4, 12, 4)
    op_layout.setSpacing(10)
    
    op_lbl = QLabel("透明度")
    op_lbl.setStyleSheet(f"color: {menu_fg};")
    op_val = QLabel(f"{int(getattr(config, 'window_opacity', 0.95)*100)}%")
    op_val.setFixedWidth(35)
    op_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    op_val.setStyleSheet(f"color: {menu_fg}; font-weight: bold;")
    
    op_slider = QSlider(Qt.Orientation.Horizontal)
    op_slider.setRange(0, 100)
    # config 可能没有 window_opacity, 默认 0.95
    current_op = getattr(config, 'window_opacity', 0.95)
    op_slider.setValue(int(current_op * 100))
    op_slider.setFixedWidth(100)
    
    def on_op_change(v):
        op_val.setText(f"{v}%")
        f_val = v / 100.0
        config.window_opacity = f_val
        if hasattr(parent_widget, "update_background_opacity"):
            parent_widget.update_background_opacity(f_val)
        if signals_proxy and hasattr(signals_proxy, 'requestOpacityChange'): # 如果有定义这个信号
            # 虽然 TranslatorWindow 没定义 requestOpacityChange，但可以直接调用 m_cfg set
            pass

    op_slider.valueChanged.connect(on_op_change)
    # 松手保存
    op_slider.sliderReleased.connect(config.save_config)
    
    op_layout.addWidget(op_lbl)
    op_layout.addWidget(op_slider)
    op_layout.addWidget(op_val)
    opacity_action.setDefaultWidget(opacity_widget)
    menu.addAction(opacity_action)

    # === 2. 缩放滑块 ===
    scale_action = QWidgetAction(menu)
    scale_widget = QWidget()
    sc_layout = QHBoxLayout(scale_widget)
    sc_layout.setContentsMargins(12, 4, 12, 4)
    sc_layout.setSpacing(10)
    
    sc_lbl = QLabel("缩放")
    sc_lbl.setStyleSheet(f"color: {menu_fg};")
    sc_val = QLabel(f"{int(config.window_scale*100)}%")
    sc_val.setFixedWidth(35)
    sc_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    sc_val.setStyleSheet(f"color: {menu_fg}; font-weight: bold;")
    
    sc_slider = QSlider(Qt.Orientation.Horizontal)
    sc_slider.setRange(80, 150)
    sc_slider.setValue(int(config.window_scale * 100))
    sc_slider.setFixedWidth(100)
    
    def on_sc_change(v):
        sc_val.setText(f"{v}%")
        f_val = v / 100.0
        if signals_proxy:
            signals_proxy.requestScaleChange.emit(f_val)
            
    sc_slider.valueChanged.connect(on_sc_change)
    sc_slider.sliderReleased.connect(config.save_config)
    
    sc_layout.addWidget(sc_lbl)
    sc_layout.addWidget(sc_slider)
    sc_layout.addWidget(sc_val)
    scale_action.setDefaultWidget(scale_widget)
    menu.addAction(scale_action)
    
    menu.addSeparator()

    # === 3. 主题 ===
    menu.addAction(make_title("主题 / 字体"))
    
    act_dark = QAction("深色主题", menu)
    act_dark.setCheckable(True)
    act_dark.setChecked(config.theme_mode == "Dark")
    act_dark.triggered.connect(lambda: signals_proxy.requestThemeChange.emit("Dark") if signals_proxy else None)
    menu.addAction(act_dark)
    
    act_light = QAction("浅色主题", menu)
    act_light.setCheckable(True)
    act_light.setChecked(config.theme_mode == "Light")
    act_light.triggered.connect(lambda: signals_proxy.requestThemeChange.emit("Light") if signals_proxy else None)
    menu.addAction(act_light)
    
    # menu.addSeparator() # 紧凑一点

    # === 4. 字体 ===
    act_song = QAction("思源宋体", menu)
    act_song.setCheckable(True)
    act_song.setChecked(config.font_name == "思源宋体")
    act_song.triggered.connect(lambda: signals_proxy.requestFontChange.emit("思源宋体") if signals_proxy else None)
    menu.addAction(act_song)
    
    act_hei = QAction("思源黑体", menu)
    act_hei.setCheckable(True)
    act_hei.setChecked(config.font_name == "思源黑体")
    act_hei.triggered.connect(lambda: signals_proxy.requestFontChange.emit("思源黑体") if signals_proxy else None)
    menu.addAction(act_hei)

    menu.addSeparator()
    
    # === 5. 系统操作 ===
    # act_settings = QAction("更多设置...", menu)
    # act_settings.triggered.connect(lambda: signals_proxy.requestOpenSettings.emit() if signals_proxy else None)
    # menu.addAction(act_settings)
    
    act_restart = QAction("重启软件", menu)
    act_restart.triggered.connect(lambda: signals_proxy.requestRestart.emit() if signals_proxy else None)
    menu.addAction(act_restart)
    
    act_quit = QAction("彻底退出", menu)
    act_quit.triggered.connect(lambda: signals_proxy.requestQuit.emit() if signals_proxy else None)
    menu.addAction(act_quit)

    return menu
