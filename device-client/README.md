# HoloHub Device Client

Device client software for HoloHub holographic display management system.

## Features

- ✅ **Device Authentication** - Secure authentication with HoloHub backend
- ✅ **Heartbeat Monitoring** - Regular health status updates
- ✅ **Content Download** - Automatic content caching and updates
- ✅ **Playlist Execution** - Scheduled content playback
- ✅ **Command Handling** - Remote commands (refresh, reboot, etc.)
- ✅ **Multiple Display Support** - Looking Glass, Hypervsn, and more
- ✅ **Simulation Mode** - Test without real hardware

## Supported Hardware

### Looking Glass Factory Displays
- Looking Glass Portrait (7.9 inch)
- Looking Glass 16 inch
- Looking Glass 32 inch
- Looking Glass 65 inch

### Other Displays
- Hypervsn Solo (LED fan displays)
- Custom holographic displays (via web emulator)

## Installation

### Requirements
- Python 3.12+
- Network connection to HoloHub backend

### Setup

1. **Install dependencies:**
```bash
cd device-client
pip install -r requirements.txt
```

2. **Configure device credentials:**

Option A - Environment variables:
```bash
export HOLOHUB_API_URL="http://localhost:8000"
export DEVICE_HARDWARE_ID="your-hardware-id"
export DEVICE_SECRET="your-device-secret"
```

Option B - Configuration file:
```bash
cp config.example.txt config.txt
# Edit config.txt with your credentials
```

3. **Run the client:**
```bash
# Simulation mode (default)
python main.py

# Production mode (real hardware)
python main.py --production

# With custom config file
python main.py --config config.txt
```

## Configuration

### Config File Format

```ini
# HoloHub Device Client Configuration

# Server Connection
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# Device Credentials
DEVICE_HARDWARE_ID=HP-DEVICE-001
DEVICE_SECRET=your-secret-key-here

# Device Settings
DISPLAY_TYPE=looking_glass_portrait
HEARTBEAT_INTERVAL=30

# Content Cache
CONTENT_CACHE_DIR=./cache/content
MAX_CACHE_SIZE_GB=10

# Display Configuration
DISPLAY_WIDTH=2048
DISPLAY_HEIGHT=2048
QUILT_VIEWS=48
QUILT_DEPTH=45

# Simulation Mode
SIMULATION_MODE=true
```

## Display Types

| Display Type | Description | Resolution |
|--------------|-------------|------------|
| `looking_glass_portrait` | Looking Glass Portrait | 2048x2048 |
| `looking_glass_16` | Looking Glass 16" | 4096x4096 |
| `looking_glass_32` | Looking Glass 32" | 8192x8192 |
| `looking_glass_65` | Looking Glass 65" | 8192x8192 |
| `hypervsn_solo` | Hypervsn Solo | 1920x1080 |
| `web_emulator` | Web Emulator | Variable |

## Device Connection Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. REGISTER DEVICE (Web Dashboard)                     │
│     Admin registers device → gets device_secret          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  2. DEVICE STARTS                                       │
│     - Load config (credentials, display type)            │
│     - Connect to backend                                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  3. AUTHENTICATE                                         │
│     POST /api/v1/devices/auth                           │
│     { hardware_id, device_secret }                        │
│     ← Returns JWT token (30 day expiry)                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  4. SEND HEARTBEAT (every 30s)                         │
│     POST /api/v1/devices/{id}/heartbeat                 │
│     ← Status changes to "active"                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  5. GET PLAYLIST                                        │
│     GET /api/v1/devices/{id}/playlists                  │
│     ← Returns assigned playlist with assets              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  6. DOWNLOAD CONTENT                                     │
│     - Download 3D models (GLB/GLTF)                     │
│     - Cache locally for playback                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  7. DISPLAY CONTENT                                      │
│     - Loop through playlist items                        │
│     - Render holographic display                         │
│     - Handle brightness, volume, etc.                    │
└─────────────────────────────────────────────────────────┘
```

## Real Hardware Integration

To use with real Looking Glass hardware:

1. **Install Looking Glass SDK:**
```bash
pip install lookingglass
```

2. **Connect display** via USB or network

3. **Run in production mode:**
```bash
python main.py --production
```

The client will automatically detect the display type and use the appropriate rendering.

## Content Formats

### 3D Models
- **GLB** - Binary glTF (recommended)
- **GLTF** - glTF JSON format

### Quilt Files (Looking Glass)
- **PNG Quilt** - Pre-rendered holographic image sequence
- **MP4 Quilt** - Video quilt format

### Other
- Images (JPG, PNG)
- Videos (MP4)

## Troubleshooting

### Device not authenticating
- Verify hardware_id and device_secret are correct
- Check backend is running
- Ensure network connectivity

### Content not displaying
- Check cache directory has files
- Verify content format is supported
- Check display is initialized

### High CPU usage
- Reduce quilt_views in config
- Lower content resolution
- Check for background processes

## Development

### Project Structure
```
device-client/
├── main.py                 # Entry point
├── config/
│   └── config.py           # Configuration module
├── src/
│   ├── api_client.py       # Backend communication
│   ├── system_metrics.py   # System health monitoring
│   ├── content_manager.py  # Content caching
│   └── display_manager.py  # Display control
└── requirements.txt        # Dependencies
```

### Testing

Run in simulation mode to test without hardware:
```bash
python main.py --simulation
```

## License

MIT License - See LICENSE file for details
