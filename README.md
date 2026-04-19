# ComfyUI Mini Nodes

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-0.3.0%2B-green)](https://github.com/comfyanonymous/ComfyUI)
(https://github.com/comfyanonymous/ComfyUI)


[**🇨🇳 中文说明 | Chinese Readme**](README_zh.md)

> A collection of simple custom nodes for ComfyUI, featuring color matching, latent size adjustment, and metadata-aware image saving.

## 📦 Features

### 🎨 Color Match Node
Are you frustrated by color shifts introduced by image editing models? Standard color matching nodes often fall short. This node provides a precise solution.

![Demo](screenshots/result-compare.png)

As shown, edited images suffer from both passive color shifts (from the model) and active color changes (due to content differences like clothing, pose, or perspective). Using the entire original image as a reference fails to accurately correct these shifts.

The `mini_color_match` node solves this by using an input mask to select only the unchanged pixels as a reference, resulting in a color correction that closely matches the original.

![Demo](screenshots/example-workflow.png)

Furthermore, besides manual masks, you can use other segmentation nodes for automated selection (e.g., segmenting skin tones is highly recommended).

![Demo](screenshots/use-with-segment-nodes.png)

Since the target mask and reference mask are separate inputs, you can even use a differently styled reference image (again, using skin tones as a reference on both) to achieve stylized color grading.

![Demo](screenshots/style-color-grading.png)

**Options:**
- **Method**: 
  - `linear`: "Scales R, G, B independently. Strongest color match."
  - `unbalanced_linear`: "Scales R, G, B uniformly. Balances color and contrast."
  - `mean`: "Only shifts the mean value. Preserves original contrast."
- **Strength**: Controls the intensity of the effect, from `0.0` (no effect) to `1.0` (full effect).

---

### 🔍 Latent Size Adjuster
Quickly select latent dimensions with presets for speed and efficiency.

![Demo](screenshots/latent-size.png)

**Options:**
- **Architecture Channels**: Select based on your model's tensor type to avoid "Dimension Mismatch" or "Shape Error".
  - `16-channel (Default)`: Compatible with most popular models (FLUX.1, QWEN-IMAGE, WAN2.1/2.2, Z-IMAGE, SD3, etc.).
  - `4-channel`: For older models (SD1, SD1.5, SDXL1.0, etc.).
  - `128-channel`: For newer models (FLUX2, FLUX2.KLEIN, etc.).

---

### 💾 Image Save with Metadata
Easily toggle whether to embed your workflow metadata into the saved image file via a simple boolean switch.

---

## 🚀 Installation

1. Open your ComfyUI directory.
2. Navigate to the `custom_nodes/` folder.
3. Run the following command:
   ```bash
   git clone https://github.com/catmaxj/comfyui-mini-nodes.git
There are no additional dependencies. Simply restart ComfyUI, search for the node names, and drag them into your workflow.

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
