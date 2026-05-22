# iOS App

Native SwiftUI client for TUE API wrapper data.

This target does not call the Next.js or FastAPI surfaces for native credentialed data flows. It logs in to Alma and Moodle directly for grades, reads Uni Tuebingen mail directly over TLS IMAP, stores university credentials in Keychain from Settings, parses the Alma timetable iCalendar feed in Swift, browses public current lectures, caches upcoming lectures in an app group container, exposes that cache through WidgetKit plus Live Activities, and ships an on-device study assistant test screen. The app-feedback sheet creates GitHub issues directly from the client when `GITHUB_FEEDBACK_TOKEN` is configured as a build setting.

## Preview

Current device capture of the iOS Calendar surface:

<img src="../docs/assets/previews/ios-calendar-preview.png" alt="iOS calendar preview" width="360" />

## Requirements

- Xcode 16 or newer
- XcodeGen
- iOS 17 simulator or device

## Development

Generate the Xcode project:

```bash
npm run generate:ios
```

Build for the default simulator:

```bash
npm run build:ios
```

Open the generated project:

```bash
xcodegen generate --spec ios/project.yml
open ios/TueAPI.xcodeproj
```

## TestFlight

Fast path for a signed TestFlight upload:

```bash
npm run archive:ios
npm run upload:ios:testflight
```

The upload uses `ios/exportOptions/testflight.plist` with automatic App Store Connect signing for team `8P4NW2AQ75`.

Before the first upload, create the App Store Connect app record for `dev.sebastianboehler.tueapi`, register the widget bundle ID `dev.sebastianboehler.tueapi.widget`, and enable the App Group below for both targets.

Each TestFlight upload needs a new `CURRENT_PROJECT_VERSION` build number in `ios/project.yml`. Keep `MARKETING_VERSION` stable for small beta rebuilds unless the user-facing version should change.

External Beta App Review notes should mention:

- The app is a University of Tuebingen student client for timetable, tasks, grades, mail, campus food, talks, maps, and course discovery.
- Testers sign in with their own university account. Credentials are stored in the iOS Keychain and are not included in feedback.
- Public discovery, campus food, talks, and map surfaces can be tested without university credentials.
- The feedback sheet creates a public GitHub issue from user-entered text and app/device context.

Run a local unsigned release sanity check without Apple signing:

```bash
npm run release-check:ios
```

## App Groups

The app and widget extension share cached upcoming events through:

```text
group.dev.sebastianboehler.tueapi
```

For device builds, register that App Group in the Apple Developer portal or change the identifier in `Shared/Config/AppGroup.swift` plus both entitlement files.
