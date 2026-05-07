# tue-api-wrapper Java

Native Java/Android module for University of Tuebingen study systems.

This module talks directly to upstream systems from Java. It does not call `tue-api-server`, the Python package, Cloud Run, or any hosted wrapper. Authenticated calls keep cookies and SAML session state inside the Java process.

## Add to an Android Monorepo

Add this repository to the Android project, for example as a submodule:

```bash
git submodule add https://github.com/SebastianBoehler/tue-api-wrapper.git third_party/tue-api-wrapper
git submodule update --init --recursive
```

In the Android project's `settings.gradle`:

```gradle
include(":tue-api-wrapper-java")
project(":tue-api-wrapper-java").projectDir = file("third_party/tue-api-wrapper/java")
```

In the app module:

```gradle
dependencies {
    implementation(project(":tue-api-wrapper-java"))
}
```

Android apps need the `INTERNET` permission. Cleartext traffic is not needed for university systems because the native clients use HTTPS upstream URLs.

If the repo is checked out next to the Android app instead of inside `third_party/`, point `projectDir` at that local `java` folder.

## Publish Locally

```bash
cd java
gradle publishToMavenLocal
```

Then depend on:

```gradle
dependencies {
    implementation("io.github.sebastianboehler:tue-api-wrapper-java:0.2.1-SNAPSHOT")
}
```

## Usage

```java
import io.github.sebastianboehler.tueapi.TuebingenClient;

TuebingenClient client = TuebingenClient.builder()
    .credentials("your-zdv-id", "your-password")
    .build();

String lectures = client.alma().currentLectures("02.05.2026", 20);
String exams = client.alma().exams(50);
String iliasTasks = client.ilias().tasks(20);
String moodleDashboard = client.moodle().dashboard(6, 12, 9);
String inbox = client.mail().inbox(10, false, "");
```

Public calls do not require credentials:

```java
TuebingenClient publicClient = TuebingenClient.builder().build();

String canteens = publicClient.campus().canteens(null);
String timms = publicClient.timms().search("machine learning", 0, 20);
String talks = publicClient.products().talks("", 20);
```

## Coverage

Native direct clients are implemented for:

- Alma login, current lectures, exam overview, timetable/enrolment/study-service/catalog pages, public module search pages
- ILIAS SAML login, root links, memberships, tasks, content/forum/exercise pages, basic search/info fetches
- Moodle SAML login, dashboard AJAX payloads, calendar/course AJAX payloads, categories, courses, grades, messages, notifications pages
- University mail over IMAPS
- Campus canteens, buildings, events, KuF page, and seatfinder payloads
- TIMMS search/suggest/item/stream/tree pages
- Talks and basic directory search

Still intentionally not routed through a backend:

- Semantic course discovery and dashboard composition need a native Java index/aggregation layer before they can exist here.
- Praxisportal Algolia support is marked as not ported instead of falling back to Python.
