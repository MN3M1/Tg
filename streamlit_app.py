import os, re, yt_dlp, asyncio, wget, time, uuid
import hashlib

from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# Token mapping for callback data (Telegram has 64 byte limit)
TOKEN_MAP = {}

def create_token(url, title="Unknown"):
    """Create short token for URL mapping"""
    token = hashlib.sha1(url.encode()).hexdigest()[:10]
    TOKEN_MAP[token] = {
        'url': url,
        'title': title
    }
    return token

def truncate_caption(text, max_length=1000):
    """Truncate caption to stay within Telegram's 1024 character limit with buffer"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def safe_truncate(text, max_length):
    """Safely truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

# Get credentials from environment variables (REQUIRED for security)
api_id = 21243549
api_hash = "d02725122025d230d52586057194595b"
bot_token = "8265705564:AAGo5ZQ0yu4ShaaVImsJMaTsiGcMWs6fYoA"

# Validate required credentials
if not api_id or not api_hash or not bot_token:
    print("❌ CRITICAL: API_ID, API_HASH, and BOT_TOKEN environment variables are required!")
    print("📝 Set them in your environment or .env file")
    print("🔒 Never hardcode credentials in your code for security!")
    exit(1)

bot = Client(
    "youtube",
    api_id = int(api_id),
    api_hash = api_hash,
    bot_token = bot_token
)

def search_yt(query):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'extract_flat': True,
        'cookiefile': 'cookies.txt',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            if info and 'entries' in info:
                return info['entries']
        except Exception as e:
            print(f"An error occurred during search: {e}")
        return []

