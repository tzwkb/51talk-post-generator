# 51Talk Post Generator

<!-- bilingual-readme:start -->

## 双语说明 / Bilingual Documentation

> 本节提供整篇 README 的中英双语维护说明；下方保留原始详细说明、命令、路径和配置示例。
> This section provides bilingual maintenance notes for the full README; the original detailed notes, commands, paths, and configuration examples are preserved below.

### 中文

**概览**：51Talk BE/GE 课程海报生成工具，用于从课程表格提取等级信息、生成营销文案并渲染 PNG 海报。

**主要能力**：
- 从源表格提取 BE/GE 等级统计和词汇信号。
- 通过配置的 LLM 接口生成海报文案。
- 使用 HTML 模板和 Playwright 渲染交付图片。

**使用方式**：运行前设置 LLM_API_KEY，并按脚本中的 WORK_DIR 指向本地项目目录。

**状态**：该仓库仍按当前 README 的说明维护或使用。

**注意事项**：不要把 API key 写回仓库；密钥应通过环境变量提供。

### English

**Overview**: 51Talk BE/GE course poster generator for extracting level data, creating marketing copy, and rendering PNG posters.

**Key capabilities**:
- Extracts BE/GE level statistics and vocabulary signals from source spreadsheets.
- Generates poster copy through the configured LLM endpoint.
- Renders delivery assets from HTML templates through Playwright.

**Usage**: Set LLM_API_KEY before running and update WORK_DIR in the scripts for the local project directory.

**Status**: This repository is maintained or used according to the current README notes.

**Notes**: Do not commit API keys; credentials should be supplied through environment variables.

<!-- bilingual-readme:end -->

51Talk BE/GE 课程海报生成工具，用于从课程表格提取等级信息、生成营销文案，并渲染可交付 PNG 海报。

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