import argparse
import sys
import os
import time
from datetime import datetime, timedelta
import json
from ffmpeg import FFmpeg, Progress


def on_progress(progress: Progress):
    days, hours, minutes, seconds = extract_timedelta(progress.time)
    print(f"\rframe: {progress.frame} fps: {progress.fps} time: {days} days, {hours:02d}:{minutes:02d}:{seconds:02d}", end="")


def on_completed():
    print("")


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def extract_timedelta(delta: timedelta):
    days = delta.days
    hours, seconds = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return days, hours, minutes, seconds


def extract_metadata(src: str, dst: str):
    print(src)
    print(dst)
    if not src or not dst:
        print("Both src and dst are expected for metadata extraction",
              file=sys.stderr)
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


def query_metadata(file: str):
    ffprobe = FFmpeg(executable="ffprobe").input(
        file,
        print_format="json",
        show_streams=None,
    )
    metadata = json.loads(ffprobe.execute())

    return metadata


def reencode(src: str, dst: str):
    ffmpeg = (
        FFmpeg()
        .option("y")
        .input(src)
    )
    arguments = {
        # 'codec:v': 'librav1e',
        'codec:v': 'libsvtav1',
        # 'codec:v': 'av1_amf',
        'pix_fmt': 'yuv420p',
        'crf': 38,
        # 'qp': 30,
        'preset': 6,
        # 'speed': 4,
        # 'tile-columns': 2,
        # 'tile-rows': 2,
    }
    map = ["0:0"]
    ffmpeg.output(
        dst,
        arguments,
        map=map
    )

    ffmpeg.on("progress", on_progress)
    ffmpeg.on("completed", on_completed)

    ffmpeg.execute()


def main():
    parser = argparse.ArgumentParser(prog='upscale',
                                     description="Upscale multiple files")
    parser.add_argument('-i', '--input', help="Source folder for the command")
    parser.add_argument('-o', '--output', help="Output folder for the command")
    args = parser.parse_args()

    entries = os.listdir(args.input)
    for entry in entries:
        src = os.path.join(args.input, entry)
        dst = os.path.join(args.output, os.path.splitext(entry)[0] + '.mp4')
        print(f"Input: {src}")
        print(f"Output: {dst}")
        metadata = query_metadata(src)
        print(f"Source:\n\tDuration: {metadata['streams'][0]['duration']}\n\tResolution: {metadata['streams'][0]['width']}x{metadata['streams'][0]['height']}")
        datetime_start = datetime.now()
        time_start = time.time()
        # dst = os.path.join(args.output, entry)
        reencode(src, dst)
        time_end = time.time()
        datetime_end = datetime.now()
        elapsed = time_end - time_start
        src_file = os.stat(src)
        dst_file = os.stat(dst)
        factor = src_file.st_size/dst_file.st_size
        print(f"Encoded {entry} in {elapsed:.1f} seconds\nStart: {datetime_start.strftime('%Y-%m-%d %H:%M:%S')}\nEnd: {datetime_end.strftime('%Y-%m-%d %H:%M:%S')}\nOld size: {sizeof_fmt(src_file.st_size)}\nNew size: {sizeof_fmt(dst_file.st_size)}\nFactor: {factor:.2f}x smaller\n")


if __name__ == "__main__":
    main()
