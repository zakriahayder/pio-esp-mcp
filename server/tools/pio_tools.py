import json
import os
import time

import serial
from mcp.server.fastmcp import FastMCP

from server.schemas import BuildResult, CommandResult, MonitorResult
from server.utils.error_parser import parse_errors
from server.utils.pio_runner import run_pio


def register_pio_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    def pio_init(
        project_path,
        board="esp32dev",
        sample_code=False,
    ):
        """Initialize a PlatformIO project directory and generate platformio.ini.

        Use this when you are asked to create a new PlatformIO project.
        Prefer this over manually writing platformio.ini from scratch. After the
        project exists, the assistant can edit src/main.cpp as needed, then call
        pio_build and pio_upload.
        """
        os.makedirs(project_path, exist_ok=True)
        args = ["project", "init", "--project-dir", project_path, "--board", board]
        if sample_code:
            args.append("--sample-code")
        result = run_pio(args)
        response = CommandResult(
            success=result["returncode"] == 0,
            stdout=result["stdout"],
            stderr=result["stderr"],
        )
        return response.model_dump()

    @mcp.tool()
    def pio_build(
        project_path: str,
    ) -> dict:
        """Build firmware in a PlatformIO project directory.

        Use this when firmware needs to be compiled before uploading to the ESP32.
        If the next goal is to discover the board's IP address, build first, then
        upload, then monitor serial output.
        """
        result = run_pio(["run"], cwd=project_path)
        success = result["returncode"] == 0
        response = BuildResult(
            success=success,
            stdout=result["stdout"],
            stderr=result["stderr"],
            errors=[] if success else parse_errors(result["stderr"]),
        )
        return response.model_dump()

    @mcp.tool()
    def pio_upload(
        project_path,
        port=None,
    ):
        """Upload compiled firmware to a connected ESP32 over serial.

        Use this after pio_build when the board needs new firmware. If  you need
        the ESP32 IP address, upload first when needed and then use
        pio_monitor_serial to read boot logs and discover it.
        """
        args = ["run", "-t", "upload"]
        if port:
            args += ["--upload-port", port]
        result = run_pio(args, cwd=project_path)
        response = CommandResult(
            success=result["returncode"] == 0,
            stdout=result["stdout"],
            stderr=result["stderr"],
        )
        return response.model_dump()

    @mcp.tool()
    def pio_list_devices() -> dict:
        """List connected serial devices and candidate ESP32 ports.

        Use this first when the you needs to identify which ESP32 is connected.
        The returned port should usually be passed into pio_monitor_serial or
        pio_upload. This is the first step for discovering the board's IP address.
        """
        result = run_pio(["device", "list", "--json-output"])
        if result["returncode"] != 0:
            return {"success": False, "devices": [], "error": result["stderr"]}
        try:
            devices = json.loads(result["stdout"])
        except json.JSONDecodeError:
            devices = []
        return {"success": True, "devices": devices}

    @mcp.tool()
    def pio_monitor_serial(
        port: str,
        baud: int = 115200,
        duration_ms: int = 5000,
    ) -> dict:
        """Read serial output from a connected device for a short time window.

        Use this immediately after pio_list_devices to inspect boot logs, Wi-Fi
        status, and especially the ESP32 IP address. When an IP address is needed
        for esp_connect, prefer this tool over asking the user.
        """
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=1)
            lines: list[str] = []
            deadline = time.monotonic() + duration_ms / 1000
            while time.monotonic() < deadline:
                raw = ser.readline()
                if raw:
                    lines.append(raw.decode("utf-8", errors="replace").rstrip())
            ser.close()
            response = MonitorResult(success=True, output="\n".join(lines))
            return response.model_dump()
        except serial.SerialException as e:
            response = MonitorResult(success=False, output="", error=str(e))
            return response.model_dump()

    @mcp.tool()
    def pio_serial_command(
        port: str,
        command: str,
        baud: int = 115200,
        wait_for: str | None = None,
        timeout: int = 10,
    ) -> dict:
        """Send a command over serial and return the device's response.

        If wait_for is provided, lines are collected until that terminator string
        appears in a line or the timeout is reached. Otherwise, output is collected
        for a fixed 2-second window. Returns all received lines joined as a single
        string in the response field.
        """
        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=1)
        except serial.SerialException as e:
            return {
                "success": False,
                "response": "",
                "error": (
                    f"Could not open port {port!r}: {e}. "
                    "Run pio_list_devices to check available ports."
                ),
            }

        try:
            ser.reset_input_buffer()
            ser.write((command + "\n").encode("utf-8"))
            lines: list[str] = []
            read_until = time.monotonic() + (timeout if wait_for else 2)
            while time.monotonic() < read_until:
                line = ser.readline().decode("utf-8", errors="replace").rstrip()
                if line:
                    lines.append(line)
                    if wait_for and wait_for in line:
                        break
                elif not wait_for:
                    break
        finally:
            ser.close()

        return {"success": True, "response": "\n".join(lines), "error": None}
