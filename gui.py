# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
import config
from cn2an import process_files, chinese_to_arabic
import re
from pathlib import Path
import logging
import threading
from cn2an import preview_conversions, perform_conversions
import requests
import webbrowser
from packaging import version

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{config.APP_NAME} v{config.__version__}")
        self.root.geometry("800x600")  # 设置窗口初始大小
        self.root.minsize(800, 600)  # 设置最小窗口尺寸，防止按钮被遮挡
        self.target_path = tk.StringVar()
        self.match_pattern = tk.StringVar()
        self.replace_pattern = tk.StringVar()
        self.conversion_list = []
        self.create_widgets()

    def create_widgets(self) -> None:
        """创建所有UI组件"""
        self._setup_main_window()
        self._create_path_selection_frame()
        self._create_conversion_rules_frame()
        self._create_action_buttons()
        self._create_preview_list()

    def _setup_main_window(self) -> None:
        """设置主窗口框架和标题"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建上部固定区域框架
        self.upper_frame = tk.Frame(self.main_frame)
        self.upper_frame.pack(fill=tk.X, expand=False)

        # 版本更新检查按钮
        self.check_update_btn = tk.Button(self.upper_frame, text=f"v{config.__version__}", fg="blue", cursor="hand2", command=self.check_for_updates)
        self.check_update_btn.pack(anchor=tk.NE, padx=20, pady=5)

        # 标题
        title_label = tk.Label(
            self.upper_frame, text=config.APP_NAME, font=("SimHei", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

    def _create_path_selection_frame(self) -> None:
        """创建文件夹选择区域"""
        path_frame = tk.Frame(self.upper_frame, padx=20)
        path_frame.pack(fill=tk.X)

        tk.Label(path_frame, text="目标文件夹:", font=("SimHei", 10)).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        tk.Entry(path_frame, textvariable=self.target_path).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        browse_btn = tk.Button(
            path_frame, text="浏览", command=self.browse_folder, width=10
        )
        browse_btn.pack(side=tk.LEFT, padx=(10, 0))

    def _create_conversion_rules_frame(self) -> None:
        """创建匹配/替换模式输入区域的UI组件"""
        regex_frame = tk.LabelFrame(self.upper_frame, text="自定义转换规则", padx=10, pady=10)
        regex_frame.pack(fill=tk.X, padx=20, pady=(10, 10))

        # 匹配模式
        match_frame = tk.Frame(regex_frame)
        match_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(match_frame, text="匹配模式:", font=("SimHei", 10)).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self.match_entry = tk.Entry(
            match_frame, textvariable=self.match_pattern, width=40
        )
        # 添加占位符编辑验证
        validation_cmd = (
            self.root.register(self.validate_placeholder_edit),
            "%P",
            "%i",
            "%d",
        )
        self.match_entry.config(validate="key", validatecommand=validation_cmd)
        self.match_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # 添加占位符按钮
        cn_num_btn = tk.Button(
            match_frame,
            text="{cn_num}",
            bg="#cce5ff",
            fg="#004085",
            font=("SimHei", 10, "bold"),
            command=lambda: self.add_placeholder(self.match_entry, "{cn_num}"),
        )
        cn_num_btn.pack(side=tk.LEFT, padx=(5, 5))
        tk.Label(
            match_frame, text="例如: 第{cn_num}章", fg="gray", font=("SimHei", 9)
        ).pack(side=tk.LEFT, padx=(5, 0))

        # 替换模式
        replace_frame = tk.Frame(regex_frame)
        replace_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(replace_frame, text="替换模式:", font=("SimHei", 10)).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        self.replace_entry = tk.Entry(
            replace_frame, textvariable=self.replace_pattern, width=40
        )
        # 添加占位符编辑验证
        self.replace_entry.config(validate="key", validatecommand=validation_cmd)
        self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # 添加占位符按钮
        an_num_btn = tk.Button(
            replace_frame,
            text="{an_num}",
            bg="#d1ecf1",
            fg="#0c5460",
            font=("SimHei", 10, "bold"),
            command=lambda: self.add_placeholder(self.replace_entry, "{an_num}"),
        )
        an_num_btn.pack(side=tk.LEFT, padx=(5, 5))
        tk.Label(
            replace_frame, text="例如: {an_num}", fg="gray", font=("SimHei", 9)
        ).pack(side=tk.LEFT, padx=(5, 0))

        # 占位符说明
        hint_label = tk.Label(
            regex_frame,
            text="占位符: {cn_num}=中文数字, {an_num}=阿拉伯数字",
            fg="gray",
            font=("SimHei", 9),
        )
        hint_label.pack(anchor=tk.W, pady=(5, 0))

    def _create_action_buttons(self) -> None:
        """创建底部操作按钮区域的UI组件"""
        btn_frame = tk.Frame(self.upper_frame, padx=20)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.convert_btn = tk.Button(
            btn_frame,
            text="开始转换",
            command=self.start_conversion,
            font=("SimHei", 12),
            bg="#4CAF50",
            fg="white",
            height=1,
        )
        self.convert_btn.pack(fill=tk.X)
        self.convert_btn.config(state=tk.DISABLED)

    def _create_preview_list(self) -> None:
        """创建转换预览列表区域的UI组件"""
        # 预览区域独占剩余空间
        preview_container = tk.Frame(self.main_frame)
        preview_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 预览列表框架
        list_frame = tk.LabelFrame(preview_container, text="转换清单预览", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.list_text = scrolledtext.ScrolledText(
            list_frame, wrap=tk.WORD, height=4
        )
        self.list_text.pack(fill=tk.BOTH, expand=True)
        self.list_text.config(state=tk.DISABLED)

        # 底部按钮
        confirm_frame = tk.Frame(preview_container, padx=20, pady=15)
        confirm_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.confirm_btn = tk.Button(
            confirm_frame,
            text="确认转换",
            command=self.confirm_conversion,
            font=("SimHei", 10),
            bg="#2196F3",
            fg="white",
            width=15,
        )
        self.confirm_btn.pack(side=tk.RIGHT, padx=(10, 0))
        self.confirm_btn.config(state=tk.DISABLED)

        self.cancel_btn = tk.Button(
            confirm_frame,
            text="取消",
            command=self.cancel_conversion,
            font=("SimHei", 10),
            bg="#f44336",
            fg="white",
            width=15,
        )
        self.cancel_btn.pack(side=tk.RIGHT)
        self.cancel_btn.config(state=tk.DISABLED)

    def browse_folder(self) -> None:
        try:
            folder_path = filedialog.askdirectory()
            if folder_path and Path(folder_path).is_dir():
                self.target_path.set(folder_path)
                self.convert_btn.config(state=tk.NORMAL)
                logger.info(f"已选择文件夹: {folder_path}")
            else:
                messagebox.showwarning("警告", "请选择有效的文件夹路径")
        except PermissionError:
            logger.error("没有文件夹访问权限")
            messagebox.showerror("权限错误", "无法访问所选文件夹，请检查权限")
        except Exception as e:
            logger.error(f"文件夹选择失败: {str(e)}")
            messagebox.showerror("错误", f"文件夹选择失败: {str(e)}")

    def start_conversion(self) -> None:
        folder_path = Path(self.target_path.get())
        if not folder_path.exists() or not folder_path.is_dir():
            messagebox.showerror("错误", "请选择有效的文件夹路径")
            return

        # 获取用户输入的匹配模式和替换模式
        match_pattern = self.match_pattern.get()
        replace_pattern = self.replace_pattern.get()

        # 验证正则表达式有效性
        try:
            if match_pattern:
                re.compile(match_pattern)
            if replace_pattern:
                re.compile(replace_pattern)
        except re.error as e:
            messagebox.showerror("错误", f"无效的正则表达式: {str(e)}")
            return

        # 验证模式中是否包含必要的占位符
        if "{cn_num}" not in match_pattern:
            messagebox.showwarning("警告", "匹配模式必须包含{cn_num}占位符")
            return
        if "{an_num}" not in replace_pattern:
            messagebox.showwarning("警告", "替换模式必须包含{an_num}占位符")
            return

        # 使用线程防止UI冻结
        self.convert_btn.config(state=tk.DISABLED)
        threading.Thread(
            target=self._generate_preview,
            args=(folder_path, match_pattern, replace_pattern),
            daemon=True,
        ).start()

    def update_preview_list(self) -> None:
        self.list_text.config(state=tk.NORMAL)
        self.list_text.delete(1.0, tk.END)

        if not self.conversion_list:
            self.list_text.insert(tk.END, "没有找到可转换的文件")
            self.list_text.config(state=tk.DISABLED)
            return

        # 优化列表更新效率
        preview_content = [f"将转换以下 {len(self.conversion_list)} 个文件:\n\n"]
        preview_content.extend(
            [
                f"{entry.name} -> {new_name}\n"
                for entry, new_name in self.conversion_list
            ]
        )
        preview_content.append(f"\n共发现 {len(self.conversion_list)} 个可转换文件")
        self.list_text.insert(tk.END, "".join(preview_content))
        self.list_text.config(state=tk.DISABLED)

        # 启用确认和取消按钮
        self.confirm_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.NORMAL)

    def _generate_preview(
        self, folder_path: str, match_pattern: str, replace_pattern: str
    ) -> None:
        """在后台线程生成转换预览"""
        try:
            logger.info(f"开始生成预览: {folder_path}")
            self.conversion_list = preview_conversions(
                folder_path,
                match_pattern=match_pattern,
                replace_pattern=replace_pattern,
            )
            # 切换回主线程更新UI
            self.root.after(0, self.update_preview_list)
            self.root.after(0, lambda: self.convert_btn.config(state=tk.NORMAL))
        except FileNotFoundError:
            logger.error(f"文件夹不存在: {folder_path}")
            self.root.after(
                0, lambda: messagebox.showerror("错误", "文件夹不存在或已被删除")
            )
            self.root.after(0, self.reset_interface)
        except Exception as e:
            logger.error(f"预览生成失败: {str(e)}")
            self.root.after(
                0, lambda: messagebox.showerror("错误", f"预览生成失败: {str(e)}")
            )
            self.root.after(0, self.reset_interface)

    def confirm_conversion(self) -> None:
        if not self.conversion_list:
            messagebox.showinfo("提示", "没有可转换的文件")
            return

        # 使用cn2an模块的执行功能
        self.confirm_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)
        # 使用线程执行转换操作
        threading.Thread(target=self._perform_conversion, daemon=True).start()

    def _perform_conversion(self) -> None:
        """在后台线程执行文件转换"""
        try:
            logger.info(f"开始转换 {len(self.conversion_list)} 个文件")
            success_count = perform_conversions(self.conversion_list)
            logger.info(f"转换完成，成功转换 {success_count} 个文件")
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "完成", f"转换完成，成功转换 {success_count} 个文件"
                ),
            )
        except PermissionError:
            logger.error("文件权限不足")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "权限错误", "无法修改文件，请检查权限设置"
                ),
            )
        except Exception as e:
            logger.error(f"转换失败: {str(e)}")
            self.root.after(
                0, lambda: messagebox.showerror("错误", f"转换失败: {str(e)}")
            )
        finally:
            self.root.after(0, self.reset_interface)

    def cancel_conversion(self) -> None:
        self.reset_interface()
        messagebox.showinfo("取消", "转换已取消")

    def reset_interface(self) -> None:
        self.conversion_list = []
        self.list_text.config(state=tk.NORMAL)
        self.list_text.delete(1.0, tk.END)
        self.list_text.config(state=tk.DISABLED)
        self.confirm_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)

    def add_placeholder(self, entry: tk.Entry, placeholder: str) -> None:
        """
        设置输入框焦点并插入占位符
        """
        entry.focus_set()
        self.insert_placeholder(entry, placeholder)

    def validate_placeholder_edit(
        self, new_value: str, index: str, action: str
    ) -> bool:
        """验证占位符编辑操作

        防止用户直接编辑{cn_num}和{an_num}占位符内容，
        保护转换规则的完整性。

        参数:
            new_value: 输入后的新值
            index: 当前光标位置
            action: 操作类型 (1=插入, 0=删除, -1=其他)

        返回:
            bool: 允许编辑返回True，阻止编辑返回False
        """
        # 允许插入或设置完整占位符 - 直接返回True不再检查
        if (action in ("1", "-1")) and new_value in ["{cn_num}", "{an_num}"]:
            return True

        placeholders = ["{cn_num}", "{an_num}"]
        # 检查所有占位符
        for ph in placeholders:
            ph_start = new_value.find(ph)
            while ph_start != -1:
                ph_end = ph_start + len(ph) - 1
                # 检查当前操作是否会修改占位符内容
                if action in ("1", "0"):  # 插入或删除操作
                    # 转换为整数索引
                    # 解析光标位置为列索引，兼容无小数点的情况
                    current_index = int(index.split(".")[-1])
                    # 检查光标位置是否在占位符范围内
                    if ph_start <= current_index <= ph_end:
                        return False  # 阻止修改
                ph_start = new_value.find(ph, ph_end + 1)
        return True

    def insert_placeholder(self, entry: tk.Entry, placeholder: str) -> None:
        """
        在输入框光标位置插入占位符
        """
        # 临时禁用验证以允许插入占位符
        entry.config(validate="none")
        entry.update_idletasks()  # 确保验证设置立即生效

        # 获取当前光标位置和文本
        # 解析光标位置为整数列索引
        cursor_index = str(entry.index(tk.INSERT))
        cursor_pos = int(cursor_index.split(".")[-1])
        current_text = entry.get()
        new_text = current_text[:cursor_pos] + placeholder + current_text[cursor_pos:]

        # 直接执行插入操作
        entry.delete(0, tk.END)
        entry.insert(0, new_text)
        entry.icursor(cursor_pos + len(placeholder))
        entry.focus_set()

        # 延迟恢复验证以确保插入完成
        # 在所有待处理事件完成后恢复验证，确保插入操作已完成
        entry.after_idle(lambda e=entry: e.config(validate="key"))

    def check_for_updates(self) -> None:
        """检查更新按钮点击事件处理"""
        self.check_update_btn.config(state=tk.DISABLED)
        self.check_update_btn.config(text="检查中...")
        threading.Thread(target=self._check_updates_in_background, daemon=True).start()

    def _check_updates_in_background(self) -> None:
        """在后台线程检查GitHub最新版本"""
        try:
            # 检查配置是否完整
            if not config.GITHUB_REPO or config.GITHUB_REPO == "username/repo":
                self.root.after(0, lambda: messagebox.showwarning("配置不完整", "请先在config.py中配置正确的GitHub仓库信息"))
                return

            # 请求GitHub API获取最新版本
            response = requests.get(f"https://api.github.com/repos/{config.GITHUB_REPO}/releases/latest", timeout=10)
            response.raise_for_status()
            latest_release = response.json()
            latest_version = latest_release['tag_name'].lstrip('v')  # 移除版本号前的'v'
            
            # 比较版本号
            current_version = config.__version__
            if version.parse(latest_version) > version.parse(current_version):
                self.root.after(0, lambda: self.show_update_dialog(latest_version, latest_release['html_url']))
            else:
                self.root.after(0, lambda: messagebox.showinfo("已是最新版本", f"当前版本 v{current_version} 已是最新"))
                
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda: messagebox.showerror("网络错误", f"无法连接到GitHub: {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"检查更新失败: {str(e)}"))
        finally:
            self.root.after(0, self._reset_update_button)

    def show_update_dialog(self, latest_version: str, release_url: str) -> None:
        """显示更新提示对话框"""
        current_version = config.__version__
        if messagebox.askyesno("发现更新", f"有新版本可用: v{latest_version}\n当前版本: v{current_version}\n是否前往下载页面?"):
            webbrowser.open(release_url)

    def _reset_update_button(self) -> None:
        """重置更新按钮状态"""
        self.check_update_btn.config(state=tk.NORMAL)
        self.check_update_btn.config(text=f"v{config.__version__}")
