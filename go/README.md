# Go CLI

This subtree contains a Unix-native Go CLI for the stable authenticated Alma and ILIAS flows already implemented in the Python package.

Current commands:

```bash
tue alma current-lectures --date 14.03.2026 --json
tue alma exams --query limit=5
tue ilias search --term graphics --page 1 --json
tue ilias info --target 5289871 --json
tue api get /api/dashboard --query term="Sommer 2026"
tue alma study-planner
tue mail inbox --query unread_only=true
tue moodle dashboard
tue timms search --query query=machine+learning
tue discovery status --raw
```

The Go CLI uses native implementations where the board needs standalone behavior, with backend routes kept for endpoints that have not been ported yet:

- native Go flows for `alma current-lectures`, `alma exams`, `ilias search`, `ilias info`, Moodle read/enrolment commands, and `discovery status`
- backend-backed read commands for the remaining FastAPI surface, plus the generic `tue api get ...` escape hatch for any new read endpoint

The backend-backed commands use `PORTAL_API_BASE_URL` and default to `http://127.0.0.1:8000`.

The CLI automatically loads `.env.local` and `.env` from the current directory or any parent directory. Canonical credentials:

Preferred setup:

- `UNI_USERNAME`
- `UNI_PASSWORD`

Legacy `ALMA_*` and `ILIAS_*` env vars are still accepted as fallbacks for compatibility.

## Build

Standard build:

```bash
cd go
go build ./cmd/tue
```

Linux ARM64 cross-compile for boards:

```bash
cd go
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o tue-linux-arm64 ./cmd/tue
```

## macOS note

On this repo's current local setup (`go1.21.1` on macOS 26), plain `go build` can produce binaries that fail at launch with a missing `LC_UUID`. This is a local toolchain/runtime issue, not a contract issue in the CLI code.

The working local workaround is:

```bash
cd go
go build -ldflags='-linkmode=external' -o tue ./cmd/tue
codesign --force --sign - tue
./tue --help
```

## Verification

Contract tests are in:

- `go/internal/alma/*.go`
- `go/internal/ilias/*.go`

On the same macOS setup, `go test` test binaries need the same external-link-and-sign workaround to execute locally.
