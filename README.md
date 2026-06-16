# Blog Content Agent Demo

一个面向技术博客写作场景的内容助手 Agent 原型项目。

输入文章草稿后，Agent 可以基于规则生成：

- 标题建议
- 文章摘要
- 推荐标签
- 发布检查清单

在线 Demo：

https://ai.xiaowenli.com/blog-agent/

> Demo 已开启访问保护，面试或展示时可提供临时账号。

## 项目背景

本项目用于探索 AI Agent 在内容工作流中的落地方式。  
相比直接写文章，Blog Content Agent 更关注写作前后的辅助流程，例如标题生成、摘要提炼、标签推荐和发布前检查。

## 当前功能

- 输入文章草稿
- 自动统计文章长度
- 根据关键词生成标题建议
- 提取文章摘要
- 推荐文章标签
- 生成发布检查清单
- 使用 Nginx 反向代理到独立路径
- 使用 Basic Auth 保护 Demo 访问
- 使用 systemd 托管服务，支持开机自启

## 技术栈

- Python
- HTML / CSS
- Linux
- Nginx
- systemd
- Content Workflow

## 后续计划

- 接入 LLM，生成更自然的标题和摘要
- 支持多种文章风格，例如项目复盘、技术笔记、部署教程
- 增加敏感信息检查，例如密码、密钥、服务器 IP
- 与 Halo 博客发布流程结合，形成博客写作 Agent