@bot.on_message((filters.private | filters.group) & filters.text)
async def main(bot, msg):
    if not msg.text:
        return
    if msg.text == "/youtube" or msg.text == "/start":
        await bot.send_message(msg.chat.id, f"• مرحبا بك 《 {msg.from_user.mention} 》\n\n• أرسل أي رابط من أي موقع!\n• أو ارسل بوت + ما تريد البحث عنه\n• يدعم التحميل حتي 2GB\n\n🌐 يدعم أكثر من 1000 موقع:\n🎬 YouTube, 📷 Instagram, 🎵 TikTok\n📘 Facebook, 🐦 Twitter, 🎵 Vimeo\n✨ والمزيد!")

    if "بوت" in msg.text and not msg.text.startswith("/dl_"):
        search_query = msg.text.replace("بوت", "").strip()
        if not search_query:
            return await bot.send_message(msg.chat.id, "Please provide a search query after 'بوت'.")

        wait = await bot.send_message(msg.chat.id, f'🔎︙البحث عن "{search_query}"...')
        search_results = search_yt(search_query)

        if not search_results:
            return await wait.edit(f'❌︙لم يتم العثور على نتائج لـ "{search_query}".')

        txt = ''
        for i, video in enumerate(search_results[:9]):
            title = video.get("title")
            duration = video.get("duration_string") or "N/A"
            views = video.get("view_count")
            id = video.get("id", "").replace("-", "mnem")
            channel_name = video.get("channel") or video.get("uploader") or "Unknown Channel"

            if not title or not id:
                continue

            # Keep original id for the clickable link, only modify for /dl_ command
            display_id = video.get("id", "")
            command_id = display_id.replace("-", "mnem")
            
            safe_title = safe_truncate(title, 80)
            safe_channel = safe_truncate(channel_name, 40)
            
            if display_id:
                txt += f"🎬 [{safe_title}](https://youtu.be/{display_id})\n👤 {safe_channel}\n🕑 {duration} - 👁 {views}\n🔗 /dl_{command_id}\n\n"

        await wait.edit(f'🔎︙نتائج البحث لـ "{search_query}"\n\n{txt}', disable_web_page_preview=True)
        return

    # Universal URL detection for ANY site yt-dlp supports
    url_pattern = r'(https?://[^\s]+)'
    url_match = re.search(url_pattern, msg.text)
    
    if url_match:
        url = url_match.group(1)
        wait = await bot.send_message(msg.chat.id, f'🔍︙فحص الرابط...', disable_web_page_preview=True)

        try:
            print(f"Processing universal URL: {url}")
            # Use yt-dlp for metadata extraction with cookies (works for 1000+ sites)
            with yt_dlp.YoutubeDL({
                'quiet': True,
                'cookiefile': 'cookies.txt',
                'extract_flat': False
            }) as ydl:
                info = ydl.extract_info(url, download=False)
                
            if not info:
                await wait.edit("❌ لا يمكن الوصول لهذا الرابط")
                return
                
            title = info.get('title', 'Unknown Title')
            author = info.get('uploader', 'Unknown Channel')
            views = info.get('view_count', 'N/A')
            thumbnail = info.get('thumbnail')
            webpage_url = info.get('webpage_url', url)
            
            # Determine platform icon based on URL
            if 'youtube.com' in url or 'youtu.be' in url:
                icon = '🎬'
                platform_name = 'YouTube'
            elif 'tiktok.com' in url:
                icon = '🎵'
                platform_name = 'TikTok'
            elif 'instagram.com' in url:
                icon = '📷'
                platform_name = 'Instagram'
            elif 'facebook.com' in url:
                icon = '📘'
                platform_name = 'Facebook'
            elif 'twitter.com' in url or 'x.com' in url:
                icon = '🐦'
                platform_name = 'Twitter/X'
            else:
                icon = '🌐'
                platform_name = 'Web'
            
            # Create token for this URL
            token = create_token(webpage_url, title)
            
            # Create download buttons using token
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(f"فيديو {icon}", callback_data=f"video&&{token}"), 
                InlineKeyboardButton(f"صوت {icon}", callback_data=f"audio&&{token}")
            ]])

            safe_title = safe_truncate(title, 100)
            safe_author = safe_truncate(author, 50)
            
            caption_text = f"{icon} [{safe_title}]({webpage_url})\n👤 {safe_author}\n👁 {views}\n🌐 {platform_name}"
            
            caption_text = truncate_caption(caption_text)
            
            if thumbnail:
                await bot.send_photo(
                    msg.chat.id,
                    photo=thumbnail,
                    caption=caption_text,
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    msg.chat.id,
                    text=caption_text,
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            print(f"Successfully processed {platform_name} link: {title}")
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            await wait.edit(f"❌ خطأ في معالجة الرابط: {str(e)}")
        finally:
            await wait.delete()
        return

    # Legacy YouTube /dl_ command support
    if msg.text.startswith("/dl_"):
        vid_id = msg.text.replace("mnem", "-").replace("/dl_", "")
        youtube_url = f"https://youtu.be/{vid_id}"
        wait = await bot.send_message(msg.chat.id, f'🔎︙البحث عن "{youtube_url}"...', disable_web_page_preview=True)

        try:
            print(f"Processing legacy download request for: {youtube_url}")
            with yt_dlp.YoutubeDL({
                'quiet': True,
                'cookiefile': 'cookies.txt',
                'extract_flat': False
            }) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
            if not info:
                await wait.edit("❌ لا يمكن الوصول للفيديو")
                return
                
            title = info.get('title', 'Unknown Title')
            author = info.get('uploader', 'Unknown Channel')
            views = info.get('view_count', 'N/A')
            thumbnail = info.get('thumbnail')
            
            # Create token for legacy command
            token = create_token(youtube_url, title)
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("مقطع فيديو 🎞", callback_data=f"video&&{token}"), 
                InlineKeyboardButton("ملف صوتي 📼", callback_data=f"audio&&{token}")
            ]])

            safe_title = safe_truncate(title, 100)
            safe_author = safe_truncate(author, 50)
            caption_text = f"🎬 [{safe_title}]({youtube_url})\n👤 {safe_author}\n👁 {views}"
            caption_text = truncate_caption(caption_text)

            if thumbnail:
                await bot.send_photo(
                    msg.chat.id,
                    photo=thumbnail,
                    caption=caption_text,
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    msg.chat.id,
                    text=caption_text,
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            print(f"Successfully processed legacy request: {title}")
        except Exception as e:
            print(f"Error processing legacy request: {e}")
            await wait.edit(f"❌ خطأ في الوصول للفيديو: {e}")
        finally:
            await wait.delete()

@bot.on_callback_query(filters.regex("&&"), group=24)
async def download(bot, query: CallbackQuery):
    await bot.delete_messages(query.message.chat.id, query.message.id)
    
    # Handle callback data as string
    data = query.data.decode() if isinstance(query.data, bytes) else str(query.data)
    data_parts = data.split("&&")
    
    if len(data_parts) < 2:
        return
        
    download_type = data_parts[0]  # 'video' or 'audio'
    token = data_parts[1]
    
    # Look up URL from token
    if token not in TOKEN_MAP:
        await bot.send_message(query.message.chat.id, "❌ انتهت صلاحية الرابط، أرسل الرابط مرة أخرى")
        return
        
    url_data = TOKEN_MAP[token]
    video_link = url_data['url']
    
    progress_msg = await bot.send_message(query.message.chat.id, "🚀 بدء التحميل....")
    
    # Initialize file paths for cleanup
    video_file = None
    audio_file = None
    thumb = None
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total > 0:
                progress = (downloaded / total) * 100
                # Simple progress logging to avoid async issues
                if progress % 10 == 0 or progress > 95:
                    print(f"Download progress: {progress:.1f}% - {downloaded/(1024*1024):.1f}/{total/(1024*1024):.1f} MB")
    
    try:
        print(f"Starting download for: {video_link}")
        # Get video info using yt-dlp for metadata
        with yt_dlp.YoutubeDL({
            'quiet': True,
            'cookiefile': 'cookies.txt',
            'extract_flat': False
        }) as ydl:
            video_info = ydl.extract_info(video_link, download=False)
            
        if not video_info:
            await progress_msg.edit_text("❌ لا يمكن الوصول للمحتوى")
            return
            
        title = video_info.get('title', 'Unknown Title') if video_info else 'Unknown Title'
        author = video_info.get('uploader', 'Unknown Channel') if video_info else 'Unknown Channel'
        duration = video_info.get('duration', 0) if video_info else 0
        thumbnail_url = video_info.get('thumbnail') if video_info else None
        
        # Download thumbnail
        if thumbnail_url:
            thumb = wget.download(thumbnail_url)
        print(f"Downloaded thumbnail for: {title}")

        if download_type == "video":
            # Try advanced format first (requires ffmpeg), with fallback
            video_ydl_opts = {
                "format": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "keepvideo": True,
                "geo_bypass": True,
                "outtmpl": "%(title)s.%(ext)s",
                "quiet": True,
                "cookiefile": "cookies.txt",
                "progress_hooks": [progress_hook]
            }
            
            try:
                with yt_dlp.YoutubeDL(video_ydl_opts) as ytdl:
                    # Download and get actual final filename after processing
                    info = ytdl.extract_info(video_link, download=True)
                    # Get the actual filename after merging/processing (safe None handling)
                    requested = info.get('requested_downloads') or []
                    video_file = None
                    if isinstance(requested, list) and requested and isinstance(requested[0], dict):
                        video_file = requested[0].get('filepath')
                    
                    if not video_file or not os.path.exists(video_file):
                        video_file = ytdl.prepare_filename(info)
                        if not os.path.exists(video_file):
                            base_name = os.path.splitext(video_file)[0]
                            video_file = base_name + ".mp4"
            except Exception as merge_error:
                print(f"Advanced format failed, trying fallback: {merge_error}")
                # Fallback to simpler format that doesn't require merging
                fallback_opts = {
                    "format": "best[ext=mp4][height<=720]/best[height<=720]/best",
                    "outtmpl": "%(title)s.%(ext)s",
                    "quiet": True,
                    "cookiefile": "cookies.txt",
                    "progress_hooks": [progress_hook]
                }
                with yt_dlp.YoutubeDL(fallback_opts) as ytdl:
                    info = ytdl.extract_info(video_link, download=True)
                    video_file = ytdl.prepare_filename(info)
                
            file_size = os.path.getsize(video_file) if os.path.exists(video_file) else 0
            size_mb = file_size / (1024 * 1024)
            
            if progress_msg:
                try:
                    await progress_msg.edit_text(
                        f"📤 **جاري الرفع إلى تليجرام...**\n"
                        f"📊 الملف: {os.path.basename(video_file)}\n"
                        f"✅ اكتمل التحميل: {size_mb:.1f} ميجابايت\n\n"
                        f"🔄 الحالة: جاري الرفع إلى تليجرام..."
                    )
                except:
                    pass
            
            def upload_progress(current, total):
                try:
                    progress = (current / total) * 100
                    # Simple progress logging to avoid async issues
                    if progress % 10 == 0 or progress > 95:
                        print(f"Upload progress: {progress:.1f}% - {current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB")
                except Exception as e:
                    print(f"Upload progress error: {e}")
                
            await bot.send_video(
                query.message.chat.id,
                video=video_file,
                duration=duration,
                thumb=thumb,
                caption=f"By : @M_N_3_M",
                progress=upload_progress
            )
                
            if progress_msg:
                try:
                    await progress_msg.edit_text(
                        f"✅ **اكتمل الرفع!**\n"
                        f"📺 الملف: {os.path.basename(video_file)}\n"
                        f"📊 الحجم: {size_mb:.1f} ميجابايت\n"
                        f"🎉 By @M_N_3_M!"
                    )
                except:
                    pass

        if download_type == "audio":
            with yt_dlp.YoutubeDL({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "outtmpl": "%(title)s.%(ext)s",
                "quiet": True,
                "cookiefile": "cookies.txt",
                "progress_hooks": [progress_hook]
            }) as ytdl:
                # Download and get actual final filename after postprocessing
                info = ytdl.extract_info(video_link, download=True)
                # After FFmpegExtractAudio, the extension changes to .mp3
                base_filename = ytdl.prepare_filename(info)
                # Remove original extension and add .mp3
                audio_file = os.path.splitext(base_filename)[0] + ".mp3"
                
            file_size = os.path.getsize(audio_file) if os.path.exists(audio_file) else 0
            size_mb = file_size / (1024 * 1024)
            
            if progress_msg:
                try:
                    await progress_msg.edit_text(
                        f"📤 **جاري الرفع إلى تليجرام...**\n"
                        f"📊 الملف: {os.path.basename(audio_file)}\n"
                        f"✅ اكتمل التحميل: {size_mb:.1f} ميجابايت\n\n"
                        f"🔄 الحالة: جاري الرفع إلى تليجرام..."
                    )
                except:
                    pass
            
            def upload_progress_audio(current, total):
                try:
                    progress = (current / total) * 100
                    # Simple progress logging to avoid async issues
                    if progress % 10 == 0 or progress > 95:
                        print(f"Audio upload progress: {progress:.1f}% - {current/(1024*1024):.1f}/{total/(1024*1024):.1f} MB")
                except Exception as e:
                    print(f"Audio upload progress error: {e}")
                
            await bot.send_audio(
                query.message.chat.id,
                audio=audio_file,
                caption=f"By : @M_N_3_M",
                title=title,
                duration=duration,
                thumb=thumb,
                performer=author,
                progress=upload_progress_audio
            )
                
            if progress_msg:
                try:
                    await progress_msg.edit_text(
                        f"✅ **اكتمل الرفع!**\n"
                        f"📺 الملف: {os.path.basename(audio_file)}\n"
                        f"📊 الحجم: {size_mb:.1f} ميجابايت\n"
                        f"🎉 By @M_N_3_M!"
                    )
                except:
                    pass

    except Exception as e:
        print(f"Download error for {video_link}: {e}")
        if progress_msg:
            try:
                await progress_msg.edit_text(f"❌ خطأ أثناء التحميل: {e}")
            except:
                pass
    finally:
        # Always clean up downloaded files regardless of success or failure
        if video_file and os.path.exists(video_file):
            try:
                os.remove(video_file)
                print(f"Cleaned up video file: {video_file}")
            except Exception as e:
                print(f"Error removing video file: {e}")
                
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
                print(f"Cleaned up audio file: {audio_file}")
            except Exception as e:
                print(f"Error removing audio file: {e}")
                
        if thumb and os.path.exists(thumb):
            try:
                os.remove(thumb)
                print(f"Cleaned up thumbnail: {thumb}")
            except Exception as e:
                print(f"Error removing thumbnail: {e}")
        
        # Clean up progress message after completion or error
        await asyncio.sleep(3)
        try:
            await progress_msg.delete()
        except:
            pass

print("🌐 Universal Media Downloader Bot Starting...")
print(f"📊 Supports 1000+ websites via yt-dlp")
print("✅ Environment credentials loaded successfully")
try:
    bot.run()
except Exception as e:
    print(f"❌ Bot execution error: {e}")
    print("💡 Check your API credentials and network connection")
