import torch
from .presets import ALL_PRESETS, PRESET_LOOKUP

class mini_latent_size:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "架构通道": (["16-Channel (Modern)", "4-Channel (SD)", "128-Channel (Flux2)"], {"default": "16-Channel (Modern)"}),
                "预设尺寸": (ALL_PRESETS, {"default": ALL_PRESETS[0]}),
                "批量大小": ("INT", {"default": 1, "min": 1, "max": 64, "step": 1}),
                "启用自定义尺寸": ("BOOLEAN", {"default": False}),
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("LATENT",)
    FUNCTION = "run"
    CATEGORY = "mini_nodes"
    def run(self, 架构通道, 预设尺寸, 批量大小, **kwargs):
        w, h = (kwargs["宽度"], kwargs["高度"]) if kwargs["启用自定义尺寸"] else PRESET_LOOKUP[预设尺寸]
        if "128-Channel" in 架构通道: channels, scale_factor = 128, 16
        elif "4-Channel" in 架构通道: channels, scale_factor = 4, 8
        else: channels, scale_factor = 16, 8
        latent = torch.zeros([批量大小, channels, h // scale_factor, w // scale_factor])
        return ({"samples": latent},)