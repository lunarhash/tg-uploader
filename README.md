# Dropbox to Telegram Video Bot

这是一个可以从 Dropbox 随机选择视频并上传到 Telegram 频道的机器人。

## 功能特点

- 列出 Dropbox 中的所有视频文件
- 支持单个或多个视频选择
- 随机上传选中的视频到 Telegram 频道
- 支持多种视频格式（.mp4, .mov, .avi）

## 安装步骤

1. 安装依赖包：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
   - 复制 `.env.example` 文件并重命名为 `.env`
   - 在 `.env` 文件中填入以下信息：
     - TELEGRAM_BOT_TOKEN：你的 Telegram 机器人 token
     - DROPBOX_ACCESS_TOKEN：你的 Dropbox access token
     - TELEGRAM_CHANNEL_ID：目标 Telegram 频道 ID

## 使用方法

1. 启动机器人：
```bash
python bot.py
```

2. 在 Telegram 中使用以下命令：
   - `/start` - 显示欢迎信息和使用说明
   - `/list` - 显示可用视频列表，可以选择多个视频
   - `/random` - 随机选择并上传一个视频

## 注意事项

- 确保机器人具有向目标频道发送消息的权限
- Dropbox token 需要有读取文件的权限
- 视频文件大小需要符合 Telegram 的限制（最大 50MB）
