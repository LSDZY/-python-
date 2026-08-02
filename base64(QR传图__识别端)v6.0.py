import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import base64
import io
import numpy as np


class QRDecoder:
    def __init__(self, root):
        self.root = root
        self.root.title("QR传图 - 识别端")
        self.root.geometry("1200x600")
        self.root.resizable(False, False)

        # 变量
        self.qr_image = None
        self.decoded_image = None
        self.optimized_image = None
        self.base64_data = None
        self.raw_base64_data = None  # 原始base64数据（不含比例信息）
        self.ratio_info = None  # 宽高比例信息 (如 "4:3")
        self.tk_preview = None
        self.tk_decoded = None
        self.tk_optimized = None
        self.apply_wiener = tk.BooleanVar(value=False)
        self.scale_factor = tk.IntVar(value=2)

        # 主框架
        self.main_frame = tk.Frame(root, padx=15, pady=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        self.title_label = tk.Label(
            self.main_frame,
            text="QR传图 - 识别端",
            font=("Microsoft YaHei", 16, "bold")
        )
        self.title_label.pack(pady=(0, 10))

        # 上传按钮区域
        self.upload_frame = tk.Frame(self.main_frame)
        self.upload_frame.pack(pady=(0, 5))

        self.upload_btn = tk.Button(
            self.upload_frame,
            text="上传QR码",
            command=self.upload_qr,
            width=15,
            font=("Microsoft YaHei", 10)
        )
        self.upload_btn.pack(side=tk.LEFT, padx=5)

        # 状态提示
        self.status_label = tk.Label(self.main_frame, text="请上传一张QR码图片开始识别", fg="gray")
        self.status_label.pack(pady=(0, 8))

        # 横向排列区域（三个面板并排显示）
        self.center_frame = tk.Frame(self.main_frame)
        self.center_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # 左侧：QR码预览区域
        self.preview_frame = tk.LabelFrame(self.center_frame, text="QR码预览")
        self.preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.preview_label = tk.Label(
            self.preview_frame,
            text="等待上传QR码...",
            bg="#f0f0f0",
            relief=tk.SUNKEN
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 中间：识别结果区域
        self.result_frame = tk.LabelFrame(self.center_frame, text="识别结果")
        self.result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 比例信息显示标签
        self.ratio_info_label = tk.Label(
            self.result_frame,
            text="宽高比例: 未识别",
            font=("Microsoft YaHei", 9),
            fg="#2196F3",
            anchor="w"
        )
        self.ratio_info_label.pack(fill=tk.X, padx=5, pady=(5, 0))

        self.result_label = tk.Label(
            self.result_frame,
            text="识别后的图片将显示在这里",
            bg="#f0f0f0",
            relief=tk.SUNKEN
        )
        self.result_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 右侧：结果优化区域
        self.optimize_frame = tk.LabelFrame(self.center_frame, text="结果优化")
        self.optimize_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 优化控制面板
        self.optimize_control = tk.Frame(self.optimize_frame)
        self.optimize_control.pack(fill=tk.X, padx=5, pady=5)

        # 放大倍数选择
        scale_frame = tk.Frame(self.optimize_control)
        scale_frame.pack(side=tk.LEFT)

        tk.Label(scale_frame, text="放大倍数:").pack(side=tk.LEFT)

        self.scale_spinbox = tk.Spinbox(
            scale_frame,
            from_=1,
            to=8,
            textvariable=self.scale_factor,
            width=3,
            font=("Microsoft YaHei", 9)
        )
        self.scale_spinbox.pack(side=tk.LEFT, padx=(5, 10))

        self.wiener_check = tk.Checkbutton(
            self.optimize_control,
            text="Wiener滤波",
            variable=self.apply_wiener,
            font=("Microsoft YaHei", 9)
        )
        self.wiener_check.pack(side=tk.LEFT)

        self.optimize_btn = tk.Button(
            self.optimize_control,
            text="执行优化",
            command=self.optimize_image,
            width=10,
            font=("Microsoft YaHei", 9),
            state=tk.DISABLED
        )
        self.optimize_btn.pack(side=tk.RIGHT)

        # 优化结果显示
        self.optimize_label = tk.Label(
            self.optimize_frame,
            text="优化后的图片将显示在这里\n\nWiener → Lanczos → 双边滤波 → USM锐化",
            bg="#f0f0f0",
            relief=tk.SUNKEN
        )
        self.optimize_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # 操作按钮区域
        self.action_frame = tk.Frame(self.main_frame)
        self.action_frame.pack(pady=(5, 0))

        self.copy_btn = tk.Button(
            self.action_frame,
            text="复制源码",
            command=self.copy_source,
            width=12,
            font=("Microsoft YaHei", 10),
            state=tk.DISABLED
        )
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = tk.Button(
            self.action_frame,
            text="保存图片",
            command=self.save_image,
            width=12,
            font=("Microsoft YaHei", 10),
            state=tk.DISABLED
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.save_opt_btn = tk.Button(
            self.action_frame,
            text="保存优化图",
            command=self.save_optimized_image,
            width=12,
            font=("Microsoft YaHei", 10),
            state=tk.DISABLED
        )
        self.save_opt_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = tk.Button(
            self.action_frame,
            text="重置程序",
            command=self.reset_program,
            width=12,
            font=("Microsoft YaHei", 10)
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)

    def upload_qr(self):
        file_path = filedialog.askopenfilename(
            title="选择QR码图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            try:
                # 显示QR码预览
                self.qr_image = Image.open(file_path)
                preview = self.qr_image.copy()
                preview.thumbnail((200, 200))
                self.tk_preview = ImageTk.PhotoImage(preview)
                self.preview_label.config(
                    image=self.tk_preview,
                    text="",
                    width=300,
                    height=300
                )

                # 自动识别QR码
                self.decode_qr(file_path)

            except Exception as e:
                messagebox.showerror("错误", f"无法打开图片: {str(e)}")

    def decode_qr(self, file_path):
        try:
            self.status_label.config(text="正在识别QR码...", fg="blue")
            self.root.update()

            # 使用pyzbar识别QR码
            from pyzbar.pyzbar import decode

            image = Image.open(file_path)
            decoded_objects = decode(image)

            if not decoded_objects:
                # 尝试使用OpenCV作为备选方案
                try:
                    import cv2

                    cv_image = cv2.imread(file_path)
                    detector = cv2.QRCodeDetector()
                    data, points, _ = detector.detectAndDecode(cv_image)

                    if data:
                        self.process_decoded_data(data)
                    else:
                        self.status_label.config(text="识别失败：无法识别QR码内容", fg="red")
                        messagebox.showwarning("警告", "无法识别QR码，请确保图片清晰且包含有效的QR码。")
                except Exception:
                    self.status_label.config(text="识别失败：无法识别QR码内容", fg="red")
                    messagebox.showwarning("警告", "无法识别QR码，请确保图片清晰且包含有效的QR码。")
            else:
                # 取第一个识别结果
                data = decoded_objects[0].data.decode("utf-8")
                self.process_decoded_data(data)

        except ImportError:
            # 如果pyzbar不可用，尝试OpenCV
            try:
                import cv2

                cv_image = cv2.imread(file_path)
                detector = cv2.QRCodeDetector()
                data, points, _ = detector.detectAndDecode(cv_image)

                if data:
                    self.process_decoded_data(data)
                else:
                    self.status_label.config(text="识别失败：无法识别QR码内容", fg="red")
                    messagebox.showwarning("警告", "无法识别QR码，请确保图片清晰且包含有效的QR码。")
            except ImportError:
                self.status_label.config(text="错误：缺少识别库，请安装pyzbar或opencv-python", fg="red")
                messagebox.showerror(
                    "错误",
                    "缺少QR码识别库，请运行以下命令安装：\n\n"
                    "pip install pyzbar\n"
                    "或\n"
                    "pip install opencv-python"
                )
        except Exception as e:
            self.status_label.config(text=f"识别失败: {str(e)}", fg="red")
            messagebox.showerror("错误", f"识别QR码时出错: {str(e)}")

    def process_decoded_data(self, data):
        try:
            # 保存完整数据（含比例信息）
            self.base64_data = data

            # 解析比例信息（生成端格式: base64数据|RATIO:长:宽）
            if "|RATIO:" in data:
                parts = data.split("|RATIO:")
                self.raw_base64_data = parts[0]
                ratio_part = parts[1]
                # 验证比例格式（如 "4:3"）
                if ":" in ratio_part:
                    try:
                        ratio_w, ratio_h = ratio_part.split(":")
                        # 验证为有效整数
                        int(ratio_w)
                        int(ratio_h)
                        self.ratio_info = ratio_part
                        self.ratio_info_label.config(
                            text=f"宽高比例: {self.ratio_info} (原图比例)",
                            fg="green"
                        )
                    except ValueError:
                        self.ratio_info = None
                        self.ratio_info_label.config(text="宽高比例: 格式错误", fg="red")
                else:
                    self.ratio_info = None
                    self.ratio_info_label.config(text="宽高比例: 格式错误", fg="red")
            else:
                self.raw_base64_data = data
                self.ratio_info = None
                self.ratio_info_label.config(text="宽高比例: 未包含比例信息", fg="gray")

            # 使用纯base64数据解码图片
            image_data = base64.b64decode(self.raw_base64_data)
            image_buffer = io.BytesIO(image_data)
            self.decoded_image = Image.open(image_buffer)

            # 如果有比例信息，按原比例还原图片（修改self.decoded_image本身）
            if self.ratio_info:
                try:
                    ratio_w, ratio_h = self.ratio_info.split(":")
                    ratio_w = int(ratio_w)
                    ratio_h = int(ratio_h)
                    # 按比例调整尺寸（以高度为基准，按比例计算宽度）
                    orig_w, orig_h = self.decoded_image.size
                    new_w = int(orig_h * ratio_w / ratio_h)
                    self.decoded_image = self.decoded_image.resize(
                        (new_w, orig_h),
                        Image.Resampling.NEAREST
                    )
                except Exception as e:
                    self.status_label.config(text=f"比例还原失败: {str(e)}", fg="orange")

            # 显示解码后的图片（限制最大尺寸）
            display_image = self.decoded_image.copy()
            display_image.thumbnail((300, 300))
            self.tk_decoded = ImageTk.PhotoImage(display_image)
            self.result_label.config(
                image=self.tk_decoded,
                text="",
                width=300,
                height=300
            )

            # 重置优化结果
            self.optimized_image = None
            self.optimize_label.config(
                image="",
                text="优化后的图片将显示在这里\n\nWiener → Lanczos → 双边滤波 → USM锐化",
                width=300,
                height=300
            )

            # 更新状态
            ratio_status = f" | 原图比例: {self.ratio_info}" if self.ratio_info else ""
            self.status_label.config(
                text=f"识别成功！图片尺寸: {self.decoded_image.size[0]}×{self.decoded_image.size[1]} 像素{ratio_status}",
                fg="green"
            )

            # 启用操作按钮
            self.copy_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            self.optimize_btn.config(state=tk.NORMAL)
            self.save_opt_btn.config(state=tk.DISABLED)

        except Exception as e:
            self.status_label.config(text=f"解码失败: {str(e)}", fg="red")
            messagebox.showerror("错误", f"解码base64数据时出错: {str(e)}")

    def optimize_image(self):
        if not self.decoded_image:
            messagebox.showwarning("警告", "请先识别QR码")
            return

        try:
            self.status_label.config(text="正在优化图片...", fg="blue")
            self.root.update()

            img = self.decoded_image.copy()
            scale = self.scale_factor.get()

            # 步骤1: 可选Wiener滤波（放在最前面）
            if self.apply_wiener.get():
                try:
                    import cv2
                    img_np = np.array(img)
                    # 对每个通道分别应用Wiener滤波
                    for c in range(3):
                        channel = img_np[:, :, c]
                        img_np[:, :, c] = self._wiener_filter_channel(channel)
                    img = Image.fromarray(img_np)
                except ImportError:
                    # 使用PIL的SHARPEN滤波作为备选
                    img = img.filter(ImageFilter.SHARPEN)

            # 步骤2: Lanczos插值放大
            w, h = img.size
            img_upscaled = img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)

            # 步骤3: 双边滤波
            img_np = np.array(img_upscaled)
            try:
                import cv2
                img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                img_bilateral = cv2.bilateralFilter(img_cv2, d=9, sigmaColor=75, sigmaSpace=75)
                img_np = cv2.cvtColor(img_bilateral, cv2.COLOR_BGR2RGB)
            except ImportError:
                img_pil = Image.fromarray(img_np)
                img_pil = img_pil.filter(ImageFilter.SMOOTH)
                img_np = np.array(img_pil)

            img_filtered = Image.fromarray(img_np)

            # 步骤4: 低强度USM锐化
            img_blur = img_filtered.filter(ImageFilter.GaussianBlur(radius=1))
            img_sharpened = Image.blend(img_filtered, img_blur, alpha=0.3)

            # 保存优化结果
            self.optimized_image = img_sharpened

            # 显示优化后的图片
            display_image = self.optimized_image.copy()
            display_image.thumbnail((300, 300))
            self.tk_optimized = ImageTk.PhotoImage(display_image)
            self.optimize_label.config(
                image=self.tk_optimized,
                text="",
                width=300,
                height=300
            )

            # 更新状态
            wiener_status = "Wiener → " if self.apply_wiener.get() else ""
            self.status_label.config(
                text=f"优化完成！({wiener_status}{scale}x Lanczos → 双边滤波 → USM锐化)",
                fg="green"
            )

            # 启用保存优化图按钮
            self.save_opt_btn.config(state=tk.NORMAL)

        except Exception as e:
            self.status_label.config(text=f"优化失败: {str(e)}", fg="red")
            messagebox.showerror("错误", f"图片优化时出错: {str(e)}")

    def _wiener_filter_channel(self, channel):
        """对单个通道应用Wiener滤波"""
        try:
            import cv2
            # 使用OpenCV实现近似Wiener滤波
            # 先做模糊，然后反锐化
            blurred = cv2.GaussianBlur(channel.astype(np.float32), (5, 5), 1.0)
            # Wiener滤波公式: result = original - noise * (original - blurred)
            # 简化版本：result = original + 0.5 * (original - blurred)
            result = channel.astype(np.float32) + 0.5 * (channel.astype(np.float32) - blurred)
            return np.clip(result, 0, 255).astype(np.uint8)
        except ImportError:
            # 备选：使用简单的反锐化掩模
            pil_channel = Image.fromarray(channel)
            blurred = pil_channel.filter(ImageFilter.GaussianBlur(radius=1))
            result = Image.blend(pil_channel, blurred, alpha=0.5)
            return np.array(result)

    def copy_source(self):
        if self.base64_data:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.base64_data)
            self.root.update()
            ratio_note = f"\n(含比例信息: {self.ratio_info})" if self.ratio_info else "\n(纯图片数据)"
            self.status_label.config(text="源码已复制到剪贴板！", fg="green")
            messagebox.showinfo("成功", f"Base64源码已复制到剪贴板{ratio_note}")

    def save_image(self):
        if self.decoded_image:
            file_path = filedialog.asksaveasfilename(
                title="保存识别结果图片",
                defaultextension=".png",
                filetypes=[
                    ("PNG图片", "*.png"),
                    ("JPEG图片", "*.jpg"),
                    ("所有文件", "*.*")
                ]
            )
            if file_path:
                try:
                    # self.decoded_image已按比例还原，直接保存
                    self.decoded_image.save(file_path)
                    self.status_label.config(text=f"图片已保存至: {file_path}", fg="green")
                    messagebox.showinfo("成功", "图片保存成功！")
                except Exception as e:
                    messagebox.showerror("错误", f"保存图片时出错: {str(e)}")

    def save_optimized_image(self):
        if self.optimized_image:
            file_path = filedialog.asksaveasfilename(
                title="保存优化后图片",
                defaultextension=".png",
                filetypes=[
                    ("PNG图片", "*.png"),
                    ("JPEG图片", "*.jpg"),
                    ("所有文件", "*.*")
                ]
            )
            if file_path:
                try:
                    self.optimized_image.save(file_path)
                    self.status_label.config(text=f"优化图片已保存至: {file_path}", fg="green")
                    messagebox.showinfo("成功", "优化后图片保存成功！")
                except Exception as e:
                    messagebox.showerror("错误", f"保存图片时出错: {str(e)}")

    def reset_program(self):
        self.qr_image = None
        self.decoded_image = None
        self.optimized_image = None
        self.base64_data = None
        self.raw_base64_data = None
        self.ratio_info = None

        # 重置界面
        self.preview_label.config(image="", text="等待上传QR码...", width=40, height=8)
        self.result_label.config(image="", text="识别后的图片将显示在这里", width=40, height=8)
        self.ratio_info_label.config(text="宽高比例: 未识别", fg="#2196F3")
        self.optimize_label.config(
            image="",
            text="优化后的图片将显示在这里\n\nWiener → Lanczos → 双边滤波 → USM锐化",
            width=40,
            height=8
        )
        self.status_label.config(text="请上传一张QR码图片开始识别", fg="gray")

        # 重置选项
        self.apply_wiener.set(False)
        self.scale_factor.set(2)

        # 禁用按钮
        self.copy_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.save_opt_btn.config(state=tk.DISABLED)
        self.optimize_btn.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = QRDecoder(root)
    root.mainloop()