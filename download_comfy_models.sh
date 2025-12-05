#!/bin/bash

echo "To simulate the production ComfyUI environment, you need the following models:"

echo "1. Qwen Image GGUF Model:"
echo "   URL: https://huggingface.co/city96/Qwen-Image-gguf/resolve/main/qwen-image-Q4_K_M.gguf"
echo "   Install Path: ComfyUI/models/diffusion_models/qwen-image-Q4_K_M.gguf"

echo ""
echo "2. Qwen Image LoRA:"
echo "   URL: https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-4steps-V2.0.safetensors"
echo "   Install Path: ComfyUI/models/loras/Qwen-Image-Lightning-4steps-V2.0.safetensors"

echo ""
echo "3. Qwen Text Encoder:"
echo "   URL: https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"
echo "   Install Path: ComfyUI/models/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"

echo ""
echo "4. Qwen VAE:"
echo "   URL: https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"
echo "   Install Path: ComfyUI/models/vae/qwen_image_vae.safetensors"

echo ""
echo "You also need the 'comfyui-gguf' custom node installed in ComfyUI."














