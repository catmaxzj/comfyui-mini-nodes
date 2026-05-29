from .presets import ALL_PRESETS, PRESET_LOOKUP

class mini_resolution:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "选择预设尺寸": (ALL_PRESETS, {"default": ALL_PRESETS[0]}),
                "启用自定义尺寸": ("BOOLEAN", {"default": False}),
                "自定义宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "自定义高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("宽度 (Width)", "高度 (Height)")
    FUNCTION = "run"
    CATEGORY = "mini_nodes"

    def run(self, 选择预设尺寸, 启用自定义尺寸, 自定义宽度, 自定义高度):
        if 启用自定义尺寸:
            w, h = 自定义宽度, 自定义高度
        else:
            w, h = PRESET_LOOKUP[选择预设尺寸]
        return (w, h)