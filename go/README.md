# Go CLI

This subtree contains a Unix-native Go CLI that runs without relying on the local Python FastAPI backend.

Current commands:

```bash
tue alma current-lectures --date 14.03.2026 --json
tue alma exams --query limit=5
tue alma timetable --query term="Sommer 2026"
tue alma timetable --query term="Sommer 2026" --ics
tue ilias search --term graphics --page 1 --json
tue ilias info --target 5289871 --json
tue moodle dashboard
tue talks list --query scope=upcoming --query query=ai
tue talks get 123
tue praxisportal filters
tue praxisportal search --query query=data --query project_type_id=1 --query industry_id=2
tue praxisportal project 456
tue seatfinder availability
tue discovery status --raw
```

The Go CLI uses native implementations for Alma/ILIAS/Moodle flows and aims to keep logic on the client side (no Python backend as a middle layer).

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
