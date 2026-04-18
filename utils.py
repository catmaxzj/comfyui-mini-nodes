import torch
import numpy as np
from PIL import Image, ImageOps

def resize_crop(image, tgt_w, tgt_h, crop_method, algo):
    resample = Image.Resampling[algo.upper()]
    # 处理图像张量
    pil_img = Image.fromarray((image.squeeze(0).cpu().numpy() * 255).astype(np.uint8))
    if crop_method == "中心裁剪":
        pil_img = ImageOps.fit(pil_img, (tgt_w, tgt_h), method=resample)
    else:
        pil_img = pil_img.resize((tgt_w, tgt_h), resample=resample)
    return torch.from_numpy(np.array(pil_img).astype(np.float32) / 255.0).unsqueeze(0)