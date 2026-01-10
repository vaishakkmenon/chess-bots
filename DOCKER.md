# Docker Development Environment

## Quick Start

### Start the container (once)
```bash
docker compose up -d
```

### Open a terminal in the container
```bash
docker compose exec dev bash
```

You can run this command in as many terminal windows as you want - they'll all connect to the same container.

### Stop the container
```bash
docker compose down
```

### Check if container is running
```bash
docker compose ps
```

## How it Works

- The container runs in the background with `sleep infinity`
- Your local directory is mounted at `/workspace` in the container
- **Changes are bidirectional**:
  - Files you edit locally (VS Code, etc.) immediately appear in the container
  - Files you modify in the container immediately appear locally
- The container persists until you run `docker compose down`

## Common Workflows

### Running Rust tests
```bash
# Open a terminal in the container
docker compose exec dev bash

# Navigate and run tests
cd rust-implementation/rust-engine
cargo test --release
```

### Running Python tests
```bash
docker compose exec dev bash
cd python-implementation
pytest --maxfail=1 --disable-warnings -q
```

### Multiple terminals
```bash
# Terminal 1: Run tests
docker compose exec dev bash

# Terminal 2: Edit files and run commands
docker compose exec dev bash

# Terminal 3: Watch logs or run perft
docker compose exec dev bash
```

## Rebuilding the Image

If you need to rebuild the `chess-dev` image:
```bash
# Rebuild your image first
docker build -t chess-dev .

# Then restart the container
docker compose down
docker compose up -d
```

## Troubleshooting

### Container not starting?
Check if the `chess-dev` image exists:
```bash
docker images | grep chess-dev
```

### Permission issues?
The container runs as root by default. If you need to match your user ID:
```bash
# Add to docker-compose.yml under 'dev:':
user: "${UID}:${GID}"
```

### Clean slate?
```bash
# Remove the container completely
docker compose down
# Remove any stopped containers
docker container prune
# Start fresh
docker compose up -d
```
