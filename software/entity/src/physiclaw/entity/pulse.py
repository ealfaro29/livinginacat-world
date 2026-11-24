"""A camera-guided, five-target game. Only the loopback director can start the robot."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import secrets
import time
from pathlib import Path

import httpx2
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

from physiclaw.entity.pulse_hardware import TOTAL, RoundEnded

ASSETS = Path(__file__).resolve().parents[1] / "static" / "entity"
MCP_URL = "http://127.0.0.1:8048/mcp"
log = logging.getLogger(__name__)


async def call(client: ClientSession, name: str, args: dict | None = None):
    result = await client.call_tool(name, args or {})
    if result.is_error:
        raise RoundEnded("offline")
    return result


def data(result) -> dict:
    return result.structured_content or json.loads(result.content[0].text)


class Pulse:
    def __init__(self, phone_url: str):
        self.phone_url = phone_url
        self.screens: dict[str, tuple[float, dict]] = {}
        self.screen_id = ""
        self.run_id = ""
        self.port = 8050
        self.phase = "ready"
        self.hits = 0
        self.running = False
        self.begin = False
        self.stop_requested = False
        self.job: asyncio.Task | None = None

    def screens_now(self) -> dict[str, dict]:
        now = time.monotonic()
        self.screens = {k: v for k, v in self.screens.items() if now - v[0] < 3.5}
        return {k: v for k, (_, v) in self.screens.items() if v["visible"]}

    def status(self) -> dict:
        live = self.screens_now()
        reason = self.phase
        manual = any(
            s["phase"] in ("playing", "countdown") and s["mode"] == "manual"
            for s in live.values()
        )
        if not self.running:
            if not live:
                reason = "no_phone"
            elif len(live) != 1:
                reason = "many"
            elif manual:
                reason = "manual"
        return {
            "reason": reason,
            "running": self.running,
            "hits": self.hits,
            "can_start": len(live) == 1 and not self.running and not manual,
            "phone_url": self.phone_url,
        }

    def current_screen(self) -> dict:
        if self.stop_requested:
            raise RoundEnded("stopped")
        screen = self.screens_now().get(self.screen_id)
        if screen is None:
            raise RoundEnded("lost")
        if screen["round"] == self.run_id and screen["phase"] == "stopped":
            raise RoundEnded("stopped")
        return screen

    async def wait_screen(self, predicate, seconds: float, failure: str) -> dict:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            screen = self.current_screen()
            if (
                screen["round"] == self.run_id
                and screen["mode"] == "entity"
                and predicate(screen)
            ):
                return screen
            await asyncio.sleep(0.10)
        raise RoundEnded(failure)

    async def play(self, client: ClientSession) -> None:
        snapshot = data(await call(client, "entity_status"))
        if not snapshot["hardware"]["ready"]:
            raise RoundEnded("offline")
        if snapshot["current"] or any((row.get("run_at") or 0) <= time.time() for row in snapshot["queue"]):
            raise RoundEnded("busy")
        screen = self.current_screen()
        title = "Jugar Pulso" if screen["lang"] == "es" else "Play Pulse"
        task = data(
            await call(
                client,
                "entity_enqueue",
                {"title": title, "request_id": "pulse-" + self.run_id},
            )
        )
        outcome = "cancelled"
        try:
            await call(client, "entity_start", {"task_id": task["id"]})
            outcome = "failed"
            self.current_screen()
            self.begin = True
            await self.wait_screen(
                lambda s: s["phase"] == "playing" and s["accepting"], 9, "lost"
            )
            self.phase = "playing"
            played = data(
                await call(
                    client,
                    "entity_play_pulse",
                    {
                        "task_id": task["id"],
                        "round_id": self.run_id,
                        "port": self.port,
                    },
                )
            )
            if played.get("reason") != "done":
                raise RoundEnded(played.get("reason", "offline"))
            screen = await self.wait_screen(
                lambda s: s["phase"] == "won" and s["hits"] == TOTAL, 2, "miss"
            )
            self.hits = screen["hits"]
            outcome = "done"
        except RoundEnded as exc:
            if exc.args == ("stopped",):
                outcome = "cancelled"
            raise
        finally:
            await call(
                client, "entity_finish", {"task_id": task["id"], "outcome": outcome}
            )

    async def run(self) -> None:
        reason = "done"
        try:
            async with (
                httpx2.AsyncClient(
                    timeout=httpx2.Timeout(60, connect=4), trust_env=False
                ) as http,
                streamable_http_client(MCP_URL, http_client=http) as (
                    rd,
                    wr,
                ),
                ClientSession(rd, wr) as client,
            ):
                # Handle an expected stop inside the MCP contexts; their
                # task groups otherwise wrap it in an ExceptionGroup.
                try:
                    await client.initialize()
                    await self.play(client)
                except RoundEnded as exc:
                    reason = str(exc)
        except Exception:
            log.exception("Pulse could not complete its MCP session")
            reason = "offline"
        finally:
            self.running = self.begin = False
            self.phase = reason

    async def phone(self, request: Request):
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > 1024:
                return Response(status_code=413)
            body.extend(chunk)
        try:
            s = json.loads(body)
            client, rid = s["client"], s["round"]
            if not (
                re.fullmatch("[a-f0-9]{24}", client)
                and (rid == "" or re.fullmatch("[a-f0-9]{24}", rid))
                and s["phase"] in ("ready", "countdown", "playing", "stopped", "won")
                and s["mode"] in ("manual", "entity")
                and s["lang"] in ("es", "en")
                and type(s["visible"]) is bool
                and type(s["accepting"]) is bool
                and type(s["hits"]) is int
                and 0 <= s["hits"] <= TOTAL
                and type(s.get("misses", 0)) is int
                and s.get("misses", 0) >= 0
            ):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            return Response(status_code=400)
        self.screens_now()
        if client not in self.screens and len(self.screens) >= 24:
            return Response(status_code=429)
        s.setdefault("misses", 0)
        self.screens[client] = (
            time.monotonic(),
            {
                k: s[k]
                for k in (
                    "round",
                    "phase",
                    "mode",
                    "lang",
                    "visible",
                    "accepting",
                    "hits",
                    "misses",
                )
            },
        )
        selected = client == self.screen_id
        if selected and self.running and rid == self.run_id and s["mode"] == "entity":
            self.hits = s["hits"]
        return JSONResponse(
            {
                "start": self.run_id
                if selected and self.running and self.begin and not self.stop_requested
                else "",
                "stop": self.run_id
                if selected
                and (self.stop_requested or (not self.running and self.phase != "done"))
                else "",
            },
            headers={"Cache-Control": "no-store"},
        )

    async def director(self, request: Request):
        if (
            not request.client
            or request.client.host not in {"127.0.0.1", "::1"}
            or request.url.hostname not in {"127.0.0.1", "localhost", "::1"}
        ):
            return Response(status_code=403)
        command = request.path_params.get("command", "")
        if not command:
            return asset("control.html")
        if command == "state" and request.method == "GET":
            return JSONResponse(self.status(), headers={"Cache-Control": "no-store"})
        if command == "session" and request.method == "GET":
            if not self.running or self.run_id != request.query_params.get("round"):
                return JSONResponse({"reason": "lost"})
            try:
                screen = self.current_screen()
            except RoundEnded as exc:
                return JSONResponse({"reason": str(exc)})
            if screen["round"] != self.run_id or screen["mode"] != "entity":
                return JSONResponse({"reason": "lost"})
            return JSONResponse(
                {k: screen[k] for k in ("hits", "misses", "phase", "accepting")},
                headers={"Cache-Control": "no-store"},
            )
        if command not in {"start", "stop"} or request.method != "POST":
            return Response(status_code=405)
        origin = request.headers.get("origin")
        if request.headers.get("x-pulse-control") != "1" or (
            origin and origin != str(request.base_url).rstrip("/")
        ):
            return Response(status_code=403)
        if command == "stop" and self.running:
            self.stop_requested = True
            self.phase = "stopping"
        elif command == "start" and self.status()["can_start"]:
            self.port = request.url.port or 80
            self.screen_id = next(iter(self.screens_now()))
            self.run_id = secrets.token_hex(12)
            self.hits, self.phase = 0, "countdown"
            self.running, self.begin, self.stop_requested = True, False, False
            self.job = asyncio.create_task(self.run())
        return JSONResponse(self.status(), headers={"Cache-Control": "no-store"})


def asset(name: str):
    base = ASSETS if name in {"sentient.svg", "space-grotesk.ttf"} else ASSETS / "pulse"
    return FileResponse(base / name, headers={"Cache-Control": "no-cache"})


def build_game(phone_url: str):
    game = Pulse(phone_url)

    async def page(request):
        return asset("index.html")

    async def files(request):
        name = request.path_params["name"]
        if name not in {
            "pulse.css",
            "pulse.js",
            "control.js",
            "sentient.svg",
            "space-grotesk.ttf",
        }:
            return Response(status_code=404)
        return asset(name)

    return Starlette(
        routes=[
            Route("/", page),
            Route("/jugar", page),
            Route("/api/phone", game.phone, methods=["POST"]),
            Route("/control", game.director),
            Route("/control/{command}", game.director, methods=["GET", "POST"]),
            Route("/{name}", files),
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--phone-url", default="http://ft412-pi.local:8050/jugar")
    args = parser.parse_args()
    uvicorn.run(
        build_game(args.phone_url),
        host=args.host,
        port=args.port,
        access_log=False,
        proxy_headers=False,
    )
