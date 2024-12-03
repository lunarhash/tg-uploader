import os
import random
from datetime import datetime
import logging
import json
from dotenv import load_dotenv
import dropbox
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取环境变量
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')

# 从环境变量加载选中的文件夹
SELECTED_FOLDERS = set(filter(None, os.getenv('SELECTED_FOLDERS', '').split(',')))

# 创建全局 Application 实例
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

def save_selected_folders():
    """保存选中的文件夹到环境变量文件"""
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    with open('.env', 'w') as f:
        for line in lines:
            if line.startswith('SELECTED_FOLDERS='):
                f.write(f'SELECTED_FOLDERS={",".join(SELECTED_FOLDERS)}\n')
            else:
                f.write(line)

# 初始化 Dropbox
try:
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )
    # 测试连接
    dbx.users_get_current_account()
    logger.info("Successfully connected to Dropbox")
except Exception as e:
    logger.error(f"Failed to initialize Dropbox: {str(e)}")
    dbx = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """发送欢迎消息"""
    await update.message.reply_text(
        "欢迎使用视频上传机器人！\n"
        "使用 /folders 命令设置视频文件夹\n"
        "使用 /list 命令查看可用视频\n"
        "使用 /random 命令随机上传视频到频道"
    )

async def select_folders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """选择视频文件夹"""
    if not dbx:
        await update.message.reply_text("Dropbox 连接失败，请检查配置！")
        return

    try:
        # 获取根目录下的所有文件夹
        logger.info("Fetching folders from Dropbox...")
        result = dbx.files_list_folder('')
        folders = [entry for entry in result.entries if isinstance(entry, dropbox.files.FolderMetadata)]
        
        if not folders:
            await update.message.reply_text("没有找到文件夹！")
            return

        # 创建文件夹选择键盘
        keyboard = []
        for folder in folders:
            # 检查文件夹是否已被选中
            is_selected = folder.path_lower in SELECTED_FOLDERS
            keyboard.append([
                InlineKeyboardButton(
                    f"{'✅ ' if is_selected else ''}📁 {folder.name}",
                    callback_data=f"folder_{folder.path_lower}"
                )
            ])
        
        # 添加确认按钮
        keyboard.append([
            InlineKeyboardButton("✅ 确认选择", callback_data="folders_ok")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "请选择视频文件夹（可多选）：\n"
            "选中的文件夹会显示 ✅ 标记\n"
            "完成选择后点击「确认选择」",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error listing folders: {str(e)}")
        await update.message.reply_text(f"获取文件夹列表时出错：{str(e)}")

async def folder_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理文件夹选择的回调"""
    query = update.callback_query
    await query.answer()

    try:
        if query.data.startswith("folder_"):
            folder_path = query.data[7:]  # 移除 "folder_" 前缀
            
            # 切换文件夹选择状态
            if folder_path in SELECTED_FOLDERS:
                SELECTED_FOLDERS.remove(folder_path)
                status = "取消选择"
            else:
                SELECTED_FOLDERS.add(folder_path)
                status = "已选择"
            
            # 更新消息中的文件夹列表
            result = dbx.files_list_folder('')
            folders = [entry for entry in result.entries if isinstance(entry, dropbox.files.FolderMetadata)]
            
            keyboard = []
            for folder in folders:
                is_selected = folder.path_lower in SELECTED_FOLDERS
                keyboard.append([
                    InlineKeyboardButton(
                        f"{'✅ ' if is_selected else ''}📁 {folder.name}",
                        callback_data=f"folder_{folder.path_lower}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("✅ 确认选择", callback_data="folders_ok")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_reply_markup(reply_markup)
            await query.message.reply_text(f"{status}：{folder_path}")

        elif query.data == "folders_ok":
            # 保存选中的文件夹
            save_selected_folders()
            selected_count = len(SELECTED_FOLDERS)
            await query.message.edit_text(
                f"已选择 {selected_count} 个文件夹：\n" +
                "\n".join(f"📁 {path}" for path in sorted(SELECTED_FOLDERS)) +
                "\n\n现在可以使用 /list 或 /random 命令来使用这些文件夹中的视频了。"
            )

    except Exception as e:
        logger.error(f"Error in folder selection: {str(e)}")
        await query.message.reply_text(f"处理文件夹选择时出错：{str(e)}")

async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """列出选中文件夹中的视频文件"""
    if not dbx:
        await update.message.reply_text("Dropbox 连接失败，请检查配置！")
        return

    if not SELECTED_FOLDERS:
        await update.message.reply_text(
            "还没有选择任何文件夹！\n"
            "请先使用 /folders 命令选择视频文件夹。"
        )
        return

    try:
        # 获取所有选中文件夹中的视频文件
        logger.info("Fetching files from selected folders...")
        all_videos = []
        
        for folder_path in SELECTED_FOLDERS:
            try:
                # 确保路径格式正确
                folder_path = folder_path.strip('/')
                logger.info(f"Listing folder: {folder_path}")
                files = dbx.files_list_folder('/' + folder_path).entries
                videos = [file for file in files if isinstance(file, dropbox.files.FileMetadata) 
                         and file.path_lower.endswith(('.mp4', '.mov', '.avi'))]
                all_videos.extend(videos)
                logger.info(f"Found {len(videos)} videos in /{folder_path}")
            except Exception as e:
                logger.error(f"Error listing folder {folder_path}: {str(e)}")
        
        if not all_videos:
            await update.message.reply_text(
                "在选中的文件夹中没有找到视频文件！\n"
                "请确保文件夹中有 .mp4、.mov 或 .avi 格式的视频文件。"
            )
            return

        # 创建视频选择键盘
        keyboard = []
        for video in all_videos:
            if 'selected_videos' not in context.user_data:
                context.user_data['selected_videos'] = set()
            
            is_selected = video.path_lower in context.user_data['selected_videos']
            keyboard.append([
                InlineKeyboardButton(
                    f"{'✅ ' if is_selected else ''}🎬 {video.name}",
                    callback_data=f"select_{video.path_lower}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("上传选中的视频", callback_data="upload_selected")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "请选择要上传的视频（可多选）：",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error listing videos: {str(e)}")
        await update.message.reply_text(f"获取视频列表时出错：{str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理按钮回调"""
    if not dbx:
        await update.callback_query.message.reply_text("Dropbox 连接失败，请检查配置！")
        return

    query = update.callback_query
    await query.answer()

    try:
        if query.data.startswith("select_"):
            video_path = query.data[7:]  # 移除 "select_" 前缀
            
            if 'selected_videos' not in context.user_data:
                context.user_data['selected_videos'] = set()
                
            # 切换选择状态
            if video_path in context.user_data['selected_videos']:
                context.user_data['selected_videos'].remove(video_path)
                await query.message.reply_text(f"取消选择: {video_path}")
            else:
                context.user_data['selected_videos'].add(video_path)
                await query.message.reply_text(f"已选择: {video_path}")

        elif query.data == "upload_selected":
            if not context.user_data.get('selected_videos'):
                await query.message.reply_text("请先选择要上传的视频！")
                return

            try:
                # 随机选择一个视频上传
                selected_video = random.choice(list(context.user_data['selected_videos']))
                await upload_video(selected_video, query.message)
                # 清空选择
                context.user_data['selected_videos'].clear()
            except Exception as e:
                logger.error(f"Error uploading video: {str(e)}")
                await query.message.reply_text(f"上传视频时出错：{str(e)}")

    except Exception as e:
        logger.error(f"Error in button callback: {str(e)}")
        await query.message.reply_text(f"处理请求时出错：{str(e)}")

async def random_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """随机选择并上传视频"""
    if not dbx:
        await update.message.reply_text("Dropbox 连接失败，请检查配置！")
        return

    if not SELECTED_FOLDERS:
        await update.message.reply_text(
            "还没有选择任何文件夹！\n"
            "请先使用 /folders 命令选择视频文件夹。"
        )
        return

    try:
        # 获取所有选中文件夹中的视频文件
        logger.info("Fetching files for random selection...")
        all_videos = []
        
        for folder_path in SELECTED_FOLDERS:
            try:
                # 确保路径格式正确
                folder_path = folder_path.strip('/')
                logger.info(f"Listing folder: {folder_path}")
                files = dbx.files_list_folder('/' + folder_path).entries
                videos = [file for file in files if isinstance(file, dropbox.files.FileMetadata) 
                         and file.path_lower.endswith(('.mp4', '.mov', '.avi'))]
                all_videos.extend(videos)
                logger.info(f"Found {len(videos)} videos in /{folder_path}")
            except Exception as e:
                logger.error(f"Error listing folder {folder_path}: {str(e)}")
        
        if not all_videos:
            await update.message.reply_text(
                "在选中的文件夹中没有找到视频文件！\n"
                "请确保文件夹中有 .mp4、.mov 或 .avi 格式的视频文件。"
            )
            return

        # 随机选择一个视频
        selected_video = random.choice(all_videos)
        await upload_video(selected_video.path_lower, update.message)

    except Exception as e:
        logger.error(f"Error in random video: {str(e)}")
        await update.message.reply_text(f"随机上传视频时出错：{str(e)}")

async def upload_video(video_path: str, message):
    """上传视频到 Telegram 频道"""
    if not dbx:
        await message.reply_text("Dropbox 连接失败，请检查配置！")
        return

    try:
        logger.info(f"Getting temporary link for video: {video_path}")
        # 获取视频的临时链接
        temp_link = dbx.files_get_temporary_link(video_path)
        
        # 发送上传状态消息
        status_message = await message.reply_text("正在上传视频，请稍候...")
        
        logger.info(f"Uploading video to channel: {TELEGRAM_CHANNEL_ID}")
        # 上传视频到频道
        await application.bot.send_video(
            chat_id=TELEGRAM_CHANNEL_ID,
            video=temp_link.link,
            caption=f"上传时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await status_message.edit_text("视频上传成功！")

    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        await message.reply_text(f"上传视频时出错：{str(e)}")

def main():
    """主函数"""
    if not all([TELEGRAM_BOT_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN, TELEGRAM_CHANNEL_ID]):
        logger.error("Missing required environment variables!")
        return

    # 添加处理程序
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("folders", select_folders))
    application.add_handler(CommandHandler("list", list_videos))
    application.add_handler(CommandHandler("random", random_video))
    application.add_handler(CallbackQueryHandler(folder_button_callback, pattern="^folder_|^folders_"))
    application.add_handler(CallbackQueryHandler(button_callback))

    # 启动机器人
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
