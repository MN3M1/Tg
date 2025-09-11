import os, re, yt_dlp, asyncio, wget, time

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

bot = Client(
    "youtube",
    api_id = 20569963,
    api_hash = "37f536fd550fa5dd70cdaaca39c2b1d7",
    bot_token = "8265705564:AAF67NcivYXYR5Ofh82PfjyUzMK8wZVLnos"
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
            if 'entries' in info:
                return info['entries']
        except Exception as e:
            print(f"An error occurred during search: {e}")
            return None

@bot.on_message((filters.private | filters.group) & filters.text)
async def main(bot, msg):
    if not msg.text:
        return
    if msg.text == "/youtube":
        await bot.send_message(msg.chat.id, f"• مرحبا بك 《 {msg.from_user.mention} 》\n\n• في بوت اليوتيوب ارسل بوت + ماذا تريد \n• يدعم التحميل حتي 2GB")

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

            txt += f"🎬 [{title}](https://youtu.be/{id})\n👤 {channel_name}\n🕑 {duration} - 👁 {views}\n🔗 /dl_{id}\n\n"

        await wait.edit(f'🔎︙نتائج البحث لـ "{search_query}"\n\n{txt}', disable_web_page_preview=True)
        return  # Exit early to avoid processing other conditions

    # Check for YouTube links (including shorts)
    youtube_pattern = r'(?:https?://)?(?:(?:www|m|music)\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|shorts/)?([a-zA-Z0-9_-]{11})'
    youtube_match = re.search(youtube_pattern, msg.text)
    
    if youtube_match:
        vid_id = youtube_match.group(1)
        wait = await bot.send_message(msg.chat.id, f'🔎︙البحث عن "https://youtu.be/{vid_id}"...', disable_web_page_preview=True)

        try:
            print(f"Processing YouTube link for video ID: {vid_id}")
            # Use yt-dlp for metadata extraction with cookies
            with yt_dlp.YoutubeDL({
                'quiet': True,
                'cookiefile': 'cookies.txt',
                'extract_flat': False
            }) as ydl:
                info = ydl.extract_info(f"https://youtu.be/{vid_id}", download=False)
                
            title = info.get('title', 'Unknown Title') if info else 'Unknown Title'
            author = info.get('uploader', 'Unknown Channel') if info else 'Unknown Channel'
            views = info.get('view_count', 'N/A') if info else 'N/A'
            thumbnail = info.get('thumbnail') if info else None
            
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("مقطع فيديو 🎞", callback_data=f"video&&{vid_id}"), InlineKeyboardButton("ملف صوتي 📼", callback_data=f"audio&&{vid_id}")]])

            if thumbnail:
                await bot.send_photo(
                    msg.chat.id,
                    photo=thumbnail,
                    caption=f"🎬 [{title}](https://youtu.be/{vid_id})\n👤 {author}\n👁 {views}",
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    msg.chat.id,
                    text=f"🎬 [{title}](https://youtu.be/{vid_id})\n👤 {author}\n👁 {views}",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            print(f"Successfully processed YouTube link: {title}")
        except Exception as e:
            print(f"Error processing YouTube link {vid_id}: {e}")
            await wait.edit(f"❌ خطأ في الوصول للفيديو: {e}")
        finally:
            await wait.delete()
        return  # Exit early to avoid processing other conditions

    if msg.text.startswith("/dl_"):
        vid_id = msg.text.replace("mnem", "-").replace("/dl_", "")
        wait = await bot.send_message(msg.chat.id, f'🔎︙البحث عن "https://youtu.be/{vid_id}"...', disable_web_page_preview=True)

        try:
            print(f"Processing download request for video ID: {vid_id}")
            # Use yt-dlp for metadata extraction with cookies
            with yt_dlp.YoutubeDL({
                'quiet': True,
                'cookiefile': 'cookies.txt',
                'extract_flat': False
            }) as ydl:
                info = ydl.extract_info(f"https://youtu.be/{vid_id}", download=False)
                
            title = info.get('title', 'Unknown Title')
            author = info.get('uploader', 'Unknown Channel')
            views = info.get('view_count', 'N/A')
            thumbnail = info.get('thumbnail')
            
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("مقطع فيديو 🎞", callback_data=f"video&&{vid_id}"), InlineKeyboardButton("ملف صوتي 📼", callback_data=f"audio&&{vid_id}")]])

            if thumbnail:
                await bot.send_photo(
                    msg.chat.id,
                    photo=thumbnail,
                    caption=f"🎬 [{title}](https://youtu.be/{vid_id})\n👤 {author}\n👁 {views}",
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    msg.chat.id,
                    text=f"🎬 [{title}](https://youtu.be/{vid_id})\n👤 {author}\n👁 {views}",
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
            print(f"Successfully processed video: {title}")
        except Exception as e:
            print(f"Error processing video {vid_id}: {e}")
            await wait.edit(f"❌ خطأ في الوصول للفيديو: {e}")
        finally:
            await wait.delete()

@bot.on_callback_query(filters.regex("&&"), group=24)
async def download(bot, query: CallbackQuery):
    await bot.delete_messages(query.message.chat.id, query.message.id)
    data_parts = query.data.split("&&")
    if len(data_parts) < 2:
        return
    video_id = data_parts[1]
    video_link = f"https://youtu.be/{video_id}"
    progress_msg = await bot.send_message(query.message.chat.id, "🚀 بدء التحميل....")
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total > 0:
                progress = (downloaded / total) * 100
                # Simple progress logging to avoid async issues
                if progress % 10 == 0 or progress > 95:
                    print(f"Download progress: {progress:.1f}% - {downloaded/(1024*1024):.1f}/{total/(1024*1024):.1f} MB")

    # Initialize file paths for cleanup
    video_file = None
    audio_file = None
    thumb = None
    
    try:
        print(f"Starting download for: {video_link}")
        # Get video info using yt-dlp for metadata
        with yt_dlp.YoutubeDL({
            'quiet': True,
            'cookiefile': 'cookies.txt',
            'extract_flat': False
        }) as ydl:
            video_info = ydl.extract_info(video_link, download=False)
            
        title = video_info.get('title', 'Unknown Title')
        author = video_info.get('uploader', 'Unknown Channel')
        duration = video_info.get('duration', 0)
        thumbnail_url = video_info.get('thumbnail')
        
        # Download thumbnail
        if thumbnail_url:
            thumb = wget.download(thumbnail_url)
        print(f"Downloaded thumbnail for: {title}")

        if data_parts[0] == "video":
            with yt_dlp.YoutubeDL({
                "format": "best",
                "keepvideo": True,
                "prefer_ffmpeg": False,
                "geo_bypass": True,
                "outtmpl": "%(title)s.%(ext)s",
                "quiet": True,
                "cookiefile": "cookies.txt",
                "progress_hooks": [progress_hook]
            }) as ytdl:
                info = ytdl.extract_info(video_link, download=False)
                video_file = ytdl.prepare_filename(info)
                ytdl.process_info(info)
                
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

        if data_parts[0] == "audio":
            with yt_dlp.YoutubeDL({
                "format": "bestaudio[ext=m4a]",
                "outtmpl": "%(title)s.%(ext)s",
                "quiet": True,
                "cookiefile": "cookies.txt",
                "progress_hooks": [progress_hook]
            }) as ytdl:
                info = ytdl.extract_info(video_link, download=False)
                audio_file = ytdl.prepare_filename(info)
                ytdl.process_info(info)
                
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

print("Bot is starting...")
try:
    bot.run()
except Exception as e:
    print(f"An error occurred during bot execution: {e}")
