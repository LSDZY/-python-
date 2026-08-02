import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import base64
import io
import os
import math
import qrcode


class QRImageTransfer:
    def __init__(self, root):
        self.root = root
        self.root.title("QR传图")
        self.root.geometry("1000x700")
        self.root.resizable(False,False)

        # 变量
        self.file_path = None
        self.selected_image = None
        self.compressed_image = None
        self.base64_string = None
        self.qr_image = None
        self.resize_size = tk.IntVar(value=16)  # 默认16x16
        self.resize_method = tk.StringVar(value="BOX")  # 默认BOX区域平均采样

        # 创建主框架
        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部按钮区域
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(pady=(0, 10))

        self.select_btn = tk.Button(self.button_frame, text="选择图片", command=self.select_image, width=12)
        self.select_btn.pack(side=tk.LEFT, padx=5)

        self.confirm_btn = tk.Button(self.button_frame, text="确定选取", command=self.process_image, width=12, state=tk.DISABLED)
        self.confirm_btn.pack(side=tk.LEFT, padx=5)

        # 压缩大小选择区域
        self.resize_frame = tk.LabelFrame(self.main_frame, text="压缩尺寸")
        self.resize_frame.pack(fill=tk.X, pady=(0, 5))

        sizes = [8, 16, 24, 32, 40, 48, 56, 64]
        for size in sizes:
            rb = tk.Radiobutton(self.resize_frame, text=f"{size}×{size}", variable=self.resize_size, value=size)
            rb.pack(side=tk.LEFT, padx=20, pady=5)

        # 压缩算法选择区域
        self.method_frame = tk.LabelFrame(self.main_frame, text="压缩算法")
        self.method_frame.pack(fill=tk.X, pady=(0, 10))

        methods = [
            ("BOX", "区域平均采样(默认)"),
            ("LANCZOS", "正弦加权采样(精度高)"),
            ("BILINEAR", "双线性插值(兼容好)"),
            ("BICUBIC", "双三次插值"),
            ("NEAREST", "最近邻采样"),
        ]
        for method, desc in methods:
            rb = tk.Radiobutton(
                self.method_frame,
                text=f"{method} ({desc})",
                variable=self.resize_method,
                value=method
            )
            rb.pack(side=tk.LEFT, padx=8, pady=5)

        # 横向排列区域（图片预览和二维码并排显示）
        self.center_frame = tk.Frame(self.main_frame)
        self.center_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 左侧图片区域（原图预览 + 压缩后预览）
        self.left_frame = tk.Frame(self.center_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 原图显示区域
        self.image_frame = tk.LabelFrame(self.left_frame, text="原图预览")
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.image_label = tk.Label(self.image_frame, text="未选择图片", bg="#f0f0f0", relief=tk.SUNKEN)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 压缩后图片显示区域
        self.compressed_frame = tk.LabelFrame(self.left_frame, text="压缩后预览")
        self.compressed_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.compressed_label = tk.Label(self.compressed_frame, text="压缩后图片", bg="#f0f0f0", relief=tk.SUNKEN)
        self.compressed_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 右侧区域（二维码和信息）
        self.right_frame = tk.Frame(self.center_frame)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 基础信息区域 - 2x2网格布局
        self.info_frame = tk.LabelFrame(self.right_frame, text="基础信息")
        self.info_frame.pack(fill=tk.X, pady=(0, 10))

        self.size_labels = {}
        info_items = [
            ("original", "未压缩图片大小", 0, 0),
            ("compressed", "压缩后图片大小", 0, 1),
            ("base64", "Base64编码大小", 1, 0),
            ("qr", "QR码大小", 1, 1),
        ]
        for key, text, row, col in info_items:
            lbl = tk.Label(self.info_frame, text=f"{text}: 0.00 kb", anchor="w")
            lbl.grid(row=row, column=col, padx=8, pady=3, sticky="w")
            self.size_labels[key] = lbl

        # 设置列权重，使两列等宽
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_columnconfigure(1, weight=1)

        # 二维码显示区域
        self.qr_frame = tk.LabelFrame(self.right_frame, text="生成的二维码")
        self.qr_frame.pack(fill=tk.BOTH, expand=True)

        # 比例修正按钮（悬浮在二维码上方）
        self.ratio_btn = tk.Button(
            self.qr_frame,
            text="比例修正",
            command=self.fix_aspect_ratio,
            width=12,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft YaHei", 9, "bold"),
            state=tk.DISABLED
        )
        self.ratio_btn.pack(pady=(5, 0))

        self.qr_label = tk.Label(self.qr_frame, text="二维码将显示在这里", bg="#f0f0f0", relief=tk.SUNKEN)
        self.qr_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 操作按钮区域
        self.action_frame = tk.Frame(self.main_frame)
        self.action_frame.pack(pady=(0, 10))

        self.save_btn = tk.Button(self.action_frame, text="保存QR码", command=self.save_qr, width=12, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = tk.Button(self.action_frame, text="重置程序", command=self.reset_program, width=12, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("JPEG图片", "*.jpg"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                self.file_path = file_path
                self.selected_image = Image.open(file_path)
                # 显示缩略图（保持比例，最大尺寸300x300）
                thumbnail = self.selected_image.copy()
                thumbnail.thumbnail((300, 300))
                self.tk_image = ImageTk.PhotoImage(thumbnail)
                self.image_label.config(image=self.tk_image, text="")
                self.confirm_btn.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图片: {str(e)}")

    def process_image(self):
        if not self.selected_image:
            messagebox.showwarning("警告", "请先选择图片")
            return

        try:
            # 获取用户选择的压缩尺寸和算法
            size = self.resize_size.get()
            method = self.resize_method.get()

            # 映射算法名称到Pillow常量
            method_map = {
                "BOX": Image.Resampling.BOX,
                "LANCZOS": Image.Resampling.LANCZOS,
                "BILINEAR": Image.Resampling.BILINEAR,
                "BICUBIC": Image.Resampling.BICUBIC,
                "NEAREST": Image.Resampling.NEAREST,
            }
            resampling = method_map.get(method, Image.Resampling.BOX)

            # 将图片压缩至指定像素
            self.compressed_image = self.selected_image.resize((size, size), resampling)

            # 显示压缩后的图片预览（放大显示以便观看）
            compressed_preview = self.compressed_image.copy()
            compressed_preview = compressed_preview.resize((200, 200), Image.Resampling.NEAREST)
            self.tk_compressed_image = ImageTk.PhotoImage(compressed_preview)
            self.compressed_label.config(image=self.tk_compressed_image, text="")

            # 从系统文件属性获取原图大小
            original_size_kb = os.path.getsize(self.file_path) / 1024

            # 将压缩后的图片转换为Base64编码
            buffer = io.BytesIO()
            self.compressed_image.save(buffer, format="JPEG")
            compressed_bytes = buffer.getvalue()
            compressed_size_kb = len(compressed_bytes) / 1024
            self.base64_string = base64.b64encode(compressed_bytes).decode("utf-8")
            base64_size_kb = len(self.base64_string.encode("utf-8")) / 1024

            # 生成二维码（使用低纠错级别以容纳更多数据）
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.base64_string)
            qr.make(fit=True)
            self.qr_image = qr.make_image(fill_color="black", back_color="white")

            # 计算QR码大小
            qr_buffer = io.BytesIO()
            self.qr_image.save(qr_buffer, format="PNG")
            qr_size_kb = len(qr_buffer.getvalue()) / 1024

            # 更新所有信息标签
            self.size_labels["original"].config(text=f"未压缩图片大小: {original_size_kb:.2f} kb")
            self.size_labels["compressed"].config(text=f"压缩后图片大小: {compressed_size_kb:.2f} kb")
            self.size_labels["base64"].config(text=f"Base64编码大小: {base64_size_kb:.2f} kb")
            self.size_labels["qr"].config(text=f"QR码大小: {qr_size_kb:.2f} kb")

            # 显示二维码（保持比例，最大尺寸250x250）
            qr_thumbnail = self.qr_image.copy()
            qr_thumbnail.thumbnail((250, 250))
            self.tk_qr_image = ImageTk.PhotoImage(qr_thumbnail)
            self.qr_label.config(image=self.tk_qr_image, text="")

            # 启用操作按钮
            self.save_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            self.ratio_btn.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("错误", f"处理图片时出错: {str(e)}")

    def fix_aspect_ratio(self):
        """比例修正：读取原始图像比例，附加到base64字符串末尾并重新生成二维码"""
        if not self.selected_image:
            messagebox.showwarning("警告", "请先选择图片")
            return

        if not self.base64_string:
            messagebox.showwarning("警告", "请先生成二维码")
            return

        try:
            # 加载状态
            self.ratio_btn.config(text="修正中...", state=tk.DISABLED, bg="#FF9800")
            self.root.update()

            # 步骤1: 读取原始图像宽高并计算最简整数比例
            try:
                width, height = self.selected_image.size
                if width <= 0 or height <= 0:
                    raise ValueError("图像尺寸无效")
                gcd = math.gcd(width, height)
                ratio_w = width // gcd
                ratio_h = height // gcd
                ratio_str = f"{ratio_w}:{ratio_h}"
            except Exception as e:
                self._reset_ratio_btn()
                messagebox.showerror("比例计算错误", f"读取图像比例失败: {str(e)}")
                return

            # 步骤2: 将比例信息附加到base64字符串末尾
            try:
                # 使用分隔符标记比例信息，便于识别端解析
                new_base64_string = f"{self.base64_string}|RATIO:{ratio_str}"
            except Exception as e:
                self._reset_ratio_btn()
                messagebox.showerror("编码错误", f"附加比例信息失败: {str(e)}")
                return

            # 步骤2.5: 按比例修正压缩后预览图片的显示
            try:
                if self.compressed_image:
                    orig_w, orig_h = self.compressed_image.size
                    new_w = int(orig_h * ratio_w / ratio_h)
                    ratio_preview = self.compressed_image.resize(
                        (new_w, orig_h),
                        Image.Resampling.NEAREST
                    )
                    # 放大显示以便观看（保持修正后的比例）
                    ratio_preview_display = ratio_preview.resize(
                        (max(new_w * 10, 100), max(orig_h * 10, 100)),
                        Image.Resampling.NEAREST
                    )
                    ratio_preview_display.thumbnail((200, 200))
                    self.tk_compressed_image = ImageTk.PhotoImage(ratio_preview_display)
                    self.compressed_label.config(image=self.tk_compressed_image, text="")
            except Exception as e:
                # 预览修正失败不影响主流程
                pass

            # 步骤3: 重新生成二维码
            try:
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(new_base64_string)
                qr.make(fit=True)
                self.qr_image = qr.make_image(fill_color="black", back_color="white")
            except qrcode.exceptions.DataOverflowError:
                self._reset_ratio_btn()
                messagebox.showerror(
                    "数据超限",
                    f"添加比例信息后数据超出二维码容量上限。\n"
                    f"当前比例: {ratio_str}\n"
                    f"建议: 减小压缩尺寸后重试。"
                )
                return
            except Exception as e:
                self._reset_ratio_btn()
                messagebox.showerror("二维码生成错误", f"重新生成二维码失败: {str(e)}")
                return

            # 步骤4: 更新base64字符串和界面显示
            self.base64_string = new_base64_string
            base64_size_kb = len(self.base64_string.encode("utf-8")) / 1024
            self.size_labels["base64"].config(text=f"Base64编码大小: {base64_size_kb:.2f} kb")

            # 重新计算QR码大小
            qr_buffer = io.BytesIO()
            self.qr_image.save(qr_buffer, format="PNG")
            qr_size_kb = len(qr_buffer.getvalue()) / 1024
            self.size_labels["qr"].config(text=f"QR码大小: {qr_size_kb:.2f} kb")

            # 显示新的二维码
            qr_thumbnail = self.qr_image.copy()
            qr_thumbnail.thumbnail((250, 250))
            self.tk_qr_image = ImageTk.PhotoImage(qr_thumbnail)
            self.qr_label.config(image=self.tk_qr_image, text="")

            # 恢复按钮并提示完成
            self.ratio_btn.config(text="已修正", bg="#2196F3")
            self.root.update()
            self.root.after(1500, self._reset_ratio_btn)

            messagebox.showinfo(
                "比例修正完成",
                f"原始图像尺寸: {width}×{height} 像素\n"
                f"最简整数比例: {ratio_str}\n"
                f"已将比例信息附加到base64编码末尾并重新生成二维码。\n"
                f"压缩后预览也已按比例修正显示。"
            )

        except Exception as e:
            self._reset_ratio_btn()
            messagebox.showerror("错误", f"比例修正过程中出错: {str(e)}")

    def _reset_ratio_btn(self):
        """恢复比例修正按钮到初始可用状态"""
        self.ratio_btn.config(text="比例修正", state=tk.NORMAL, bg="#4CAF50")

    def save_qr(self):
        if not self.qr_image:
            messagebox.showwarning("警告", "请先生成二维码")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存二维码",
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("JPEG图片", "*.jpg"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                self.qr_image.save(file_path)
                messagebox.showinfo("成功", "二维码已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

    def reset_program(self):
        self.file_path = None
        self.selected_image = None
        self.compressed_image = None
        self.base64_string = None
        self.qr_image = None

        # 重置界面
        self.image_label.config(image="", text="未选择图片")
        self.compressed_label.config(image="", text="压缩后图片")
        self.size_labels["original"].config(text="未压缩图片大小: 0.00 kb")
        self.size_labels["compressed"].config(text="压缩后图片大小: 0.00 kb")
        self.size_labels["base64"].config(text="Base64编码大小: 0.00 kb")
        self.size_labels["qr"].config(text="QR码大小: 0.00 kb")
        self.qr_label.config(image="", text="二维码将显示在这里")

        # 禁用按钮
        self.confirm_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.DISABLED)
        self._reset_ratio_btn()
        self.ratio_btn.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = QRImageTransfer(root)
    root.mainloop()
