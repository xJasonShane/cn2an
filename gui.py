# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import config
from cn2an import process_files, chinese_to_arabic
import re
from pathlib import Path
import logging
from cn2an import preview_conversions, perform_conversions
import re

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.target_path = tk.StringVar()
        self.conversion_list = []
        self.create_widgets()

    def create_widgets(self):
        # 创建主框架
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 版本信息
        version_label = tk.Label(main_frame, text=f"v{config.__version__}", fg="gray")
        version_label.pack(anchor=tk.NE)

        # 标题
        title_label = tk.Label(main_frame, text=config.APP_NAME, font=('SimHei', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # 文件夹选择
        path_frame = tk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=(10, 10))

        tk.Label(path_frame, text="目标文件夹:", font=('SimHei', 10)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Entry(path_frame, textvariable=self.target_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(path_frame, text="浏览", command=self.browse_folder, width=10).pack(side=tk.LEFT, padx=(10, 0))

        # 转换按钮
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 10))

        self.convert_btn = tk.Button(btn_frame, text="开始转换", command=self.start_conversion, 
                                    font=('SimHei', 12), bg="#4CAF50", fg="white", height=1)
        self.convert_btn.pack(fill=tk.X)

        # 转换清单
        list_frame = tk.LabelFrame(main_frame, text="转换清单预览", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        self.list_text = scrolledtext.ScrolledText(list_frame, wrap=tk.WORD, height=18)
        self.list_text.pack(fill=tk.BOTH, expand=True)
        self.list_text.config(state=tk.DISABLED)

        # 确认按钮
        confirm_frame = tk.Frame(main_frame)
        confirm_frame.pack(fill=tk.X, pady=15)

        self.confirm_btn = tk.Button(confirm_frame, text="确认转换", command=self.confirm_conversion, 
                                    font=('SimHei', 10), bg="#2196F3", fg="white", width=15)
        self.confirm_btn.pack(side=tk.RIGHT, padx=(10, 0))
        self.confirm_btn.config(state=tk.DISABLED)

        self.cancel_btn = tk.Button(confirm_frame, text="取消", command=self.cancel_conversion, 
                                   font=('SimHei', 10), width=15)
        self.cancel_btn.pack(side=tk.RIGHT)
        self.cancel_btn.config(state=tk.DISABLED)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.target_path.set(folder_path)
            # 启用转换按钮
            self.convert_btn.config(state=tk.NORMAL)

    def start_conversion(self):
        folder_path = self.target_path.get()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("错误", "请选择有效的文件夹路径")
            return

        # 使用cn2an模块的预览功能
        self.conversion_list = preview_conversions(Path(folder_path))
        self.update_preview_list()

    def update_preview_list(self):
        self.list_text.config(state=tk.NORMAL)
        self.list_text.delete(1.0, tk.END)

        if not self.conversion_list:
            self.list_text.insert(tk.END, "没有找到可转换的文件")
            self.list_text.config(state=tk.DISABLED)
            return

        self.list_text.insert(tk.END, f"将转换以下 {len(self.conversion_list)} 个文件:\n\n")

        for entry, new_name in self.conversion_list:
            self.list_text.insert(tk.END, f"{entry.name} -> {new_name}\n")

        self.list_text.insert(tk.END, f"\n共发现 {len(self.conversion_list)} 个可转换文件")
        self.list_text.config(state=tk.DISABLED)

        # 启用确认和取消按钮
        self.confirm_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.NORMAL)

    def confirm_conversion(self):
        if not self.conversion_list:
            messagebox.showinfo("提示", "没有可转换的文件")
            return

        # 使用cn2an模块的执行功能
        success_count = perform_conversions(self.conversion_list)
        messagebox.showinfo("完成", f"转换完成，成功转换 {success_count} 个文件")
        self.reset_interface()

    def cancel_conversion(self):
        self.reset_interface()
        messagebox.showinfo("取消", "转换已取消")

    def reset_interface(self):
        self.conversion_list = []
        self.list_text.config(state=tk.NORMAL)
        self.list_text.delete(1.0, tk.END)
        self.list_text.config(state=tk.DISABLED)
        self.confirm_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.DISABLED)