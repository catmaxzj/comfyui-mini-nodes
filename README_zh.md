# ComfyUI Mini Nodes (中文说明)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-0.3.0%2B-green)](https://github.com/comfyanonymous/ComfyUI)


[**EN 英文说明 | English Readme**](README.md)
> 一组简洁的 ComfyUI 自定义节点，包含颜色匹配、潜在空间尺寸调整和元数据保存功能。

## 📦 功能特性

### 🎨 颜色匹配节点 (Color Match Node)
你是否也经常为图像编辑模型的偏色烦恼，而普通的颜色匹配节点又往往无法妥善解决？这个节点可以为你提供精准的解决方案。

![示例](screenshots/edited-image.png)

如图所示，被编辑的图片不仅会因为编辑模型而导致被动的偏色，更会由于编辑内容的变化（如服装、动作或视角差异）产生主动的颜色变化。此时，若使用原图的整体作为校色参考，便无法精准地还原图像的偏色。

这个 `mini_color_match` 节点可以通过遮罩输入，仅选取未被主动更改的像素作为参考，从而使整体的校色效果更接近原图。

![示例](screenshots/example-workflow.png)

此外，除了手动输入遮罩，还可以通过其他分割节点进行自动化选取（建议自动分割裸露的肤色部分作为参考）。

![示例](screenshots/use-with-segment-nodes.png)

并且，由于目标遮罩和参考遮罩是分开的输入，还可以通过输入不同风格的参考图（建议两张图都选取肤色部分作为参考），以达到风格化调色的目的。

![示例](screenshots/style-color-grading.png)

**选项说明:**
- **方法 (Method)**: 
  - `linear`: "RGB独立缩放，色彩匹配度最强。"
  - `unbalanced_linear`: "RGB均匀缩放，兼顾对比度匹配。"
  - `mean`: "仅平移均值，保留原图对比度。"
- **强度 (Strength)**: 控制调色生效的强度，从 `0.0`（完全不起效）到 `1.0`（完全起效）。

---

### 🔍 潜在空间尺寸调整器 (Latent Size Adjuster)
通过预设快速选择潜在空间尺寸，高效便捷。

![示例](screenshots/latent-size.png)

**选项说明:**
- **架构通道 (Architecture Channels)**: 根据所使用模型的类型进行选择，以避免“维度不匹配”(Dimension Mismatch) 或 “形状错误”(Shape Error)。
  - `16通道 (默认)`: 兼容大部分流行的模型 (FLUX.1, QWEN-IMAGE, WAN2.1/2.2, Z-IMAGE, SD3 等)。
  - `4通道`: 适用于较早的使用4通道的模型 (SD1, SD1.5, SDXL1.0 等)。
  - `128通道`: 适用于使用128通道的模型 (FLUX2, FLUX2.KLEIN 等)。

---

### 💾 带元数据的图像保存 (Image Save with Metadata)
通过一个简单的布尔开关，即可决定是否将你的工作流信息嵌入到保存的图像文件中。

---

## 🚀 安装指南

1. 打开你的 ComfyUI 目录。
2. 进入 `custom_nodes/` 文件夹。
3. 运行以下命令：
   ```bash
   git clone https://github.com/catmaxj/comfyui-mini-nodes.git
   git clone https://github.com/catmaxj/comfyui-mini-nodes.git
4. 本项目无额外依赖。只需重启 ComfyUI，在节点搜索框中输入节点名称，然后将其拖入你的工作流即可。

📜 许可证
本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。
