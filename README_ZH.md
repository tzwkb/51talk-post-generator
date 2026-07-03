# 51Talk Post Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)

[English](README.md) | 中文

## 概览

51Talk BE/GE 课程海报生成工具，用于从课程表格提取等级信息、生成营销文案并渲染 PNG 海报。

## 主要能力

- 从源表格提取 BE/GE 等级统计和词汇信号。
- 通过配置的 LLM 接口生成海报文案。
- 使用 HTML 模板和 Playwright 渲染交付图片。

## 使用方式

运行前设置 LLM_API_KEY，并按脚本中的 WORK_DIR 指向本地项目目录。

## 注意事项

不要把 API key 写回仓库；密钥应通过环境变量提供。

## 命令与配置参考

以下命令、路径和配置键保持原样，复制时请以实际环境为准。

```powershell
$env:LLM_API_KEY="..."
$env:LLM_BASE_URL="https://api.vectorengine.ai/v1"
```
