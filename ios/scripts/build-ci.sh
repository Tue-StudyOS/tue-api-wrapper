#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

"$ROOT_DIR/ios/scripts/generate-project.sh"

xcodebuild \
  -resolvePackageDependencies \
  -project "$ROOT_DIR/ios/TueAPI.xcodeproj" \
  -scheme TueAPI \
  -clonedSourcePackagesDirPath "$ROOT_DIR/ios/build/SourcePackages"

xcodebuild \
  -project "$ROOT_DIR/ios/TueAPI.xcodeproj" \
  -scheme TueAPI \
  -destination "generic/platform=iOS Simulator" \
  -derivedDataPath "$ROOT_DIR/ios/build/DerivedData" \
  -clonedSourcePackagesDirPath "$ROOT_DIR/ios/build/SourcePackages" \
  -onlyUsePackageVersionsFromResolvedFile \
  -skipPackageUpdates \
  -jobs 1 \
  ARCHS=arm64 \
  ONLY_ACTIVE_ARCH=YES \
  COMPILER_INDEX_STORE_ENABLE=NO \
  CODE_SIGNING_ALLOWED=NO \
  build
