"""Operator entry point. The default opens a local, hardware-free panel preview."""

import argparse
import os
import webbrowser
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(prog="entity", description="Entity by Sentient")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("preview", help="Open the interactive TS24 preview on this computer")
    control = sub.add_parser(
        "mcp", help="Start the on-demand Entity MCP and read-only panel"
    )
    control.add_argument("--port", type=int, default=8048)
    control.add_argument(
        "--hot-start",
        action="store_true",
        help="Reconnect with the saved calibration if the rig is still parked",
    )
    args = parser.parse_args()
    if args.command in (None, "preview"):
        source = (
            Path(__file__).resolve().parents[1] / "static" / "entity" / "index.html"
        )
        url = source.as_uri()
        print(f"Entity by Sentient · {url}")
        webbrowser.open(url)
        return
    if not 1 <= args.port <= 65534:
        parser.error("Use a port between 1 and 65534.")
    os.environ["ENTITY_ON_DEMAND"] = "1"
    os.environ["PHYSICLAW_DISABLE_UPDATE_CHECK"] = "1"
    from physiclaw.common import config
    from physiclaw.common.proxy import normalize_proxy_env

    normalize_proxy_env()
    config.load()
    from physiclaw.cli.server import server

    print(f"Entity by Sentient · http://127.0.0.1:{args.port}/entity/", flush=True)
    server(
        host="127.0.0.1",
        port=args.port,
        no_runtime=True,
        no_setup_hardware=True,
        hot_start=args.hot_start,
    )


if __name__ == "__main__":
    main()
