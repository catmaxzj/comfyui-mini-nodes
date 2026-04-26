import torch
import numpy as np
from .utils import resize_crop

class mini_color_match:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_image": ("IMAGE",),  # 目标图 (必填)
                "ref_image": ("IMAGE",),     # 参考图 (必填)
                "method": (["linear", "balanced_linear", "mean"], {
                    "default": "linear",
                    "tooltip": "linear: RGB独立缩放，色彩匹配度最强；\nbalanced_linear: RGB均匀缩放，兼顾对比度匹配；\nmean: 仅平移均值,保留原图对比度。"
                }), 
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "target_mask": ("MASK",),    # 目标掩码 (可选)
                "ref_mask": ("MASK",),       # 参考掩码 (可选)
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "match"
    CATEGORY = "mini_nodes"

    def match(self, target_image, ref_image, method, strength, target_mask=None, ref_mask=None):
        device = target_image.device
        B, H, W, C = target_image.shape
        
        # --- 步骤 1：在各自的原始空间提取像素 ---
        t_img_rgb = target_image[..., :3].cpu().numpy()
        r_img_rgb = ref_image[..., :3].cpu().numpy() # 使用参考图原始尺寸

        # 处理目标遮罩
        if target_mask is not None:
            t_mask = target_mask.cpu().numpy()
            if len(t_mask.shape) == 2: t_mask = t_mask[None, ..., None]
            elif len(t_mask.shape) == 3: t_mask = t_mask[..., None]
        else:
            t_mask = np.ones((B, H, W, 1), dtype=np.float32)

        # 处理参考遮罩
        if ref_mask is not None:
            r_mask = ref_mask.cpu().numpy()
            if len(r_mask.shape) == 2: r_mask = r_mask[None, ..., None]
            elif len(r_mask.shape) == 3: r_mask = r_mask[..., None]
        else:
            r_mask = np.ones((ref_image.shape[0], ref_image.shape[1], ref_image.shape[2], 1), dtype=np.float32)

        # --- 步骤 2：计算统计数据（独立采样） ---
        result = []
        for i in range(t_img_rgb.shape[0]):
            img = t_img_rgb[i]
            m = t_mask[i] if i < t_mask.shape[0] else t_mask[0]
            
            # 参考图和参考遮罩使用自己的索引
            ref = r_img_rgb[i] if i < r_img_rgb.shape[0] else r_img_rgb[0]
            rm = r_mask[i] if i < r_mask.shape[0] else r_mask[0]

            # 降低采样阈值以包含羽化区域，且在各自空间采样
            t_pixels = img[m[..., 0] > 0.1] 
            r_pixels = ref[rm[..., 0] > 0.1]

            if len(t_pixels) == 0 or len(r_pixels) == 0:
                result.append(img)
                continue

            t_mean, t_std = np.mean(t_pixels, axis=0), np.std(t_pixels, axis=0)
            r_mean, r_std = np.mean(r_pixels, axis=0), np.std(r_pixels, axis=0)

            # --- 步骤 3：应用校色
            if method == "linear":
                scale = r_std / (t_std + 1e-5)
                corrected = (img - t_mean) * scale + r_mean
            elif method == "balanced_linear":
                avg_t_std = np.mean(t_std)
                avg_r_std = np.mean(r_std)
                # 从 0.85-1.15 改为更激进的范围以应对明显色差
                global_scale = np.clip(avg_r_std / (avg_t_std + 1e-5), 0.5, 2.0)
                corrected = (img - t_mean) * global_scale + r_mean
            else:
                corrected = img + (r_mean - t_mean)

            final = img + (corrected - img) * strength
            result.append(np.clip(final, 0, 1))

        out_tensor = torch.from_numpy(np.array(result)).to(device)
        return (out_tensor,)
