"""Render the Entity panel against Makerbase's LVGL 6.1 host build."""

import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("render.py MAKERBASE_CHECKOUT OUTPUT_DIRECTORY")
    panel = Path(__file__).resolve().parents[1]
    library = Path(sys.argv[1]).resolve() / "Firmware/libraries/lvgl"
    output = Path(sys.argv[2]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp)
        conf = (library / "lv_conf.h").read_text(encoding="utf-8")
        for key, value in (
            ("LV_TICK_CUSTOM", "0"),
            ("LV_HOR_RES_MAX", "(320)"),
            ("LV_VER_RES_MAX", "(240)"),
        ):
            conf, replacements = re.subn(
                r"(?m)^(#define " + key + r"\s+)[^/\n]+",
                lambda match, replacement=value: match[1] + replacement,
                conf,
            )
            if replacements != 1:
                raise ValueError("Unexpected LVGL configuration: " + key)
        (build / "lv_conf.h").write_text(conf, encoding="utf-8")
        flags = [
            os.environ.get("CC", "cc"),
            "-std=gnu11",
            "-include",
            "stdlib.h",
            "-DLV_CONF_INCLUDE_SIMPLE",
            "-I" + str(build),
            "-I" + str(library / "src"),
            "-I" + str(panel),
        ]
        sources = [
            *sorted((library / "src/src").rglob("*.c")),
            *sorted(panel.glob("*.c")),
        ]

        def compile_source(pair):
            i, source = pair
            obj = build / f"{i}.o"
            subprocess.run([*flags, "-c", str(source), "-o", str(obj)], check=True)
            return str(obj)

        with ThreadPoolExecutor(max_workers=min(6, os.cpu_count() or 1)) as pool:
            objects = list(pool.map(compile_source, enumerate(sources)))
        executable = build / "render"
        subprocess.run(
            [
                *flags,
                str(panel / "host/check.c"),
                *objects,
                "-lm",
                "-o",
                str(executable),
            ],
            check=True,
        )
        subprocess.run([str(executable), str(output)], check=True)


if __name__ == "__main__":
    main()
