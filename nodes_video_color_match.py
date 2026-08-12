import torch
import numpy as np
import cv2

# =========================================================
# 核心统计量 / 变换计算函数（只在 target_image / ref_image 上计算一次）
# =========================================================

def compute_linear_params(t_pixels, r_pixels):
    """返回 Linear 方法的 (t_mean, scale, r_mean)，用于 corrected = (img - t_mean) * scale + r_mean"""
    t_mean = np.mean(t_pixels, axis=0)
    t_std = np.std(t_pixels, axis=0)
    r_mean = np.mean(r_pixels, axis=0)
    r_std = np.std(r_pixels, axis=0)
    scale = r_std / (t_std + 1e-5)
    return t_mean, scale, r_mean


def compute_mean_params(t_pixels, r_pixels):
    """返回 Mean 方法的 (t_mean, r_mean)，用于 corrected = img + (r_mean - t_mean)"""
    t_mean = np.mean(t_pixels, axis=0)
    r_mean = np.mean(r_pixels, axis=0)
    return t_mean, r_mean


def compute_mkl_params(t_pixels, r_pixels):
    """返回 MKL 方法的 (t_mean, transform_matrix, r_mean)，
    用于 corrected = (img - t_mean) @ transform.T + r_mean"""
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

        transform = sqrt_r @ inv_sqrt_t
    except Exception:
        # 退化为对角缩放矩阵（等价于 Linear 的独立缩放）
        scale = np.std(r_pixels, axis=0) / (np.std(t_pixels, axis=0) + 1e-6)
        transform = np.diag(scale)

    return mu_t, transform, mu_r


# =========================================================
# 应用变换（向量化，一次性作用于整段视频）
# =========================================================

def apply_linear_batch(video, t_mean, scale, r_mean):
    return (video - t_mean) * scale + r_mean


def apply_mean_batch(video, t_mean, r_mean):
    return video + (r_mean - t_mean)


def apply_mkl_batch(video, t_mean, transform, r_mean):
    # video: (N, H, W, 3) -> reshape 成 (N*H*W, 3) 做矩阵乘法，再还原形状
    n, h, w, c = video.shape
    flat = video.reshape(-1, c)
    out = (flat - t_mean) @ transform.T + r_mean
    return out.reshape(n, h, w, c)


# =========================================================
# 强度插值（分段线性：start_frame 之前恒定 start_strength，
# end_frame 之后恒定 end_strength，中间线性过渡）
# =========================================================

def compute_strength_curve(num_frames, start_frame, start_strength, end_frame, end_strength):
    # start_frame / end_frame 为 1-indexed 用户输入，这里转换成 0-indexed
    s_idx = max(0, start_frame - 1)
    e_idx = min(num_frames - 1, end_frame - 1)

    idx = np.arange(num_frames, dtype=np.float32)
    curve = np.empty(num_frames, dtype=np.float32)

    if e_idx <= s_idx:
        # 起止帧重合或异常，直接用 start_strength 全程覆盖
        curve[:] = start_strength
    else:
        curve[:] = np.clip((idx - s_idx) / (e_idx - s_idx), 0.0, 1.0)
        curve = start_strength + (end_strength - start_strength) * curve

    curve[:s_idx] = start_strength
    curve[e_idx + 1:] = end_strength
    return curve  # shape (N,)


# =========================================================
# 节点主体
# =========================================================

