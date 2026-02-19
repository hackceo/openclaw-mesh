# OpenClaw Mesh Network

Decentralized OpenClaw Agent Network Deployment

## Quick Start

### Server A (Seed Node)
```bash
curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/install.sh | sudo bash -s agent-a
```

### Server B/C/D/E (Connect to Seed)
```bash
curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/install.sh | sudo bash -s agent-b 100.64.1.1
```

## Files

- `decentralized_discovery.py` - Gossip protocol core
- `install.sh` - One-click install script
- `start.sh` - Start script

## Author

For Lei Ge
