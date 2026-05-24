# Desktop App

Electron desktop shell for the TUE Study Hub.

It wraps the existing Python backend as a managed local sidecar, stores credentials locally with Electron `safeStorage`, and renders a dedicated desktop UI for onboarding and dashboard access.

## Development

Install dependencies:

```bash
cd desktop
npm install
```

For local development, the desktop app expects the Python backend dependencies to be available. The simplest setup is:

```bash
cd ../package
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then start the desktop shell:

```bash
cd ../desktop
npm run dev
```

The Electron main process will prefer `package/.venv` automatically when it exists.

## Packaging

Build the renderer and Electron main process:

```bash
npm run build
```

Build the Python sidecar binary with PyInstaller:

```bash
python -m pip install -e ../package pyinstaller
npm run build:backend
```

Package the desktop installers:

```bash
npm run package
```

Or run the full pipeline in one step:

```bash
npm run dist
```

### Local signed macOS release

For a DMG that macOS can open without the malware-check warning, build on macOS with a `Developer ID Application` certificate and notarization credentials:

```bash
export APPLE_ID="apple-id@example.com"
export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="TEAMID1234"
npm run dist:mac:signed
```

The local helper also accepts App Store Connect API key notarization:

```bash
export APPLE_API_KEY="/path/to/AuthKey_ABC123DEFG.p8"
export APPLE_API_KEY_ID="ABC123DEFG"
export APPLE_API_ISSUER="00000000-0000-0000-0000-000000000000"
npm run dist:mac:signed
```

If the certificate is already in your login keychain, the helper uses the first `Developer ID Application` identity it finds. If you keep the certificate as an exported `.p12`, set `CSC_LINK` and `CSC_KEY_PASSWORD` instead. The command builds the release, then verifies `codesign`, `spctl`, and stapled notarization tickets for the generated `.app` and `.dmg`.

You can run the same command from the repository root:

```bash
npm run dist:desktop:mac:signed
```

## Releases

Two GitHub workflows are included:

- `desktop-build.yml` builds installer artifacts for macOS, Windows, and Linux on pushes to `main` and pull requests that touch `desktop/` or `package/`
- `desktop-release.yml` publishes a GitHub Release when you push a tag matching `desktop-v*`

`desktop-build.yml` disables signing on CI intentionally so pull request and branch builds stay deterministic.

`desktop-release.yml` requires signed and notarized macOS artifacts. The macOS job fails instead of publishing an unsigned or signed-only DMG when required secrets are missing.

### Auto updates

Packaged desktop builds check GitHub Releases for newer versions after launch and then every four hours. When a newer release is available, the app downloads it in the background and shows an in-app banner once the update is ready to install. The user still chooses when to restart into the new version.

The updater is wired to `SebastianBoehler/tue-api-wrapper` through `desktop/electron-builder.yml`. Keep uploading the full `desktop/release/*` output in `desktop-release.yml` so release metadata files such as `latest-mac.yml`, `latest.yml`, blockmaps, and installer artifacts stay available to `electron-updater`.

`desktop-release.yml` supports:

- macOS signing when `APPLE_SIGNING_CERTIFICATE_P12_BASE64` and `APPLE_SIGNING_CERTIFICATE_PASSWORD` are set
- macOS notarization when the signing certificate secrets are present and `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, and `APPLE_TEAM_ID` are also set
- macOS notarization with an App Store Connect API key when `APPLE_API_KEY_BASE64`, `APPLE_API_KEY_ID`, and `APPLE_API_ISSUER` are set
- Windows code signing when `WINDOWS_SIGNING_CERTIFICATE_PFX_BASE64` and `WINDOWS_SIGNING_CERTIFICATE_PASSWORD` are set

If Windows secrets are missing, the workflow still builds the Windows installer and emits an explicit warning. Linux AppImage artifacts are not code signed.

### Recommended GitHub secrets

macOS:

- `APPLE_SIGNING_CERTIFICATE_P12_BASE64`: base64-encoded `Developer ID Application` certificate export
- `APPLE_SIGNING_CERTIFICATE_PASSWORD`: password for the `.p12` export
- `APPLE_ID`: Apple account email used for notarization
- `APPLE_APP_SPECIFIC_PASSWORD`: app-specific password for notarization
- `APPLE_TEAM_ID`: Apple Developer team identifier

Alternative macOS notarization:

- `APPLE_API_KEY_BASE64`: base64-encoded App Store Connect API key `.p8`
- `APPLE_API_KEY_ID`: App Store Connect API key identifier
- `APPLE_API_ISSUER`: App Store Connect API issuer UUID

Windows:

- `WINDOWS_SIGNING_CERTIFICATE_PFX_BASE64`: base64-encoded Authenticode `.pfx` certificate export
- `WINDOWS_SIGNING_CERTIFICATE_PASSWORD`: password for the `.pfx` export

Notes:

- The current workflow covers standard macOS signing plus notarization and standard Windows `.pfx` signing.
- EV Windows certificates bound to hardware tokens are a different setup. For that case, switch to Azure Trusted Signing or a dedicated Windows signing runner.
