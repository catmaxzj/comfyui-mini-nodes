import torch
import numpy as np
from .utils import resize_crop

class mini_color_match:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_image": ("IMAGE",),  # 目标图
                "target_mask": ("MASK",),   # 目标图Mask
                "ref_image": ("IMAGE",),    # 参考图
                "ref_mask": ("MASK",),      # 参考图Mask
                "method": (["linear", "balanced_linear", "mean"], {
                    "default": "linear",
                    "tooltip": "linear: RGB独立缩放，色彩匹配度最强；\nbalanced_linear: RGB均匀缩放，兼顾对比度匹配；\nmean: 仅平移均值,保留原图对比度。"
                }), 
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "match"
    CATEGORY = "mini_nodes"

    def match(self, target_image, target_mask, ref_image, ref_mask, method, strength):
        device = target_image.device
        
        # 1. 尺寸对齐逻辑：获取目标图尺寸
        B, H, W, C = target_image.shape
        
        # 自动对齐参考图（利用 utils.py）
        if ref_image.shape[1] != H or ref_image.shape[2] != W:
            ref_image = resize_crop(ref_image, W, H, "中心裁剪", "lanczos")
        
        # 2. 转换数据为 Numpy 处理
        t_img_rgb = target_image[..., :3].cpu().numpy()
        r_img_rgb = ref_image[..., :3].cpu().numpy()
        
        t_mask = target_mask.cpu().numpy()
        r_mask = ref_mask.cpu().numpy()
        
        # 遮罩维度补全并自动缩放（如果需要）
        if len(t_mask.shape) == 2: t_mask = t_mask[None, ..., None]
        elif len(t_mask.shape) == 3: t_mask = t_mask[..., None]
        if len(r_mask.shape) == 2: r_mask = r_mask[None, ..., None]
        elif len(r_mask.shape) == 3: r_mask = r_mask[..., None]

        if r_mask.shape[1] != H or r_mask.shape[2] != W:
            from PIL import Image
            r_mask_list = []
            for m in r_mask:
                pil_m = Image.fromarray((m.squeeze() * 255).astype(np.uint8), mode="L")
                pil_m = pil_m.resize((W, H), resample=Image.Resampling.LANCZOS)
                r_mask_list.append(np.array(pil_m).astype(np.float32) / 255.0)
            r_mask = np.array(r_mask_list)[..., None]

        # 3. 核心计算循环
        result = []
        for i in range(t_img_rgb.shape[0]):
            img = t_img_rgb[i]
            m = t_mask[i] if i < t_mask.shape[0] else t_mask[0]
            ref = r_img_rgb[i] if i < r_img_rgb.shape[0] else r_img_rgb[0]
            rm = r_mask[i] if i < r_mask.shape[0] else r_mask[0]

            # 采样 Mask 区域像素
            t_pixels = img[m[..., 0] > 0.5]
            r_pixels = ref[rm[..., 0] > 0.5]

            # 防错处理
            if len(t_pixels) == 0 or len(r_pixels) == 0:
                result.append(img)
                continue

            # 获取统计数据
            t_mean, t_std = np.mean(t_pixels, axis=0), np.std(t_pixels, axis=0)
            r_mean, r_std = np.mean(r_pixels, axis=0), np.std(r_pixels, axis=0)

            if method == "linear":
                # RGB独立缩放，色彩匹配度最强
                scale = r_std / (t_std + 1e-5)
                corrected = (img - t_mean) * scale + r_mean
            
            elif method == "balanced_linear":
                # RGB均匀缩放，兼顾对比度匹配
                avg_t_std = np.mean(t_std)
                avg_r_std = np.mean(r_std)
                global_scale = np.clip(avg_r_std / (avg_t_std + 1e-5), 0.85, 1.15)
                corrected = (img - t_mean) * global_scale + r_mean
            
            else: # mean
                # 仅平移均值,保留原图对比度
                corrected = img + (r_mean - t_mean)

            # 应用强度并裁剪
            final = img + (corrected - img) * strength
            result.append(np.clip(final, 0, 1))

        # 4. 最终输出强制为 RGB，不含 Alpha
        out_tensor = torch.from_numpy(np.array(result)).to(device)
        return (out_tensor,)
