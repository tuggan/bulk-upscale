import argparse
import sys
import os
import subprocess
from ffmpeg import FFmpeg, Progress


def clean_path(path: str):
    path = os.path.normpath(path)
    path = path.replace(' ', '_')
    path = path.replace('\'', '')
    return path


def on_progress(progress: Progress):
    print(f"\rframe: {progress.frame} fps: {progress.fps} time: {str(progress.time)}", end="")


def on_completed():
    print("")


def extract_metadata(src: str, dst: str):
    print(src)
    print(dst)
    if not src or not dst:
        print("Both src and dst are expected for metadata extraction", file=sys.stderr)
        return
    print("Extracting metadata")
    entries = os.listdir(src)
    for entry in entries:
        path = os.path.join(src, entry)
        if not os.path.isfile(path):
            print(f"Skipping {entry}, not a file!")
            continue
        print(f"Converting {entry}")
        output = os.path.join(dst, os.path.splitext(entry)[0] + '.txt')
        stream = (
            FFmpeg()
            .option("y")
            .input(path)
            .output(output, f='ffmetadata')
        )
        stream.execute()


def extract_frames(src: str, dst: str, fmt: str):
    if not os.path.isfile(src):
        print(f"Skipping {src}, not a file!")
        return
    print(f"Converting {src}")
    try:
        os.mkdir(dst)
    except FileExistsError:
        pass
    dest = os.path.join(dst, f"frame%08d.{fmt}")
    ffmpeg = (
        FFmpeg()
        .option("y")
        .input(src)
        .output(dest, {
                    "qscale:v": 1,
                    "qmin": 1,
                    "qmax": 1,
                    "vsync": 0
                })
    )

    ffmpeg.on("progress", on_progress)
    ffmpeg.on("completed", on_completed)

    ffmpeg.execute()


def upscale(src: str, dst: str, fmt: str, gpu: str = 'auto',
            scale: str = '4', model: str = 'realesr-animevideov3'):
    # realesrgan-ncnn-vulkan -i tmp_frames/ -o out_frames/ -f png -s 2 -n realesr-animevideov3 -g 0
    try:
        os.mkdir(dst)
    except FileExistsError:
        pass
    command = [
        '/usr/bin/realesrgan-ncnn-vulkan',
        '-i', src,
        '-o', dst,
        '-f', fmt,
        '-s', scale,
        '-n', model,
        '-g', gpu]
    print(f"Upscaling {src}")
    frame = 0
    with subprocess.Popen(command, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          bufsize=1,
                          universal_newlines=True) as p:
        for line in p.stdout:
            output = line.rstrip()
            output = output.lstrip()
            if output == "0.00%":
                frame += 1
            if output[0] == '[':
                print(output)
            else:
                print(f"\rOn frame: ~{frame}", end='')
                # print(f"\r{output}", end='', sep='')
    print("Done")


def main():
    parser = argparse.ArgumentParser(prog='upscale',
                                     description="Upscale multiple files")
    parser.add_argument('action', help="Action to perform")
    parser.add_argument('-i', '--input', help="Source folder for the command")
    parser.add_argument('-o', '--output', help="Output folder for the command")
    parser.add_argument('-f', '--format',  default="jpg",
                        help="Intermediate format to use for upscaling,\
                         commonly jpg or png")
    parser.add_argument('-g', '--gpu', default='auto',
                        help="Select what GPUs to for upscaling, (default=auto) can be 0,1,2 for multi-gpu")
    parser.add_argument('-s', '--scale', default='4',
                        help='upscale ratio (can be 2, 3, 4. default=4)')
    parser.add_argument('-n', '--model-name', default='realesr-animevideov3',
                        help="model name (default=realesr-animevideov3, can be realesr-animevideov3 | realesrgan-x4plus | realesrgan-x4plus-anime | realesrnet-x4plus)")
    args = parser.parse_args()
    if args.format not in ["png", "jpg", "jpeg"]:
        print(f"Format {args.format} is not a valid output format")
        return

    match args.action:
        case "extract_metadata":
            extract_metadata(args.input, args.output)
        case "extract_frames":
            entries = os.listdir(args.input)
            for entry in entries:
                src_folder = os.path.join(args.input, entry)
                dest_folder = os.path.join(args.output, os.path.splitext(entry)[0])
                extract_frames(src_folder, dest_folder, args.format)
        case "upscale":
            entries = os.listdir(args.input)
            for entry in entries:
                src_folder = os.path.join(args.input, entry)
                dest_folder = os.path.join(args.output, entry)
                if not os.path.isfile(src_folder):
                    src_folder = f"{src_folder}/"
                if not os.path.isfile(dest_folder):
                    dest_folder = f"{dest_folder}/"
                upscale(src_folder, dest_folder, args.format,
                        gpu=args.gpu, scale=args.scale, model=args.model_name)
        case "bulk":
            print("Run bulk action")
        case "test":
            print("test")
        case _:
            print(f"Not a valid command: \"{args.action}\"\n\n", file=sys.stderr)
            parser.print_help()
            exit(1)


if __name__ == "__main__":
    main()
