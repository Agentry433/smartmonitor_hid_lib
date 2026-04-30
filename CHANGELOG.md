# Changelog

All notable changes to `smartmonitor-hid` will be documented in this file.

The format is based on Keep a Changelog, and the project follows a simple
`major.minor.patch` versioning scheme.

## [0.1.0] - 2026-05-01

### Added

- Initial standalone `smartmonitor-hid` package structure
- HID transport with auto-detection, reset, YMODEM upload, runtime packets, and datetime packets
- Standalone `.ui` parser and writer
- Standalone `.img.dat` parser and record packing helpers
- Standalone `.ui -> img.dat` compiler
- CLI entry point `smartmonitor-hid`
- English and Russian README files
- English and Russian integration manuals
- Unit tests for runtime mapping, client behavior, CLI, bridge handling, `.ui`, `.img.dat`, and standalone compile flow
