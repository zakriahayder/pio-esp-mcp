# Platform IO + ESP32 MCP 

Python MCP server that lets an AI like Claude act as an embedded developer. It can write firmware, build, flash, and iterate without the user having to touch a terminal.

It also has additional ESP32 support where the AI can connect to the device over HTTP by flashing a lightweight base firmware once and perform basic GPIO operations like digital read/write, analog read, and PWM.

## Table of Contents

- [The Problem](#the-problem)
- [Where This Fits](#where-this-fits)
- [Demos](#demos)
- [Setup](#setup)
- [How It Works](#how-it-works)
- [Requirements](#requirements)

## The Problem

Embedded development has always required a human in the loop. You install an IDE, write code, hit upload, read serial output, debug, and repeat. Every step is manual and environment-dependent: the compiler, the USB, the board config all have to be set up correctly before anything works.

AI coding tools have mostly ignored this space because the feedback loop is physical. You can't just run the code and see the output, you have to flash it to hardware and observe what happens on a real device.

This project closes that loop. The AI finds the board, writes the firmware, compiles it, flashes it, reads serial output, and if needed connects over WiFi to control the device at runtime, all without the user doing anything.

## Where This Fits

Most MCP tooling targets web APIs and cloud services. Physical hardware is a different problem. The embedded dev cycle is slower, less forgiving, and harder to automate because it involves physical states. 

This project is a small but meaningful step in getting an AI to automate that cycle and towards autonomous embedded development, which has many applicattions e,g. robotics, automotive, industrial systems, etc.

## Demos

### Demo 1: AI writes and flashes LED blink firmware from scratch
The AI is given an directory and told that an ESP32 is connected over USB. 
It creates the PlatformIO project, writes C++ firmware, compiles it, and flashes it to the device, all from a single prompt.

<img width="1339" height="944" alt="image" src="https://github.com/user-attachments/assets/965a9c3a-e8d4-41a3-a6df-3906bd2675c8" />

### Demo 2: AI connects to a running ESP32 over WiFi and controls GPIO
The AI is told to connect to an ESP32 and flash is LED over http. It flashes the base firmware, reads the IP address from serial output, connects over HTTP, and turns the LED ON.

<img width="727" height="483" alt="image" src="https://github.com/user-attachments/assets/2435f309-848b-4d8f-9b67-3ad10bc27a4f" />

### Demo 3: Custom device and script
The AI is given a pre-written script and the board type, and asked to flash the script to the board. It automatically builds the PlatformIO project specific to the given board, flash the script and confirms output via Serial. 

<img width="1196" height="742" alt="image" src="https://github.com/user-attachments/assets/76592dda-647f-4adb-a85b-59280757f03e" /> 

<img width="1423" height="529" alt="image" src="https://github.com/user-attachments/assets/4ea15758-0770-43b1-b436-841fdd49b12a" />

## Setup

### 1. Install PlatformIO CLI

```bash
pip install platformio
pio --version
```

### 2. Clone this repo

```bash
git clone https://github.com/yourusername/embedded-mcp-bridge.git
cd embedded-mcp-bridge
pip install -e .
```

### 3. Add to Claude Code

```bash
claude mcp add pio-esp32-mcp -- uv run python -m server.main
```

### 4. Set your WiFi credentials

Open your MCP config (the file Claude Code created in step 3) and add an `env` block:

```json
{
  "mcpServers": {
    "pio-esp32-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "server.main"],
      "cwd": "/path/to/pio-esp32-mcp",
      "env": {
        "WIFI_SSID": "your_network_name",
        "WIFI_PASSWORD": "your_password"
      }
    }
  }
}
```

These are only used when flashing the base WiFi firmware. They never leave your machine.

### 5. Verify

Restart Claude Code, run `/mcp`, confirm you see the tools.


## How It Works

### PlatformIO (any board)

Works with any board PlatformIO supports (1000+ boards).

| What Claude can do |
|--------------------|
| Create a PlatformIO project |
| Compile firmware for the connected board |
| Flash firmware to the microcontroller |
| Monitor serial output |

---

### ESP32 Runtime Control (over WiFi)

Once flashed, the ESP32 runs a tiny HTTP server. No custom firmware needed for each task. Claude uses the same 4 commands to control any GPIO hardware.

**Endpoints:**
- `GET /tools` — Claude discovers what the board can do
- `POST /call` — Claude executes a command

**Commands:**

| Command | Use case |
|---------|----------|
| `gpio_write` | LEDs, relays, buzzers |
| `gpio_read` | Buttons, motion sensors, switches |
| `adc_read` | Potentiometers, light sensors, thermistors |
| `pwm_write` | LED dimming, motor speed |

**Workflow:**
1. Flash the base WiFi firmware once
2. Monitor serial to get the IP address
3. Connect over WiFi
4. Control any GPIO device

## Requirements

- Python 3.11+
- ESP32 dev board
- USB cable

## License

MIT
