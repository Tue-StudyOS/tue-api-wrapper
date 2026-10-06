# Single-VM deployment

One Node 24 process handles OAuth, MCP, account links, confirmations and the
outbound sidecar relay. SQLite uses a persistent Docker volume. Caddy handles
HTTPS. No external database, identity provider, Redis or inbound student tunnel
is required. Only ports 80 and 443 are exposed by Compose.

The deployment keeps university passwords and cookies on each student's device.
Requested private responses pass through this service to ChatGPT. Running the
local Python API on this VM with shared university credentials is unsupported.

## Deploy after obtaining a VM and domain

1. Install Docker with Compose on the VM. Point the hostname at the VM.
2. Allow inbound TCP 80 and 443. Use a persistent local disk for Docker volumes.
3. Copy `.env.example` to `.env` and set the real HTTPS `APP_BASE_URL` origin.
4. Run `docker compose up --build -d` from `chatgpt/`.
5. Check `/healthz`, the home/support/privacy/terms pages and OAuth metadata.
6. Verify an unauthenticated `/mcp` request returns HTTP 401 with
   `WWW-Authenticate` and the protected-resource metadata URL.
7. Run the local sidecar, link through ChatGPT, and complete the submission cases
   using a real permitted student account. Check account isolation with two users.

Caddy shares the app container's network and forwards through loopback. Express
trusts loopback proxies only. Do not expose port 8080 or add arbitrary trusted
proxies. Keep one app replica: relay jobs live in process memory, and SQLite
does not provide cross-host relay routing. Avoid Cloud Run's ephemeral disk and
multiple replicas. Existing Cloud Build can build the container; it does not
establish durable hosting.

## Local student runtime

Install the Python package on the student's own machine and configure its local
university credentials. Start its API on numeric loopback, normally port 8000:

```sh
cd package
PYTHONPATH=src python -m tue_api_wrapper.api_server
```

With Node 24 and the built ChatGPT package on that same device:

```sh
cd chatgpt
npm run link-sidecar -- --server https://YOUR_PRODUCTION_HOST
```

If the API uses another port, add `--backend http://127.0.0.1:PORT`. Only numeric
loopback is accepted; university cookies are never forwarded by this client.
Keep the sidecar running. Enter its printed link password on the service's
account connection page, never in chat. Link credentials are stored locally
under `~/.tuebingen-study-hub/` with mode 0600. Use a permitted demo account for
review; keep that account's sidecar running so reviewers need no local setup.

Disconnect and invalidate the device and OAuth connection:

```sh
npm run link-sidecar -- --server https://YOUR_PRODUCTION_HOST --disconnect
```

## Resource and retention limits

Compose caps the app at 512 MiB and one CPU; these are limits, not measured
capacity guarantees. TLS has a separate 128 MiB cap. Polls wait 20 seconds;
university requests stop after 25 seconds, relay requests after 30 seconds.
JSON responses are limited to 1 MiB and PDFs to 8 MiB. At most four PDF transfers
and 100 relay jobs run concurrently, with twelve jobs per account.
The server never retries a university write. Results lost after submission
must be checked in the university portal.

Do not enable access logging, request-body logging or logging of authorization
headers or download paths. Back up the SQLite volume only with a documented
retention and deletion policy. Backups contain account links and grants, but
not university passwords. Restoring backups can restore revoked grants; rotate
or clear grants after recovery. To reset all connections, stop the app and remove
its database, then require every user to link again.

Before production, load-test the real VM with expected concurrency and check
actual portal latency, memory, disconnects and restart behavior. Local regression
tests establish protocol behavior, not university portal availability or capacity.
