# Small-container protocol capacity — 6 October 2026

The target follows Lecture Pilot's university-VM deployment: Caddy, persistent
storage, health checks and bounded containers. This plugin keeps authentication
and the relay in one Node process with SQLite. Students perform university
login and portal requests on their own devices.

## Measured scope

- Node 24.21.0 in Linux aarch64 Docker on a local Apple Silicon host. Docker
  reported 14 CPUs and 23,842,430,976 available bytes; the measured container was
  capped at **one CPU and 512 MiB RAM**, with swap disabled.
- Read-only container filesystem, no extra capabilities, no new privileges,
  network disabled except its own loopback. No external or university calls.
- Real authenticated HTTP MCP handlers, SQLite token checks, opaque account
  profiles and account-specific task relay requests. Each response verifies the
  expected synthetic identity. Unauthenticated MCP access must return 401.
- Synthetic in-memory accounts and a simulated 10 ms device response. These
  fixtures exist only in the benchmark, not production routes or feature data.
- Each reader alternates profile and task calls, waits two seconds after each
  response, and starts staggered over two seconds. Arrival windows are 15 seconds;
  elapsed time includes final reader waits, roughly 17 seconds per run.
- The load generator and server share the same process and container budget.
  RSS includes both, and is sampled after responses. This is not a pure server
  memory measurement or the memory use of hundreds of idle HTTPS connections.

## Final run

| Active readers | Requests | Requests/s | p50 | p95 | p99 | HTTP/identity errors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30 | 223 | 13.17 | 8.26 ms | 20.56 ms | 24.78 ms | 0 |
| 60 | 448 | 26.39 | 8.26 ms | 19.34 ms | 22.04 ms | 0 |

| Sampled resource | 30 readers | 60 readers |
| --- | ---: | ---: |
| Maximum process RSS, including load generator | 117.51 MiB | 143.32 MiB |
| Maximum JavaScript heap | 38.63 MiB | 40.01 MiB |
| Average process CPU, 100% = one core | 13.67% | 21.95% |

An earlier run produced zero errors at both levels, with 60-reader p95 18.27 ms
and sampled RSS 136.28 MiB. These short runs establish protocol overhead for this
workload. They are not a maximum capacity estimate, an endurance test, a benchmark
of the university VM, or a measurement of Alma/ILIAS/Moodle latency. They omit TLS,
real sidecar networking, dashboard aggregation, mail and PDF workloads.

The production app container also passed health/public-page checks and returned
401 for unauthenticated MCP while running non-root with a read-only filesystem.
SQLite and its WAL/shared-memory files were verified as mode 0600. Caddy and
Compose configuration validation passed; no real certificate was issued.

## Reproduce locally

```sh
docker build -t tue-study-hub-release-check .
npx esbuild tests/benchmark-relay.ts --bundle --platform=node --format=esm \
  --packages=external --target=node24 --outfile=/tmp/tue-benchmark-relay.mjs
docker run --rm --network none --memory=512m --memory-swap=512m --cpus=1 \
  --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  -v /tmp/tue-benchmark-relay.mjs:/app/dist/benchmark-relay.mjs:ro \
  --entrypoint node tue-study-hub-release-check /app/dist/benchmark-relay.mjs
```

Final measured harness SHA-256:
`72bcebb1fde81cf49ac03c8cd4502e877243bef8243a80bd8443aa5a9a4fec90`.
The benchmark uses the image's production dependencies and widget assets but
bundles the current server source into a temporary, explicitly synthetic harness.
It never enters the public submission ZIP or production server image.

On the university VM, repeat with real HTTPS/device connections and permitted
accounts. Measure tail latency, idle connection memory, simultaneous private
requests and PDF transfers, restart recovery and portal failures. Keep a margin
below the first observed CPU, memory or upstream-service limit.

Reference method: Lecture Pilot's
[bounded read-capacity report](../../lecture-pilot/docs/research/2026-09-06-read-capacity-results.md).
Its workload and memory metric differ, so these numbers are not a speed comparison.