class mini_video_color_match:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "target_video": ("IMAGE",),   # 要被校色的视频帧序列 (N,H,W,C)
                "target_image": ("IMAGE",),   # 目标锚点图，强制单帧，用于计算颜色统计量
                "ref_image": ("IMAGE",),      # 参考锚点图，强制单帧
                "method": (["Linear", "Mean", "MKL"], {
                    "default": "Linear",
                    "tooltip": "Linear: 遮罩校色,RGB独立缩放,色彩参考最直接\nMean: 遮罩校色,平移均值保留原图对比度\nMKL: 无遮罩,通用全局映射,快捷校色最方便"
                }),
                "start_frame": ("INT", {"default": 1, "min": 1, "max": 999999}),
                "start_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "end_frame": ("INT", {"default": -1, "min": -1, "max": 999999,
                                       "tooltip": "-1 表示视频最后一帧"}),
                "end_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "target_mask": ("MASK",),   # 强制单帧，对应 target_image
                "ref_mask": ("MASK",),      # 强制单帧，对应 ref_image
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("video",)
    FUNCTION = "match"
    CATEGORY = "mini_nodes"

    # ---- 工具函数 ----

    @staticmethod
    def _to_mask3d(mask_tensor):
        """把 MASK 张量统一转成 (frames, H, W, 1) 的 numpy 数组"""
        m = mask_tensor.cpu().numpy()
        if len(m.shape) == 2:
            m = m[None, ..., None]
        elif len(m.shape) == 3:
            m = m[..., None]
        return m

    @staticmethod
    def _get_single_frame_mask(mask_tensor, target_hw, node_tag):
        """从 mask 输入里取第 0 帧，多帧时打印警告；并 resize 到目标图分辨率"""
        m_all = mini_video_color_match._to_mask3d(mask_tensor)
        if m_all.shape[0] > 1:
            print(f"[mini_video_color_match] {node_tag} 输入了 {m_all.shape[0]} 帧，"
                  f"强制只使用第 1 帧，其余帧被忽略。")
        m = m_all[0]
        if m.shape[0] != target_hw[0] or m.shape[1] != target_hw[1]:
            m = cv2.resize(m[..., 0], (target_hw[1], target_hw[0]),
                            interpolation=cv2.INTER_LINEAR)[..., None]
        return m

    def match(self, target_video, target_image, ref_image, method,
              start_frame, start_strength, end_frame, end_strength,
              target_mask=None, ref_mask=None):

        device = target_video.device
        t_video = target_video.cpu().numpy()          # (N,H,W,3)
        num_frames = t_video.shape[0]

        # ---- 目标锚点图：强制单帧 ----
        t_img_np = target_image.cpu().numpy()
        if t_img_np.shape[0] > 1:
            print(f"[mini_video_color_match] target_image 输入了 {t_img_np.shape[0]} 帧，"
                  f"强制只使用第 1 帧，其余帧被忽略。")
        t_img = t_img_np[0]                            # (H,W,3)

        # ---- 参考锚点图：强制单帧 ----
        r_img_np = ref_image.cpu().numpy()
        if r_img_np.shape[0] > 1:
            print(f"[mini_video_color_match] ref_image 输入了 {r_img_np.shape[0]} 帧，"
                  f"强制只使用第 1 帧，其余帧被忽略。")
        r_img = r_img_np[0]                            # (H,W,3)

        # ---- 目标遮罩：强制单帧，对应 target_image ----
        if target_mask is not None:
            tm = self._get_single_frame_mask(target_mask, t_img.shape[:2], "target_mask")
        else:
            tm = np.ones((t_img.shape[0], t_img.shape[1], 1), dtype=np.float32)

        # ---- 参考遮罩：强制单帧，对应 ref_image ----
        if ref_mask is not None:
            rm = self._get_single_frame_mask(ref_mask, r_img.shape[:2], "ref_mask")
        else:
            rm = np.ones((r_img.shape[0], r_img.shape[1], 1), dtype=np.float32)

        # ---- 采样像素 ----
        t_pixels = t_img[tm[..., 0] > 0.1]
        r_pixels = r_img[rm[..., 0] > 0.1]

        MIN_PIXELS = 50
        if len(t_pixels) < MIN_PIXELS or len(r_pixels) < MIN_PIXELS:
            print(f"[mini_video_color_match] target_image 或 ref_image 有效像素过少"
                  f"(target={len(t_pixels)}, ref={len(r_pixels)})，低于阈值 {MIN_PIXELS}，"
                  f"跳过校色，原样输出视频。")
            return (target_video,)

        # ---- 计算锁定的变换参数（只算一次）----
        if method == "Linear":
            t_mean, scale, r_mean = compute_linear_params(t_pixels, r_pixels)
            corrected = apply_linear_batch(t_video, t_mean, scale, r_mean)
        elif method == "Mean":
            t_mean, r_mean = compute_mean_params(t_pixels, r_pixels)
            corrected = apply_mean_batch(t_video, t_mean, r_mean)
        elif method == "MKL":
            t_mean, transform, r_mean = compute_mkl_params(t_pixels, r_pixels)
            corrected = apply_mkl_batch(t_video, t_mean, transform, r_mean)
        else:
            corrected = np.copy(t_video)

        corrected = np.clip(corrected, 0, 1)

        # ---- 强度插值曲线，并与原视频混合 ----
        end_frame_resolved = num_frames if end_frame == -1 else end_frame
        weights = compute_strength_curve(
            num_frames, start_frame, start_strength, end_frame_resolved, end_strength
        )  # (N,)
        weights = weights.reshape(-1, 1, 1, 1)  # 广播到 (N,H,W,C)

        final = t_video + (corrected - t_video) * weights
        final = np.clip(final, 0, 1)

        out_tensor = torch.from_numpy(final.astype(np.float32)).to(device)
        return (out_tensor,)


NODE_CLASS_MAPPINGS = {
    "mini_video_color_match": mini_video_color_match,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "mini_video_color_match": "Mini Video Color Match",
}
