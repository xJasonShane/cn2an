# main.py
import tkinter as tk
from tkinter import ttk
from gui import MainWindow
import config

if __name__ == "__main__":
    root = tk.Tk()
    root.title(f"{config.APP_NAME} v{config.__version__}")
    
    # 设置窗口大小
    root.geometry("700x600")
    
    # 窗口居中显示
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    app = MainWindow(root)
    root.mainloop()