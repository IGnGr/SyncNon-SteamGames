# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.4]

### Added
- Automatic GitHub Actions build and release.

### Changed
- Updated logic so shortcuts use normalized paths for comparisons, to make the logic more robust.
- Updated logic so shortcuts generated manually or by other means are no longer deleted.
- Added full stack traces to error logs for better debugging.

## [v1.3]

### Added
- Multi folder support.

## [v1.2]

### Added
- Added "Redist" exception to executable names.

### Changed
- Modified UserData finder.

## [v1.1]

### Added
- "Home" images support.
- GitIgnore file.

## [v1.0]

### Added
- Initial release with core functionality for syncing non-Steam games to Steam.
- GUI support via Gooey.
- Logging, API integration with SteamGridDB.

### Changed
- Improved executable detection logic.

### Fixed
- Issues with Steam user data path inference.
