# /// script
# requires-python = ">=3.12"
# dependencies = ["mcp==2.3.0"]
# ///
"""Alfonsito's authenticated operator queue, exposed to a local MCP client."""

import getpass
import http.client
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

HOST = "entity.livinginacat.world"
ORIGIN = "https://" + HOST
COOKIE = "__Host-entity_session"
TASKS = "/entity/api/tasks"
LOGIN_FILE = Path.home() / ".config" / "entity" / "alfonsito-login.txt"


def credentials():
    user = os.getenv("ENTITY_OPERATOR_USER")
    password = os.getenv("ENTITY_OPERATOR_PASSWORD")
    if user and password:
        return user, password
    if not (user or password) and LOGIN_FILE.is_file():
        if LOGIN_FILE.stat().st_mode & 0o077:
            raise ValueError("Use chmod 600 on " + str(LOGIN_FILE))
        fields = {}
        for line in LOGIN_FILE.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition(" = ")
            if sep:
                fields[key] = value
        if fields.get("Usuario") and fields.get("Contraseña"):
            return fields["Usuario"], fields["Contraseña"]
    raise ValueError(
        "Configurá el acceso con --login. Configure operator access with --login."
    )


def configure_login():
    user = input("Usuario / Username: ").strip()
    password = getpass.getpass("Contraseña / Password: ")
    if not user or not password or any(c in user + password for c in "\r\n"):
        raise ValueError(
            "Usuario y contraseña requeridos. Username and password required."
        )
    LOGIN_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=LOGIN_FILE.parent, delete=False, encoding="utf-8"
    ) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(f"{ORIGIN}\nUsuario = {user}\nContraseña = {password}\n")
            stream.flush()
            os.replace(temporary, LOGIN_FILE)
        finally:
            temporary.unlink(missing_ok=True)
    print("Acceso guardado en este equipo. Operator login saved on this computer.")


class OperatorPortal:
    def __init__(self):
        self.token = None

    def request(self, method, path, body=None, content_type=None):
        headers = {"Accept": "application/json", "User-Agent": "Entity-Operator-MCP/1"}
        if body is not None:
            headers.update({"Origin": ORIGIN, "Content-Type": content_type})
        if self.token:
            headers["Cookie"] = f"{COOKIE}={self.token}"
        connection = http.client.HTTPSConnection(HOST, timeout=25)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, response.headers, response.read()
        finally:
            connection.close()

    def login(self):
        user, password = credentials()
        body = urlencode({"username": user, "password": password}).encode("ascii")
        status, headers, _ = self.request(
            "POST", "/auth/login", body, "application/x-www-form-urlencoded"
        )
        cookie = SimpleCookie()
        cookie.load(headers.get("Set-Cookie", ""))
        token = cookie[COOKIE].value if COOKIE in cookie else ""
        if status != 303 or not re.fullmatch(r"[0-9a-f]{64}", token):
            raise RuntimeError(f"Acceso de operador / Operator sign-in: HTTP {status}")
        self.token = token

    def queue(self, action=None):
        payload = (
            None
            if action is None
            else json.dumps(action, ensure_ascii=False).encode("utf-8")
        )
        method = "GET" if payload is None else "POST"
        for attempt in range(2):
            if self.token is None:
                self.login()
            status, _, raw = self.request(method, TASKS, payload, "application/json")
            if status == 401 and attempt == 0:
                self.token = None
                continue
            try:
                data = json.loads(raw)
            except (ValueError, UnicodeError):
                data = {}
            if status != 200 or not isinstance(data, dict) or "queue" not in data:
                reason = data.get("error", "") if isinstance(data, dict) else ""
                code = (
                    reason
                    if isinstance(reason, str)
                    and re.fullmatch(r"[a-z0-9_]{1,48}", reason)
                    else ""
                )
                raise RuntimeError(f"Alfonsito HTTP {status} {code}".strip())
            return data


def scheduled_epoch(value):
    if value is None:
        return None
    moment = datetime.fromisoformat(value)
    if moment.utcoffset() is None:
        raise ValueError("Incluí la zona horaria. Include a time-zone offset or Z.")
    return int(moment.timestamp())


portal = OperatorPortal()
server = MCPServer(
    "Alfonsito · Entity by Sentient",
    instructions=(
        "Use alfonsito_estado first to read live readiness and the shared queue. "
        "A status request never authorizes sending or changing a task. When the operator requests "
        "work, submit it once with a stable request key, reusing that key on retries. "
        "The Raspberry executes authorized work and updates the web dashboard and physical MKS. "
        "An accepted task is queued. Report completion from its actual state and result. "
        "Respond in the operator's language."
    ),
)


@server.tool(annotations=ToolAnnotations(readOnlyHint=True))
def alfonsito_estado() -> dict:
    """Lee la disponibilidad, la tarea actual, la cola y el último resultado. Read live state and queue."""
    return portal.queue()


@server.tool()
def alfonsito_enviar(
    instruccion: str, solicitud_id: str, cuando: str | None = None
) -> dict:
    """Agrega una tarea autorizada. Submit one requested task. Reuse solicitud_id (8–80 letters, digits, dash or underscore) on retries. Optional cuando is ISO 8601 with offset."""
    return portal.queue(
        {
            "action": "add",
            "instructions": instruccion,
            "request_id": solicitud_id,
            "run_at": scheduled_epoch(cuando),
        }
    )


@server.tool()
def alfonsito_mover(id: int, vecino: int, direccion: Literal["up", "down"]) -> dict:
    """Sube o baja una tarea pendiente un puesto. Move a queued task past its adjacent neighbor from alfonsito_estado."""
    return portal.queue(
        {"action": "move", "id": id, "neighbor": vecino, "direction": direccion}
    )


@server.tool()
def alfonsito_eliminar(id: int) -> dict:
    """Quita de la cola una tarea pendiente. Remove a waiting task when requested by the operator."""
    return portal.queue({"action": "remove", "id": id})


if __name__ == "__main__":
    if sys.argv[1:] == ["--login"]:
        configure_login()
    elif not sys.argv[1:]:
        server.run(transport="stdio")
    else:
        raise SystemExit("Uso / Usage: alfonsito.py [--login]")
