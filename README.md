# Upscale

A convenience script for bulk upscaling using [ffmpeg](https://ffmpeg.org/) and
[Real-ESRGAN ncnn Vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan)

This is in progress

## Usage

Make sure the `ffmpeg` and `realesrgan-ncnn-vulkan` commands are available.

'''shell
pip install -r requirements.txt
python upscale.py upscale -i test_out/ -o test_upscale/ -f jpg -s 2
'''
