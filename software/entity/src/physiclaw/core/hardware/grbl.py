"""Auto-detect GRBL devices on serial ports."""

import errno
import logging
import os
import time

import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

from physiclaw.common.logger.evidence import record_event
from physiclaw.core.hardware.device import (
    DeviceTimeout,
    MksConnectionError,
    ProtocolError,
)
from physiclaw.core.hardware.transport import SerialTransport

log = logging.getLogger(__name__)

GRBL_BAUDRATE = 115200


def open_mks_port(port: str, baudrate: int) -> serial.Serial:
    """Open Alfonsito's configured CH340 with the ESP32 boot lines inactive."""
    ser = serial.Serial(
        None, baudrate, timeout=3, write_timeout=3,
        exclusive=True if os.name == "posix" else None,
    )
    try:
        # Supplying a port to the constructor asserts DTR/RTS before we can
        # change them. On this board that can leave GRBL silent at startup.
        ser.dtr = False
        ser.rts = False
        ser.port = port
        ser.open()
        return ser
    except OSError as exc:
        ser.close()
        code = {
            errno.ENOENT: "arm_usb_missing",
            errno.ENODEV: "arm_usb_missing",
            errno.EBUSY: "arm_usb_busy",
            errno.EAGAIN: "arm_usb_busy",
            errno.EACCES: "arm_usb_access",
            errno.EPERM: "arm_usb_access",
        }.get(exc.errno, "arm_usb_io")
        raise MksConnectionError(code, f"Cannot open the configured MKS USB port: {exc}") from exc


def identify_mks(transport: SerialTransport) -> None:
    """Identify the board on the handle that will also drive it."""
    identity: list[str] = []
    try:
        transport.send("$I", diagnostics=identity, diagnostic_prefix="[MSG:Using machine:")
    except DeviceTimeout as exc:
        raise MksConnectionError("arm_no_reply", "The USB port opened but the MKS did not answer.") from exc
    except ProtocolError as exc:
        raise MksConnectionError("arm_identity", "The USB device did not return an MKS identity.") from exc
    except OSError as exc:
        raise MksConnectionError("arm_usb_io", "The USB connection was lost during identification.") from exc
    if not any(line.casefold() == "[msg:using machine:mks dlc32]" for line in identity):
        raise MksConnectionError("arm_identity", "The USB device did not identify as an MKS DLC32.")

# Skip ports that are never GRBL devices
_SKIP_KEYWORDS = {"bluetooth", "bt-", "debug", "wlan", "wifi", "airpods"}

# GRBL boards typically use CH340/CP210x/FTDI USB-serial chips. Match on
# both macOS-style device names (`/dev/tty.usbserial-XXXX`) and Windows-style
# port descriptions (`USB-SERIAL CH340 (COM3)`, `Arduino Uno (COM5)`).
_LIKELY_KEYWORDS = {
    "ch340",
    "cp210",
    "ftdi",
    "usbserial",
    "usbmodem",
    "wch",
    "serial",
    "arduino",
    "prolific",
}

# USB vendor ids of the USB-serial bridge chips these boards use. The VID is
# identical on macOS, Windows and Linux no matter how the port is named, so
# it's the most reliable cross-platform signal. The MKS DLC32 V2.1 is a CH340
# (0x1A86); the rest cover other common GRBL/ESP32 boards.
_LIKELY_VIDS = frozenset(
    {
        0x1A86,  # QinHeng CH340/CH341 — MKS DLC32 V2.1
        0x10C4,  # Silicon Labs CP210x
        0x0403,  # FTDI
        0x067B,  # Prolific PL2303
        0x303A,  # Espressif — native-USB ESP32-S2/S3/C3
    }
)


