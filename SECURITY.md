# Security Policy

## Supported Versions

At the moment, security fixes are only guaranteed for the latest state of the
`main` branch and the most recent tagged release.

## Reporting a Vulnerability

If you discover a security issue in `smartmonitor-hid`, please report it
privately first instead of opening a public issue with exploit details.

Recommended contact path:

- open a GitHub issue only for non-sensitive security discussions
- for sensitive reports, contact the repository owner directly and include:
  - affected version or commit
  - impact summary
  - reproduction steps
  - any suggested mitigation

Please avoid publishing working exploit details until the issue has been
reviewed and a fix or mitigation is available.

## Scope Notes

This library is primarily a local Linux HID/device communication package.
Potentially sensitive areas include:

- local device access through `/dev/hidraw*`
- theme parsing and compilation inputs
- any future host-project bridge integrations

Dependencies and operating system configuration may also affect the practical
security posture of applications that use this library.
