import os
import json
import torch
import numpy as np
import datetime
import folder_paths
from PIL import Image, PngImagePlugin


class mini_image_save:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "图像": ("IMAGE",),
                "文件名头": ("STRING", {"default": "%y%m%d_%H%M"}),
                "保存工作流": ("BOOLEAN", {"default": True}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "mini_nodes"

    def save_images(self, 图像, 文件名头, 保存工作流, prompt=None, extra_pnginfo=None):
        # 防止路径注入，并清理非法字符
        文件名头 = os.path.basename(文件名头)

        now = datetime.datetime.now()
        文件名头 = 文件名头.replace("%date%", now.strftime("%Y-%m-%d"))
        文件名头 = 文件名头.replace("%time%", now.strftime("%H-%M-%S"))
        文件名头 = 文件名头.replace("%y", now.strftime("%y"))   # 2位年份
        文件名头 = 文件名头.replace("%m", now.strftime("%m"))
        文件名头 = 文件名头.replace("%d", now.strftime("%d"))
        文件名头 = 文件名头.replace("%H", now.strftime("%H"))
        文件名头 = 文件名头.replace("%M", now.strftime("%M"))
        文件名头 = 文件名头.replace("%S", now.strftime("%S"))

        full_output_folder, filename, counter, subfolder, filename_prefix = (
            folder_paths.get_save_image_path(
                文件名头, self.output_dir, 图像[0].shape[1], 图像[0].shape[0]
            )
        )

        results = []
        for batch_number, image in enumerate(图像):
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = PngImagePlugin.PngInfo()
            if 保存工作流:
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for key in extra_pnginfo:
                        metadata.add_text(key, json.dumps(extra_pnginfo[key]))

            # 改成2位递增编号，如 01, 02, 03...
            file = f"{filename}_{counter + 1:02d}.png"
            img.save(
                os.path.join(full_output_folder, file),
                pnginfo=metadata,
                compress_level=4,
            )

            results.append(
                {"filename": file, "subfolder": subfolder, "type": self.type}
            )
            counter += 1

        return {"ui": {"images": results}}