# Security Policy

## Scope

Pulse Runner is a local Pygame desktop prototype. The supported security
surface is the Python package, bundled code, and documented asset-loading paths
on `main` and the latest tagged release. It does not expose a network service.

## Reporting a vulnerability

Please report security issues privately through GitHub's **Report a
vulnerability** flow on this repository. Do not post exploit code, local file
paths, or other sensitive information in a public issue. If private reporting
is unavailable, share only a non-sensitive summary publicly and request a
private channel.

Include the affected commit or release, operating system, Python/Pygame
versions, reproduction steps, and the expected versus observed behavior.

## Response

Reports are investigated against the current `main` branch and coordinated
with the reporter before public disclosure. Third-party artwork and local
assets should be treated as untrusted input and should not be used to share
private data.
