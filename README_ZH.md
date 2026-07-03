# 51Talk Post Generator

中文 | [English](README.md)


## 概览

51Talk BE/GE 课程海报生成工具，用于从课程表格提取等级信息、生成营销文案并渲染 PNG 海报。

## 主要能力

- 从源表格提取 BE/GE 等级统计和词汇信号。
- 通过配置的 LLM 接口生成海报文案。
- 使用 HTML 模板和 Playwright 渲染交付图片。

## 使用方式

运行前设置 LLM_API_KEY，并按脚本中的 WORK_DIR 指向本地项目目录。

## 状态

该仓库仍按当前 README 的说明维护或使用。

## 注意事项

不要把 API key 写回仓库；密钥应通过环境变量提供。

## 命令与配置参考

以下代码块从主 README 保留；命令、路径和配置键不翻译，复制时请以实际环境为准。

```powershell
$env:LLM_API_KEY="..."
$env:LLM_BASE_URL="https://api.vectorengine.ai/v1"
```

## 详细技术说明

主 README 保留了原始技术细节、历史说明、完整命令和文件结构。本文件作为中文版本维护核心说明；需要逐项核对命令时，请参照主 README 的代码块和路径。
