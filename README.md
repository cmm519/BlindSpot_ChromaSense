# ChromaSense

An AI powered color accessibility web portal that helps people with color vision deficiency and low vision understand color coded information in images.

## Start the portal

You need Docker with Docker Compose.

1. From the repository root, build the images:

   ```
   docker compose build
   ```

2. Start the portal:

   ```
   docker compose up portal
   ```

3. On the same computer, open `http://localhost:9090`.

The portal works with no AI provider. To use the AI features, copy `.env.example` to `.env`, and fill in the provider URL, API key, and model before you start the portal. Keep the API key in `.env`. Do not commit that file.

## Reach the portal from another device

Use a computer or phone on the same LAN as the host.

1. Find the host's IP address:
   - **macOS:** `ipconfig getifaddr en0`
   - **Linux:** `hostname -I`
   - **Windows:** `ipconfig`, then find the IPv4 address of the active adapter
2. Allow incoming TCP connections on port 9090 through the host's firewall:
   - **macOS:** System Settings, Network, Firewall, Options. Allow Docker to accept incoming connections.
   - **Linux with ufw:** `sudo ufw allow 9090/tcp`
   - **Windows:** Windows Defender Firewall, Advanced settings, Inbound Rules. Add a rule for TCP port 9090.
3. On the other device, open `http://<host-ip>:9090`.

The portal has no sign in and uses plain HTTP, so keep it on the LAN. Do not expose it to the internet.

## Run the checks

```
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
docker compose run --rm dev pytest src/color_engine/tests --cov=color_engine --cov-fail-under=70
docker compose run --rm dev pytest src/portal/tests
```
