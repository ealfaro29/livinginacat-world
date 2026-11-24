#!/usr/bin/env python3
"""Stage and build the application only. This tool never opens the serial port."""

import argparse
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

PIN = "e3edf9292f511ee44223021b2b8853e31b1aabe7"
HERE = Path(__file__).resolve().parent


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "makerbase", type=Path, help="Official MKS-DLC32-FIRMWARE checkout"
    )
    parser.add_argument("output", type=Path, help="Destination .bin")
    parser.add_argument("--pio", default="pio")
    args = parser.parse_args()
    with TemporaryDirectory(prefix="entity-ts24-") as directory:
        root = Path(directory) / "makerbase"
        run(
            "git",
            "clone",
            "-q",
            "--no-checkout",
            "--local",
            str(args.makerbase.resolve()),
            str(root),
        )
        run("git", "checkout", "-q", "--detach", PIN, cwd=root)
        run(
            "git",
            "apply",
            "--whitespace=nowarn",
            str(HERE / "makerbase.patch"),
            cwd=root,
        )
        firmware = root / "Firmware"
        target = firmware / "Grbl_Esp32/src/entity"
        target.mkdir()
        for name in (
            "panel.h",
            "panel.c",
            "entity_font.c",
            "entity_wordmark_font.c",
            "mark.c",
        ):
            shutil.copy2(HERE.parent / name, target)
        for name in ("device.cpp", "device.h"):
            shutil.copy2(HERE / name, target)
        shutil.copy2(HERE / "platformio.ini", firmware / "entity.ini")
        run(args.pio, "run", "-c", "entity.ini", "-e", "entity_ts24", cwd=firmware)
        image = firmware / ".pio/build/entity_ts24/firmware.bin"
        if not 0 < image.stat().st_size <= 0x300000 or image.read_bytes()[0] != 0xE9:
            raise RuntimeError("Invalid ESP32 application partition image")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image, args.output)


if __name__ == "__main__":
    main()
