# Authentication and deployment boundaries

Status: local hardening and operating guidance, 15 October 2026. This document
does not establish university approval, legal compliance, or production safety.
Lecture Pilot's deployed configuration has not been assessed in this change.

## What remains supported

- Public-data clients without university credentials.
- Direct login, HTML scraping, and existing authenticated workflows in a local
  SDK, CLI, native app, or local sidecar using the account owner's credentials.
- Existing upstream Shibboleth/SAML handoffs used by those local clients.

Local execution reduces central collection of passwords. It does not establish
permission from upstream operators. Respect access rules and upstream limits.

## What the password model means

`UniversityCredentials` holds a password as a Python string in process memory.
Direct login submits that password to the upstream service. The SDK omits it
from generated `repr` and `str` output, including nested facade representations.
This does not encrypt memory, redact arbitrary logs or tracebacks, prevent
explicit field access or serialization, or securely erase Python strings.

Loading a password from `.env` means the file contains the password in plaintext.
The credential model itself does not write a password file. Keep secret files
outside version control and restrict access. Do not enable request-body logging
or capture credential-bearing traffic in diagnostic exports.

HTTPS protects transport. A hosted application that receives a password can
still read it. Encrypting a server-side password vault does not remove this
trust relationship. An institutional domain does not prove operator approval.

## Local API restrictions and remaining risks

The standard `tue-api-server` command and Python module entry point reject a
non-loopback bind when any university username or password is configured through
`UNI_*`, `ALMA_*`, or `ILIAS_*` login variables. Local authenticated use remains
available on loopback. Without university credentials, the bind check permits
network deployment; do not configure other private credentials in a public API.

This startup check is not an access-control boundary:

- Direct ASGI launches, such as `uvicorn tue_api_wrapper.api_server:app`, bypass it.
- A reverse proxy, tunnel, or server-rendered Next.js frontend can expose a
  loopback API. Do not publish those surfaces with account credentials loaded.
- HTTP routes use the process account without per-caller authentication.
- CORS currently allows arbitrary origins. Loopback binding alone therefore
  does not protect against browser-origin access. CORS is not authentication.
- Local processes can access the API. Browser access controls and per-instance
  authorization need a separate change across the desktop and sidecar clients.

The Docker image sets `HOST=0.0.0.0`. It will now fail startup with university
credentials. Use native local execution for authenticated access. Do not bypass
the check to publish the environment-backed account.

## Hosted university applications

Do not collect ZDV passwords in a hosted login form. For a hosted application,
agree a service-provider integration with the ZDV, then send users to the ZDV
identity provider in their browser. Validate the resulting authentication
assertion using a maintained SAML implementation and agreed metadata.

The ZDV documents its Shibboleth identity provider on its
[Single Sign On page](https://uni-tuebingen.de/einrichtungen/zentrum-fuer-datenverarbeitung/dienstleistungen/digitale-identitaet/single-sign-on/).
The [OASIS SAML overview](https://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-tech-overview-2.0-cd-02.html)
describes browser SSO between an identity provider and a service provider.

Logging into our application does not provide an Alma or ILIAS session or
permission to retrieve private records there. Agree a separate supported data
access method, keep those operations local, or limit hosted functionality to
public data and explicitly supplied material. Replaying an IdP password from
the server is not a password-free service-provider integration.

## Response to the reported concern

For a service reported to collect university passwords, keep that hosted login
disabled while its operator and the ZDV review the actual flow. Establish which
processes received passwords, how long they retained them, and whether logs,
telemetry, files, backups, or third parties received secrets. Preserve evidence
without making additional secret-bearing exports.

Agree user communication, session revocation, and password-change instructions
with the ZDV based on that investigation. The quoted dataclass alone does not
prove credential theft, persistence, or a particular legal finding.

Moving the repository to a personal account and marking it independent can
clarify ownership. Neither measure changes the deployed credential flow or
replaces review of the hosted application.
