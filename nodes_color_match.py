import torch
import numpy as np
import cv2

# --- 核心算法支持函数 ---

def apply_mkl(t_img, t_pixels, r_pixels):
    mu_t = np.mean(t_pixels, axis=0)
    mu_r = np.mean(r_pixels, axis=0)
    
    t_centered = t_pixels - mu_t
    r_centered = r_pixels - mu_r
    
    cov_t = np.cov(t_centered, rowvar=False) + np.eye(3) * 1e-6
    cov_r = np.cov(r_centered, rowvar=False) + np.eye(3) * 1e-6
    
    try:
        evals_t, evecs_t = np.linalg.eigh(cov_t)
        inv_sqrt_t = evecs_t @ np.diag(1.0 / np.sqrt(np.maximum(evals_t, 1e-6))) @ evecs_t.T
        
        evals_r, evecs_r = np.linalg.eigh(cov_r)
        sqrt_r = evecs_r @ np.diag(np.sqrt(np.maximum(evals_r, 0))) @ evecs_r.T
        
        t = sqrt_r @ inv_sqrt_t
        out = (t_img - mu_t) @ t.T + mu_r
    except:
        out = (t_img - mu_t) * (np.std(r_pixels, axis=0) / (np.std(t_pixels, axis=0) + 1e-6)) + mu_r
        
    return np.clip(out, 0, 1)

def apply_wavelet_easy(t_img, r_img):
    t_low = cv2.GaussianBlur(t_img, (0, 0), 15)
    r_low = cv2.GaussianBlur(r_img, (0, 0), 15)
    out = t_img + (r_low - t_low)
    return np.clip(out, 0, 1)

class mini_color_match:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_image": ("IMAGE",), 
                "ref_image": ("IMAGE",),    
                "method": (["Linear", "Mean", "MKL", "Wavelet"], {
                    "default": "Linear",
                    "tooltip": "Linear: 适合遮罩校色,RGB独立缩放,色彩参考最直接\nMean: 适合遮罩校色,平移均值保留原图对比度,风格参考最稳定\nMKL: 适合无遮罩,通用全局映射,快捷校色最方便\nWavelet: 适合无遮罩,且相同构图矫正偏色,还原参考最自然"
                }), 
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                }),
            },
            "optional": {
                "target_mask": ("MASK",),  
                "ref_mask": ("MASK",),      
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "match"
    CATEGORY = "mini_nodes"

    def match(self, target_image, ref_image, method, strength, target_mask=None, ref_mask=None):
        device = target_image.device
        t_img_rgb = target_image.cpu().numpy()
        r_img_rgb = ref_image.cpu().numpy() 

        # 处理目标遮罩
        if target_mask is not None:
            t_mask = target_mask.cpu().numpy()
            if len(t_mask.shape) == 2: t_mask = t_mask[None, ..., None]
            elif len(t_mask.shape) == 3: t_mask = t_mask[..., None]
        else:
            t_mask = np.ones((t_img_rgb.shape[0], t_img_rgb.shape[1], t_img_rgb.shape[2], 1), dtype=np.float32)

        # 处理参考遮罩
        if ref_mask is not None:
            r_mask = ref_mask.cpu().numpy()
            if len(r_mask.shape) == 2: r_mask = r_mask[None, ..., None]
            elif len(r_mask.shape) == 3: r_mask = r_mask[..., None]
        else:
            r_mask = np.ones((r_img_rgb.shape[0], r_img_rgb.shape[1], r_img_rgb.shape[2], 1), dtype=np.float32)

        result = []
        for i in range(t_img_rgb.shape[0]):
            img = t_img_rgb[i]
            m = t_mask[i] if i < t_mask.shape[0] else t_mask[0]
            ref = r_img_rgb[i] if i < r_img_rgb.shape[0] else r_img_rgb[0]
            rm = r_mask[i] if i < r_mask.shape[0] else r_mask[0]
            
            # 在各自原始空间进行独立采样
            t_pixels = img[m[..., 0] > 0.1]
            r_pixels = ref[rm[..., 0] > 0.1] 

            if len(t_pixels) == 0 or len(r_pixels) == 0:
                result.append(img)
                continue

            if method == "Linear":
                # Linear 独立缩放
                t_mean, t_std = np.mean(t_pixels, axis=0), np.std(t_pixels, axis=0)
                r_mean, r_std = np.mean(r_pixels, axis=0), np.std(r_pixels, axis=0)
                scale = r_std / (t_std + 1e-5)
                corrected = (img - t_mean) * scale + r_mean
            elif method == "Mean":
                # mean 仅平移
                t_mean = np.mean(t_pixels, axis=0)
                r_mean = np.mean(r_pixels, axis=0)
                corrected = img + (r_mean - t_mean)
            elif method == "MKL":
                # mkl 通用全局
                corrected = apply_mkl(img, t_pixels, r_pixels)
            elif method == "Wavelet":
                # Wavelet 相同构图校色
                ref_resized = cv2.resize(ref, (img.shape[1], img.shape[0]))
                corrected = apply_wavelet_easy(img, ref_resized)
            else:
                corrected = np.copy(img)

            final = img + (corrected - img) * strength
            result.append(np.clip(final, 0, 1))

        out_tensor = torch.from_numpy(np.array(result)).to(device)
        return (out_tensor,)