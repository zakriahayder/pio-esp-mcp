# embedded-mcp-bridge

A bridge that lets Claude interact with physical hardware. You can ask claude 
to compile firmware, flash it to your ESP32 and then read sensors or toggle outputs. All of this happens without leaving the conversation with CC!

## Requirements

- Python 3.11+
- [PlatformIO Core](https://docs.platformio.org/en/latest/core/installation/index.html)
- ESP32 dev board

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Implementation Plan
- Setup basic project structure