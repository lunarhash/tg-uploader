# Dropbox to Telegram Video Bot

一个可以从 Dropbox 随机选择视频并上传到 Telegram 频道的机器人。支持多文件夹选择，可以单个或批量上传视频。

## 功能特点

- 🗂 支持选择多个 Dropbox 文件夹
- 📹 支持多种视频格式（.mp4, .mov, .avi）
- 🎲 随机选择视频上传
- ✅ 支持单选或多选视频
- 💾 自动保存文件夹选择设置

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/lunarhash/tg-uploader.git
cd tg-uploader
```

2. 创建并激活虚拟环境：
```bash
# 创建虚拟环境
python3 -m venv venv

# 在 macOS/Linux 上激活虚拟环境
source venv/bin/activate

# 在 Windows 上激活虚拟环境
# .\venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的配置信息
```

## 配置说明

你需要在 `.env` 文件中填入以下信息：

1. Telegram 配置：
   - `TELEGRAM_BOT_TOKEN`: 从 [@BotFather](https://t.me/botfather) 获取的机器人令牌
   - `TELEGRAM_CHANNEL_ID`: 目标频道 ID（通常以 -100 开头）

2. Dropbox 配置：
   - `DROPBOX_APP_KEY`: Dropbox 应用的 App Key
   - `DROPBOX_APP_SECRET`: Dropbox 应用的 App Secret
   - `DROPBOX_REFRESH_TOKEN`: Dropbox 的刷新令牌
   
获取 Dropbox 配置的步骤：
1. 访问 [Dropbox 开发者控制台](https://www.dropbox.com/developers/apps)
2. 点击 "Create app"
3. 选择 "Scoped access"
4. 选择 "Full Dropbox" 访问权限
5. 为你的应用命名
6. 在 "Permissions" 标签页中启用以下权限：
   - `files.metadata.read`
   - `files.content.read`
7. 生成访问令牌并填入配置文件

## 使用说明

1. 启动机器人：
```bash
python bot.py
```

2. 在 Telegram 中使用以下命令：
   - `/start` - 显示欢迎信息和使用说明
   - `/folders` - 选择要使用的视频文件夹
   - `/list` - 显示所选文件夹中的视频列表
   - `/random` - 随机选择一个视频上传

## 注意事项

1. 确保机器人已被添加到目标频道并具有管理员权限
2. Dropbox 中的视频文件大小需要符合 Telegram 的限制（最大 50MB）
3. 支持的视频格式：.mp4、.mov、.avi
4. 选择的文件夹设置会保存在 `.env` 文件中，重启后仍然有效

## 常见问题

1. 如何获取频道 ID？
   - 在频道中发送一条消息
   - 将该消息转发到 [@username_to_id_bot](https://t.me/username_to_id_bot)
   - 机器人会返回频道 ID

2. 上传失败？
   - 检查机器人是否有频道管理员权限
   - 确认视频文件大小是否超过限制
   - 查看视频格式是否支持

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
