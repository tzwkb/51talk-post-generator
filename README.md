# 51Talk Post Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)

English | [中文](README_ZH.md)

A 51Talk BE/GE course poster generator that extracts level data from spreadsheets, drafts marketing copy, and renders deliverable PNG posters.

A 51Talk BE/GE course poster generator that extracts level data from spreadsheets, creates marketing copy through an LLM API, and renders delivery-ready PNG posters.

## What It Does

- Extracts BE/GE level statistics and vocabulary signals from source spreadsheets.
- Generates poster copy with the configured LLM endpoint.
- Renders posters from HTML templates through Playwright.

## Configuration

Set the LLM credentials before running a generator. `LLM_BASE_URL` is optional and defaults to the current VectorEngine-compatible endpoint.

```powershell
$env:LLM_API_KEY="..."
$env:LLM_BASE_URL="https://api.vectorengine.ai/v1"
```

Update `WORK_DIR` in the scripts to match the local project directory before running them.

## Scripts

- `generate_posters.py`: generate GE posters.
- `generate_be.py`: generate BE posters.
- `extract_be.py`: extract BE level statistics.

## License

[MIT](LICENSE)
