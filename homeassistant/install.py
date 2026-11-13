#!/usr/bin/env python3
"""Creates or updates the Note 4C's Home Assistant side through Home Assistant's API.

Everything ends up managed in the UI: the Note4C to-do list, the input_text helpers, and the
scripts and automations from note4c_screen.yaml. Running it again updates them. It never deletes
anything, and it leaves alone whatever is already defined in YAML, such as an older package.

The screen data automation keeps the variables (your entities) it already has in Home Assistant.
On a first install, set them in note4c_screen.yaml first, or change them in the UI afterwards.

Needs PyYAML (pip install pyyaml). Set HA_URL (default http://homeassistant.local:8123) and
HA_TOKEN, a long-lived access token for an administrator (Profile, then Security), then run:

    python homeassistant/install.py
"""
import base64
import json
import os
import pathlib
import socket
import ssl
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

TODO_LIST = "Note4C"  # Becomes todo.note4c, which note4c_screen.yaml uses.
TODO_ENTITY = "todo.note4c"
OFF_ON_CREATE = {"note4c_mirror_ha_notifications"}  # Created turned off. See note4c_screen.yaml.

URL = os.environ.get("HA_URL", "http://homeassistant.local:8123").rstrip("/")
TOKEN = os.environ.get("HA_TOKEN")


def rest(method, path, body=None):
    request = urllib.request.Request(
        URL + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")


class WebSocket:
    """Just enough of a WebSocket client for Home Assistant's API, with the standard library."""

    def __init__(self, url):
        parts = urllib.parse.urlsplit(url)
        secure = parts.scheme == "https"
        port = parts.port or (443 if secure else 80)
        sock = socket.create_connection((parts.hostname, port), timeout=30)
        if secure:
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=parts.hostname)
        self.sock = sock
        key = base64.b64encode(os.urandom(16)).decode()
        sock.sendall(
            (
                f"GET /api/websocket HTTP/1.1\r\nHost: {parts.netloc}\r\nUpgrade: websocket\r\n"
                f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        header = b""
        while b"\r\n\r\n" not in header:
            chunk = sock.recv(1)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed")
            header += chunk
        if b" 101 " not in header.split(b"\r\n", 1)[0]:
            raise ConnectionError(header.split(b"\r\n", 1)[0].decode())
        self.next_id = 1
        self.receive()  # auth_required
        self.send({"type": "auth", "access_token": TOKEN})
        if self.receive().get("type") != "auth_ok":
            raise PermissionError("Home Assistant didn't accept the token")

    def _read(self, count):
        data = b""
        while len(data) < count:
            chunk = self.sock.recv(count - len(data))
            if not chunk:
                raise ConnectionError("WebSocket closed")
            data += chunk
        return data

    def send(self, message):
        payload = json.dumps(message).encode()
        header = bytes([0x81])
        if len(payload) < 126:
            header += bytes([0x80 | len(payload)])
        elif len(payload) < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", len(payload))
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", len(payload))
        mask = os.urandom(4)
        self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def receive(self):
        message = b""
        while True:
            first, second = self._read(2)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._read(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._read(8))[0]
            message += self._read(length)
            if first & 0x80:
                return json.loads(message)

    def call(self, message_type, **data):
        message_id = self.next_id
        self.next_id += 1
        self.send({"id": message_id, "type": message_type, **data})
        while True:
            reply = self.receive()
            if reply.get("id") == message_id and reply.get("type") == "result":
                if not reply["success"]:
                    raise RuntimeError(f"{message_type}: {reply['error']['message']}")
                return reply["result"]


def entity_exists(entity_id):
    status, _ = rest("GET", f"/api/states/{entity_id}")
    return status == 200


def ensure_todo_list(ws):
    entries = ws.call("config_entries/get", domain="local_todo")
    if not any(entry["title"] == TODO_LIST for entry in entries):
        status, flow = rest("POST", "/api/config/config_entries/flow", {"handler": "local_todo"})
        if status != 200:
            sys.exit(f"Couldn't start adding the to-do list: {flow}")
        status, result = rest(
            "POST", f"/api/config/config_entries/flow/{flow['flow_id']}", {"todo_list_name": TODO_LIST}
        )
        if status != 200 or result.get("type") != "create_entry":
            sys.exit(f"Couldn't add the to-do list: {result}")
        print(f"created the {TODO_LIST} to-do list")
        for _ in range(20):
            if entity_exists(TODO_ENTITY):
                break
            time.sleep(0.5)
    if not entity_exists(TODO_ENTITY):
        sys.exit(f"The {TODO_LIST} to-do list isn't {TODO_ENTITY}. Rename its entity, then run this again.")
    print(f"{TODO_ENTITY} is ready")


def ensure_input_texts(ws, helpers):
    managed = {item["id"]: item for item in ws.call("input_text/list")}
    for helper_id, config in helpers.items():
        if helper_id in managed:
            ws.call("input_text/update", input_text_id=helper_id, **config)
            print(f"updated input_text.{helper_id}")
        elif entity_exists(f"input_text.{helper_id}"):
            print(f"left input_text.{helper_id} alone: it's defined in YAML")
        else:
            created = ws.call("input_text/create", **config)
            if created["id"] != helper_id:
                sys.exit(f"input_text.{helper_id} came out as input_text.{created['id']}. Check its name.")
            print(f"created input_text.{helper_id}")


def ensure_config(kind, item_id, config, exists):
    """Writes a script or automation into the UI's config. kind is "script" or "automation".

    Returns True when it was created. exists() says whether Home Assistant already has it, which
    without a UI config means it's defined in YAML."""
    status, existing = rest("GET", f"/api/config/{kind}/config/{item_id}")
    if status != 200 and exists():
        print(f"left {kind} {item_id} alone: it's defined in YAML")
        return False
    created = status != 200
    if not created and isinstance(existing, dict) and "variables" in existing and "variables" in config:
        config = {**config, "variables": existing["variables"]}  # Your entities, set in the UI.
    status, result = rest("POST", f"/api/config/{kind}/config/{item_id}", config)
    if status != 200:
        sys.exit(f"Couldn't save {kind} {item_id}: {result}")
    print(f"{'created' if created else 'updated'} {kind} {item_id}")
    return created


def automation_entity(automation_id, wait=False):
    """Finds an automation's entity by its id, as its entity id comes from the alias."""
    for _ in range(20 if wait else 1):
        status, states = rest("GET", "/api/states")
        for state in states if status == 200 else []:
            if state["entity_id"].startswith("automation.") and state["attributes"].get("id") == automation_id:
                return state["entity_id"]
        if wait:
            time.sleep(0.5)
    return None


def main():
    if not TOKEN:
        sys.exit("Set HA_TOKEN to a long-lived access token first.")
    package = yaml.safe_load(pathlib.Path(__file__).with_name("note4c_screen.yaml").read_text(encoding="utf-8"))
    ws = WebSocket(URL)
    ensure_todo_list(ws)
    ensure_input_texts(ws, package["input_text"])
    for script_id, config in package["script"].items():
        ensure_config("script", script_id, config, lambda: entity_exists(f"script.{script_id}"))
    for config in package["automation"]:
        automation_id = config["id"]
        created = ensure_config("automation", automation_id, config, lambda: automation_entity(automation_id))
        if created and automation_id in OFF_ON_CREATE:
            entity_id = automation_entity(automation_id, wait=True)
            if entity_id:
                rest("POST", "/api/services/automation/turn_off", {"entity_id": entity_id})
                print(f"turned off {entity_id}. Turn it on to use it.")
    print("done")


if __name__ == "__main__":
    main()
