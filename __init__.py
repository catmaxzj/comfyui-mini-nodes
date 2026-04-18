# __init__.py
from .nodes_color_match import mini_color_match
from .nodes_latent_size import mini_latent_size
from .nodes_image_save import mini_image_save

NODE_CLASS_MAPPINGS = {
    "mini_color_match": mini_color_match,
    "mini_latent_size": mini_latent_size,
    "mini_image_save": mini_image_save
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "mini_color_match": "mini_color_match",
    "mini_latent_size": "mini_latent_size",
    "mini_image_save": "mini_image_save"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
