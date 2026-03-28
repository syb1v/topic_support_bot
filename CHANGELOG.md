# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Added admin ID `939731263` to `config.py`.
- New `deploy.sh` script specifically for `topic_support_bot`.
- New `update.sh` script for automated code refreshment.

### Changed
- Refactored `handlers/group/topics.py` to fix the "General topic" bug:
    - Bot now correctly ignores messages in topics without an associated ticket (like General).
    - Admins and Managers no longer receive "invalid command" errors when writing in General.

### Configured
- Configured `.env` with `BOT_TOKEN` and `SUPERGROUP_ID`.
