# ComfyUI Mini Nodes (中文说明)

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-0.3.0%2B-green)](https://github.com/comfyanonymous/ComfyUI)


[**EN 英文说明 | English Readme**](README.md)
> 一组简洁的 ComfyUI 自定义节点，包含颜色匹配、潜在空间尺寸调整和元数据保存功能。

# 升级历史

🚀 v1.0.2 核心节点升级：mini_color_match
这是 v1.0.2 的重要修正版本，解决了新算法在特定场景下的局限性。

回归与平衡：重新引入了 Linear 和 Mean 算法并排在首位。经过测试，这两个算法在配合 Mask（遮罩） 进行局部校色（如皮肤）时，比复杂的非线性算法更稳定、更精准，有效避免了色偏。

新增 MKL & Wavelet：

MKL：无遮罩通用校色的最佳选择，擅长氛围迁移。

Wavelet：适合同构图（同机位、同背景）的白平衡修复。

交互优化：移除了冗余的 Balanced Linear 选项，用户可通过 strength 滑块获得一致的效果。

-------------------------------------------------------------------------------------------------------------------------------

🚀 v1.0.1 核心节点升级：mini_color_match
针对扩图场景与人物肤色一致性需求，本次升级彻底解决了由于图像尺寸不一导致的“采样偏移”顽疾，显著提升了校色精度。

主要更新亮点
空间解耦采样 (Decoupled Sampling)：
彻底废弃了强制缩放参考图的旧逻辑。节点现在会在目标图与参考图各自的原始分辨率下进行独立像素采样。无论两张图的长宽比如何悬殊，只要你在各自脸上画了遮罩，肤色统计就能精准对齐，不再发生“采样偏移”。

智能可选遮罩 (Auto-Full-Frame Mode)：
遮罩输入现已改为可选。如果不连接遮罩，节点会自动切换为“全图匹配”模式，利用全图统计数据进行快速调色。

高感度采样算法：
将像素提取阈值从 0.5 降至 0.1。这一改动确保了手绘遮罩的羽化边缘也能被有效计入统计，大幅增强了肤色修正的细腻度与自然感。

强化版平衡线性匹配 (Balanced Linear Plus)：
大幅放宽了对比度缩放的限制范围（从 0.85-1.15 扩展至 0.5-2.0）。这使得算法能够处理光影差异更巨大的素材，轻松实现从“现代高清”到“90年代电影感”的深度色彩迁移。

建议用法：在扩图（Outpainting）任务中，分别对目标人脸和参考人脸绘制遮罩并输入，即可获得像素级的肤色对齐效果。

## 📦 功能特性

### 🎨 颜色匹配节点 (Color Match Node)
你是否也经常为图像编辑模型的偏色烦恼，而普通的颜色匹配节点又往往无法妥善解决？这个节点可以为你提供精准的解决方案。

![示例](screenshots/edited-image.png)

如图所示，被编辑的图片不仅会因为编辑模型而导致被动的偏色，更会由于编辑内容的变化（如服装、动作或视角差异）产生主动的颜色变化。此时，若使用原图的整体作为校色参考，便无法精准地还原图像的偏色。

![示例](screenshots/result-compare.png)

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
  - 
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
4. 本项目无额外依赖。只需重启 ComfyUI，在节点搜索框中输入节点名称，然后将其拖入你的工作流即可。

📜 许可证
本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。
