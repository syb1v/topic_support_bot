# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Added an automatic one-hour inactivity prompt with inline actions to close or continue a ticket.
- Added `/bye <ticket_id>` for managers/admins and topic-context execution without an ID.
- Added immutable GHCR build and SSH production deployment through GitHub Actions.
- Added `ADMIN_IDS` support in `.env` and `config.py` for dynamic management of administrators.
- Added admin ID `939731263` and `6499614618` to the default administrative list.
- New `deploy.sh` script specifically for `topic_support_bot`.
- New `update.sh` script for automated code refreshment.

### Fixed
- Registered Telegram slash-command hints, added `/menu`, and made `/bye` work in the configured support forum topic or staff private chat.
- Fixed `ImportError` by upgrading `yarl` and `aiosignal`.
- Resolved "silent bot" issue in terminal by changing log level from `ERROR` to `INFO` in `utils/logger.py`.
- Corrected `.env` parsing issue where inline comments were treated as part of the value.
- Fixed bot conflict errors by stopping all redundant instances.
- Fixed admin/manager button routing by simplifying `IsAdmin`, `IsManager`, and `IsUser` filters in `handlers/filters.py`.
- Hardened `start_bot()` so a transient `delete_webhook` failure no longer prevents polling from starting.

### Changed
- Removed the active-ticket reply keyboard; users now chat without a persistent close button.
- Upgraded core dependencies (`aiogram`, `aiohttp`, `pydantic`, etc.) to their latest versions.
- Refactored `handlers/group/topics.py` to fix the "General topic" bug:
    - Bot now correctly ignores messages in topics without an associated ticket (like General).
    - Admins and Managers no longer receive "invalid command" errors when writing in General.
- Removed proxy support (`PROXY_URL`, `aiohttp-socks`, `python-socks`); the bot connects to Telegram directly.

### Configured
- Configured `.env` with `BOT_TOKEN`, `SUPERGROUP_ID`, and `ADMIN_IDS`.
- Finalized `requirements.txt` with stable version pins.
