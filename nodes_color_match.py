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
    # 提取低频 (色彩层)
    t_low = cv2.GaussianBlur(t_img, (0, 0), 15)
    r_low = cv2.GaussianBlur(r_img, (0, 0), 15)
    
    # 计算低频层的全局差异并补偿
    t_mean = np.mean(t_low, axis=(0, 1))
    r_mean = np.mean(r_low, axis=(0, 1))
    
    # 线性偏移补偿
    out = t_img + (r_low - t_low)
    
    return np.clip(out, 0, 1)

def apply_hm(t_img, t_pixels, r_pixels):
    out = np.zeros_like(t_img)
    for i in range(3):
        t_chan = t_img[..., i]
        t_pix_chan = t_pixels[:, i]
        r_pix_chan = r_pixels[:, i]
        
        t_sorted = np.sort(t_pix_chan)
        r_sorted = np.sort(r_pix_chan)
        
        rank = np.searchsorted(t_sorted, t_chan)
        rank = np.clip(rank, 0, len(t_sorted) - 1)
        percentile = rank / len(t_sorted)
        
        out[..., i] = np.interp(percentile, np.linspace(0, 1, len(r_sorted)), r_sorted)
    return np.clip(out, 0, 1)


class mini_color_match:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_image": ("IMAGE",), 
                "ref_image": ("IMAGE",),    
                "method": (["MKL", "Wavelet", "HM"], {
                    "default": "MKL",
                    "tooltip": "MKL: 全局线性映射，适用大部分情况。\nWavelet: 适合相同构图间的色彩矫正，效果最佳。\nHM: 强制分布对齐,适合色差较大的矫正。"
                }), 
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "节点总体强度控制。"
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

        if target_mask is not None:
            t_mask = target_mask.cpu().numpy()
            if len(t_mask.shape) == 2: t_mask = t_mask[None, ..., None]
            elif len(t_mask.shape) == 3: t_mask = t_mask[..., None]
        else:
            t_mask = np.ones((t_img_rgb.shape[0], t_img_rgb.shape[1], t_img_rgb.shape[2], 1), dtype=np.float32)

        result = []
        for i in range(t_img_rgb.shape[0]):
            img = t_img_rgb[i]
            m = t_mask[i] if i < t_mask.shape[0] else t_mask[0]
            ref = r_img_rgb[i] if i < r_img_rgb.shape[0] else r_img_rgb[0]
            
            t_pixels = img[m[..., 0] > 0.1]
            r_pixels = ref.reshape(-1, 3) 

            if len(t_pixels) == 0:
                result.append(img)
                continue

            if method == "MKL":
                corrected = apply_mkl(img, t_pixels, r_pixels)
            elif method == "Wavelet":
                ref_resized = cv2.resize(ref, (img.shape[1], img.shape[0]))
                corrected = apply_wavelet_easy(img, ref_resized)
            elif method == "HM":
                corrected = apply_hm(img, t_pixels, r_pixels)
            else:
                corrected = np.copy(img)

            final = img + (corrected - img) * strength
            result.append(np.clip(final, 0, 1))

        out_tensor = torch.from_numpy(np.array(result)).to(device)
        return (out_tensor,)