def _probe_port(port: str, baudrate: int = GRBL_BAUDRATE) -> str | None:
    """Try to connect to a port and identify a GRBL device.

    Uses $I query (no reset side-effect, faster than soft-reset).
    Returns the version string if GRBL is detected, None otherwise.
    """
    try:
        with serial.Serial(port, baudrate, timeout=0.4, write_timeout=2) as ser:
            # The DLC32 touchscreen can boot twice after USB open. Keep the
            # banner and fragmented replies, and retry identification on this
            # same handle rather than triggering another reset on each retry.
            reply = b""
            for _ in range(8):
                ser.write(b"$I\n")
                time.sleep(0.5)
                reply = (reply + ser.read(min(ser.in_waiting or 256, 2048)))[-4096:]
                for line in reply.decode("ascii", errors="ignore").splitlines():
                    if "grbl" in line.lower() or "[VER:" in line:
                        record_event(
                            "arm.serial_probe_reply",
                            port=port,
                            baudrate=baudrate,
                            reply=line,
                        )
                        return line.strip()
            record_event(
                "arm.serial_probe_reply",
                port=port,
                baudrate=baudrate,
                reply=reply.decode("ascii", errors="replace"),
            )
    except (serial.SerialException, OSError) as exc:
        record_event(
            "arm.serial_probe_failed",
            port=port,
            baudrate=baudrate,
            exception_type=type(exc).__name__,
            message=str(exc),
        )
    return None


def _port_priority(port_info: ListPortInfo) -> int:
    """Lower value = probe first. Likely USB-serial chips first, unlikely ports last."""
    vid = getattr(port_info, "vid", None)
    # Built-in / virtual UARTs (Linux /dev/ttyS*, Pi /dev/ttyAMA*, motherboard
    # COM ports) report no USB vendor id and are never the GRBL board — a real
    # USB-serial adapter always has one. Skip them so we don't auto-pick a
    # phantom port like /dev/ttyS0 when the board isn't connected/powered.
    if vid is None:
        return 99
    name = (port_info.device + " " + (port_info.description or "")).lower()
    if any(kw in name for kw in _SKIP_KEYWORDS):
        return 99  # bluetooth / wifi / debug — skip
    # A known USB-serial VID, or a chip keyword in the name, → most likely GRBL.
    # VID is checked first because it's the same across all OSes; the keyword
    # fallback catches clone chips with an unlisted VID.
    if vid in _LIKELY_VIDS or any(kw in name for kw in _LIKELY_KEYWORDS):
        return 0
    return 50  # some other USB device — probe after likely ones


def _candidate_port_infos() -> list[ListPortInfo]:
    """port_info objects that look worth probing (skipping bluetooth/debug etc.).

    Sorted by likelihood — likely USB-serial chips first. Shared by
    detect_grbl() (which probes them) and candidate_ports() (diagnostics).
    """
    return sorted(
        [p for p in serial.tools.list_ports.comports() if _port_priority(p) < 99],
        key=lambda p: (_port_priority(p), p.device),
    )


def candidate_ports() -> list[str]:
    """Device names that detect_grbl() would probe. For diagnostics."""
    return [p.device for p in _candidate_port_infos()]


def detect_grbl() -> str | None:
    """Scan serial ports and return the first GRBL device port, or None.

    Skips Bluetooth/debug ports and probes likely USB-serial ports first.
    """
    ports = _candidate_port_infos()
    record_event(
        "arm.serial_candidates",
        ports=[
            {
                "device": p.device,
                "description": p.description,
                "vid": p.vid,
                "pid": getattr(p, "pid", None),
            }
            for p in ports
        ],
    )
    if not ports:
        log.warning(
            "[GRBL] no candidate serial ports found",
            extra={"console_message": "Arm not found — check its USB cable and power"},
        )
        return None

    log.debug(f"[GRBL] scanning {len(ports)} serial port(s)")
    for port_info in ports:
        desc = port_info.description or ""
        log.debug(f"[GRBL] trying {port_info.device} ({desc})")

        version = _probe_port(port_info.device)
        if version:
            log.debug("GRBL found on %s [%s]", port_info.device, version)
            return port_info.device
        else:
            log.debug(f"[GRBL] {port_info.device} didn't answer")

    return None
