# ==========================================
# الجزء الأول: المكتبات والإعدادات والتهيئة
# ==========================================
import os
import sys
import time
import math
import asyncio
import logging
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)

# إعداد السجل (Logger) لمتابعة العمليات بالكونسول
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("QSM_Bot_Pro")

# بيانات الاتصال الخاصة بالبوت
API_ID = 34550810
API_HASH = "7074624ed7873407bacfef90e2c0a877"
BOT_TOKEN = "8648166375:AAEkUitY5Gkkxxtu3hKegsZwixxepKkeTo4"

# مجلد التخزين المؤقت للوسائط المسحوبة
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# تهيئة عميل بوت تيليجرام (Pyrogram Client)
app = Client(
    "qsm_content_saver_bot_pro",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)
# ==========================================
# الجزء الثاني: إدارة إعدادات وحالات المستخدمين
# ==========================================
user_settings = {}

def get_setting(user_id: int, key: str, default=False):
    """جلب حالة إعداد معين للمستخدم، وإن لم يوجد يتم إنشاؤه بالقيم الافتراضية"""
    if user_id not in user_settings:
        user_settings[user_id] = {
            "header": False,
            "footer": False,
            "private_rights": True,
            "smart_compress": False,
            "watermark": False,
            "auto_mp3": False,
            "hybrid_engine": True,
            "fetch_mode": "public",        # النمط الافتراضي للسحب (قناة عامة)
            "waiting_for_phone": False,
            "remove_thumb_rights": False,
            "custom_thumb_path": None,
            "video_watermark_text": "Qˢᴹ",
            "watermark_size": 24,
            "watermark_position": "bottom-right", # bottom-right, top-left, center, etc.
            "extra_hashtag": "#QSM"     # حالة انتظار رقم الهاتف لتسجيل دخول اليوزر بوت
        }
        
    return user_settings[user_id].get(key, default)

def set_setting(user_id: int, key: str, value):
    """تعيين قيمة جديدة لإعداد معين للمستخدم"""
    get_setting(user_id, key)
    user_settings[user_id][key] = value

def toggle_setting(user_id: int, key: str):
    """عكس حالة الإعداد (True / False) للتبديل السريع"""
    current = get_setting(user_id, key)
    user_settings[user_id][key] = not current
    return not current
# ==========================================
# الجزء الثالث: الكيبوردات ولوحات التحكم التفاعلية
# ==========================================
def main_control_panel(user_id: int):
    """لوحة التحكم الرئيسية للبوت"""
    h = lambda key: "🟢 شغال" if get_setting(user_id, key) else "🔴 معطل"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 سحب محتوى", callback_data="menu_fetch"),
            InlineKeyboardButton("⚙️ إعدادات الحقوق", callback_data="menu_rights")
        ],
        [
            InlineKeyboardButton("🏷️ العنوان والهاشتاق", callback_data="setting_header"),
            InlineKeyboardButton("🖼️ الصورة المصغرة", callback_data="setting_thumb")
        ],
        [
            InlineKeyboardButton("💧 العلامة المائية", callback_data="setting_watermark"),
            InlineKeyboardButton("⏰ الجدولة", callback_data="menu_cron")
        ],
        [
            InlineKeyboardButton(f"🎵 تلقائي MP3: {h('auto_mp3')}", callback_data="toggle_auto_mp3"),
            InlineKeyboardButton(f"🤖 تصنيف ذكي: {h('smart_compress')}", callback_data="toggle_smart")
        ],
        [
            InlineKeyboardButton(f"✍️ إزالة الحقوق: {h('private_rights')}", callback_data="toggle_rights"),
            InlineKeyboardButton(f"⚡ المحرك الهجين: {h('hybrid_engine')}", callback_data="toggle_hybrid")
        ],
        [
            InlineKeyboardButton("👤 حسابي", callback_data="menu_account"),
            InlineKeyboardButton("⭐ اشحن رصيدك", callback_data="menu_stars")
        ],
        [
            InlineKeyboardButton("🎁 الإحالة", callback_data="menu_referral"),
            InlineKeyboardButton("📊 إحصائياتي", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton("❓ مساعدة", callback_data="menu_help"),
            InlineKeyboardButton("⚙️ الإعدادات الشاملة", callback_data="menu_settings")
        ]
    ])

def fetch_menu_keyboard(user_id: int):
    """قائمة قسم سحب المحتوى (تحتوي الأزرار الأربعة وتدعم علامات الصح التفاعلية)"""
    mode = get_setting(user_id, "fetch_mode", "public")
    
    m_pub = "✅ " if mode == "public" else ""
    m_priv = "✅ " if mode == "private" else ""
    m_grp = "✅ " if mode == "group" else ""
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{m_pub}📢 السحب من قناة عامة", callback_data="set_mode_public")],
        [InlineKeyboardButton(f"{m_priv}🔒 السحب من قناة خاصة", callback_data="set_mode_private")],
        [InlineKeyboardButton("🔑 تسجيل دخول الحساب (Userbot)", callback_data="fetch_login_userbot")],
        [InlineKeyboardButton(f"{m_grp}👥 السحب من القروبات (خاصة وعامة)", callback_data="set_mode_group")],
        [InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="back_home")]
    ])
def rights_control_panel(user_id: int):
    """لوحة إعدادات الحقوق والوسائط الأربعة المتطورة"""
    h = lambda key: "🟢 مفعل" if get_setting(user_id, key) else "🔴 معطل"
    
    thumb_status = "🖼️ مُضافة" if get_setting(user_id, "custom_thumb_path") else "❌ افتراضية"
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"1️⃣ إزالة الحقوق والصورة: {h('remove_thumb_rights')}", callback_data="toggle_remove_rights")
        ],
        [
            InlineKeyboardButton(f"2️⃣ إضافة/تغيير الصورة المصغرة [{thumb_status}]", callback_data="rights_set_thumb")
        ],
        [
            InlineKeyboardButton("3️⃣ حقوق الفيديو (الحجم والموقع التفاعلي)", callback_data="rights_video_watermark")
        ],
        [
            InlineKeyboardButton("4️⃣ إضافة الهاشتاق والنص الأصلي", callback_data="rights_extra_hashtag")
        ],
        [
            InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="back_home")
        ]
    ])
def back_home_keyboard():
    """زر الرجوع للقائمة الرئيسية"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="back_home")]
    ])
# ==========================================
# الجزء الرابع: دوال تنسيق الحجم وشريط التقدم
# ==========================================
# ==========================================
# الجزء الرابع: دوال تنسيق الحجم، شريط التقدم، وحرق الحقوق بالفيديو (FFmpeg)
# ==========================================
import subprocess

def human_readable_size(size_bytes):
    """تحويل بايتات الملف إلى صيغة مقروءة للبشر"""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

async def progress_for_pyrogram(current, total, message: Message, start_time, action_text="جاري التحميل"):
    """دالة شريط التحميل والرفع التفاعلي في الرسائل والكونسول"""
    now = time.time()
    diff = now - start_time
    if round(diff) % 2 == 0 and current != total:
        return
    
    percentage = current * 100 / total if total > 0 else 0
    speed = current / diff if diff > 0 else 0
    eta = (total - current) / speed if speed > 0 else 0
    
    completed = int(percentage // 10)
    progress_bar = "█" * completed + "░" * (10 - completed)
    
    sys.stdout.write(
        f"\r[QSM Terminal] {action_text}: [{progress_bar}] {percentage:.1f}% | "
        f"{human_readable_size(current)} / {human_readable_size(total)} | "
        f"Speed: {human_readable_size(speed)}/s"
    )
    sys.stdout.flush()
    
    progress_text = (
        f"📥 **{action_text}...**\n\n"
        f"[{progress_bar}] `{percentage:.1f}%`\n\n"
        f"📦 الحجم: `{human_readable_size(current)}` من `{human_readable_size(total)}`\n"
        f"⚡ السرعة: `{human_readable_size(speed)}/s`\n"
        f"⏳ المتبقي: `{int(eta)} ثانية`"
    )
    try:
        await message.edit_text(progress_text)
    except Exception:
        pass

def apply_video_watermark(input_video_path, output_video_path, text, size=24, position="bottom-right"):
    """دالة دمج الحقوق مع صندوق خلفي شفاف (بنفس ستايل الصورة) باستخدام FFmpeg"""
    
    # حساب الإحداثيات للموقع
    pos_map = {
        "bottom-right": "x=w-tw-30:y=h-th-30",
        "bottom-left": "x=30:y=h-th-30",
        "top-right": "x=w-tw-30:y=30",
        "top-left": "x=30:y=30",
        "center": "x=(w-tw)/2:y=(h-th)/2"
    }
    
    # فلتر مركب: الأول ترسم مستطيل خلف النص (صندوق مظلل شفاف)، والثاني ترسم النص فوقه
    # box=1 تفعيل الصندوق، boxcolor لون الخلفية (أسود مع شفافية 0.5)، boxborderw مساحة الحشوة حول النص
    pos_expression = pos_map.get(position, "x=w-tw-30:y=h-th-30")
    
    # استخراج الإحداثيات بشكل دقيق لفلتر الصندوق والنص معا
    # استخدام drawtext مع خاصية box المدمجة لضمان تطابق حجم المستطيل تماماً مع النص
    # box=1:boxcolor=black@0.4:boxborderw=10 (صندوق أسود شفاف مع حشوة مرتبة)
    filter_complex = (
        f"drawtext=text='{text}':fontsize={size}:fontcolor=white:"
        f"box=1:boxcolor=black@0.5:boxborderw=12:{pos_expression}"
    )
    
    cmd = [
        "ffmpeg", "-y", "-i", input_video_path,
        "-vf", filter_complex,
        "-codec:a", "copy", output_video_path
    ]
    
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode != 0:
            print(f"\n[❌ FFmpeg Box Watermark Failed]: {process.stderr}")
            return False
        return True
    except Exception as e:
        print(f"\n[❌ Exception]: {e}")
        return False
# ==========================================
# الجزء الخامس (المعدل): معالجات الروابط وإرسال كود اليوزر بوت الفعلي
# ==========================================

# تخزين مؤقت لجلسات اليوزر بوت قيد الإنشاء لكل مستخدم
temp_userbot_sessions = {}

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """معالج أمر /start وعرض اللوحة الرئيسية"""
    user_id = message.from_user.id
    welcome_text = (
        "🔥 **أهلاً بك في بوت حفظ المحتوى المطور (Qˢᴹ)**\n\n"
        "أرسل رابط أي منشور وسيجلبها لك البوت فوراً مع شريط التحميل! 🔍🔥\n\n"
        "اختر من لوحة التحكم أدناه:"
    )
    await message.reply_text(text=welcome_text, reply_markup=main_control_panel(user_id))

@app.on_message((filters.text | filters.photo) & ~filters.regex(r"^/"))
async def link_handler(client: Client, message: Message):
    """معالج النصوص والوسائط: يستقبل الصور المصغرة، الهاشتاق، رقم الهاتف، أو روابط تليجرام"""
    user_id = message.from_user.id
    
    # 1. استقبال وحفظ الصورة المصغرة المخصصة عند تفعيل الحالة
    if get_setting(user_id, "waiting_for_custom_thumb") and message.photo:
        photo = message.photo.file_id
        file_path = await client.download_media(photo, file_name=str(DOWNLOAD_DIR) + f"/thumb_{user_id}.jpg")
        set_setting(user_id, "custom_thumb_path", file_path)
        set_setting(user_id, "waiting_for_custom_thumb", False)
        await message.reply_text("✅ **تم حفظ الصورة المصغرة بنجاح وربطها بالملفات!** 🖼️", reply_markup=rights_control_panel(user_id))
        return

    # استخراج النص إن وجد بأمان
    text = message.text.strip() if message.text else ""

    # 2. استقبال الهاشتاق الجديد
    if get_setting(user_id, "waiting_for_hashtag"):
        set_setting(user_id, "extra_hashtag", text)
        set_setting(user_id, "waiting_for_hashtag", False)
        await message.reply_text(f"✅ **تم اعتماد الهاشتاق/النص الإضافي بنجاح:**\n`{text}`", reply_markup=rights_control_panel(user_id))
        return

    # 3. استقبال نص الحقوق الجديد للفيديو
    if get_setting(user_id, "waiting_for_wm_text"):
        set_setting(user_id, "video_watermark_text", text)
        set_setting(user_id, "waiting_for_wm_text", False)
        await message.reply_text(f"✅ **تم تحديث نص حقوق الفيديو إلى:** `{text}`", reply_markup=rights_control_panel(user_id))
        return

    # 4. معالجة حالة استقبال رقم الهاتف لتسجيل دخول اليوزر بوت فعلياً
    if get_setting(user_id, "waiting_for_phone"):
        phone_number = text
        status_msg = await message.reply_text(f"⏳ **جاري الاتصال بسيرفرات تيليجرام وإرسال الكود للرقم:** `{phone_number}`...")
        
        try:
            ubot = Client(
                f"session_{user_id}",
                api_id=API_ID,
                api_hash=API_HASH
            )
            await ubot.connect()
            sent_code = await ubot.send_code(phone_number)
            
            temp_userbot_sessions[user_id] = {
                "client": ubot,
                "phone": phone_number,
                "phone_code_hash": sent_code.phone_code_hash
            }
            
            set_setting(user_id, "waiting_for_phone", False)
            set_setting(user_id, "waiting_for_otp", True)
            
            await status_msg.edit_text(
                f"✅ **تم إرسال كود التحقق بنجاح إلى حسابك في تيليجرام (على الرقم `{phone_number}`)!**\n\n"
                "👉 **يرجى إرسال الكود هنا في الشات:**"
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ **فشل إرسال الكود:**\n`{str(e)}`")
            set_setting(user_id, "waiting_for_phone", False)
        return

    # 5. معالجة حالة استقبال كود التحقق (OTP)
    if get_setting(user_id, "waiting_for_otp"):
        otp_code = text.replace(" ", "")
        session_data = temp_userbot_sessions.get(user_id)
        
        if not session_data:
            await message.reply_text("⚠️ انتهت صلاحية الجلسة أو حدث خطأ. يرجى إعادة محاولة تسجيل الدخول من جديد.")
            set_setting(user_id, "waiting_for_otp", False)
            return
            
        status_msg = await message.reply_text("⏳ **جاري التحقق من الكود وتسجيل الدخول...**")
        ubot = session_data["client"]
        phone = session_data["phone"]
        phone_code_hash = session_data["phone_code_hash"]
        
        try:
            await ubot.sign_in(phone, phone_code_hash, otp_code)
            await status_msg.edit_text("✅ **تم تسجيل دخول اليوزر بوت بنجاح تام!** 🎉")
            set_setting(user_id, "waiting_for_otp", False)
            temp_userbot_sessions.pop(user_id, None)
        except Exception as e:
            err_str = str(e)
            if "SessionPasswordNeeded" in err_str or "PASSWORD_HASH_REQUIRED" in err_str or "401" in err_str and "PASSWORD" in err_str.upper():
                set_setting(user_id, "waiting_for_otp", False)
                set_setting(user_id, "waiting_for_password", True)
                await status_msg.edit_text("🔒 **حسابك محمي بكلمة مرور التحقق بخطوتين (Password):**\n\n👉 **أرسل كلمة المرور الآن:**")
            else:
                await status_msg.edit_text(f"❌ **خطأ في الكود المدخل:**\n`{err_str}`\n\nأرسل الكود الصحيح مجدداً.")
        return

    # 6. معالجة كلمة المرور بخطوتين إن وجدت
    if get_setting(user_id, "waiting_for_password"):
        password = text
        session_data = temp_userbot_sessions.get(user_id)
        status_msg = await message.reply_text("⏳ **جاري التحقق من كلمة المرور...**")
        ubot = session_data["client"]
        
        try:
            await ubot.check_password(password)
            await status_msg.edit_text("✅ **تم تسجيل الدخول وتخطي التحقق بخطوتين بنجاح تام!** 🔥")
            set_setting(user_id, "waiting_for_password", False)
            temp_userbot_sessions.pop(user_id, None)
        except Exception as e:
            await status_msg.edit_text(f"❌ **كلمة المرور غير صحيحة:**\n`{str(e)}`\n\nأعد إرسال كلمة المرور الصحيحة:")
        return
    
    # 7. معالجة الروابط وسحب المحتوى وتطبيق الحقوق والصورة والهاشتاق
    if "t.me/" in text or "telegram.me/" in text:
        status_msg = await message.reply_text("⏳ **جاري تحليل الرابط وسحب المحتوى...**")
        start_time = time.time()
        
        try:
            parts = text.split("t.me/")[-1].split("/")
            
            # تحديد ما إذا كانت القناة خاصة (تحتوي على c/) أو عامة
            is_private_link = "c/" in text
            
            if is_private_link:
                chat_id = int("-100" + parts[1])
                msg_id = int(parts[2].split("?")[0])
            else:
                chat_id = parts[0]
                msg_id = int(parts[1].split("?")[0])
                
            # اختيار العميل المناسب: إذا كانت خاصة نستخدم اليوزر بوت المسجل، وإذا عامة نستخدم البوت العادي
            fetch_client = client
            if is_private_link:
                if user_id in temp_userbot_sessions:
                    fetch_client = temp_userbot_sessions[user_id]["client"]
                else:
                    try:
                        fetch_client = Client(
                            f"session_{user_id}",
                            api_id=API_ID,
                            api_hash=API_HASH
                        )
                        await fetch_client.connect()
                        temp_userbot_sessions[user_id] = {"client": fetch_client}
                    except Exception as e:
                        print(f"Session error: {e}")
                        fetch_client = None

                if not fetch_client or not fetch_client.is_connected:
                    await status_msg.edit_text(
                        "🔒 **هذه قناة خاصة!**\n\n"
                        "⚠️ لم يتم التعرف على جلسة اليوزر بوت الخاصة بك. يرجى تسجيل الدخول (Userbot) من الأزرار مرة أخرى."
                    )
                    return

            # حل مشكلة الـ Peer الخاصة بالقنوات الخاصة
            if is_private_link:
                try:
                    await fetch_client.get_chat(chat_id)
                except Exception as err:
                    print(f"Peer resolve warning: {err}")

            # جلب الرسالة عبر العميل المناسب
            target_msg = await fetch_client.get_messages(chat_id, msg_id)
            
            if not target_msg or (not target_msg.media and not target_msg.text):
                await status_msg.edit_text("⚠️ **عذراً:** لم يتم العثور على محتوى أو أن الحساب ليس عضواً في هذه القناة.")
                return
                
            if target_msg.media:
                await status_msg.edit_text("📥 **جاري تحميل الملف الأصلي...**")
                
                downloaded_file_path = await fetch_client.download_media(
                    target_msg,
                    file_name=str(DOWNLOAD_DIR) + "/",
                    progress=progress_for_pyrogram,
                    progress_args=(status_msg, start_time, "جاري التحميل")
                )
                
                remove_rights = get_setting(user_id, "remove_thumb_rights")
                custom_thumb = get_setting(user_id, "custom_thumb_path")
                hashtag = get_setting(user_id, "extra_hashtag", "#QSM")
                
                original_caption = target_msg.caption or ""
                final_caption = original_caption
                if hashtag and not remove_rights:
                    if original_caption:
                        final_caption = f"{original_caption}\n\n{hashtag}"
                    else:
                        final_caption = hashtag

                final_file_path = downloaded_file_path
                
                # حرق الحقوق بالفيديو
                is_video = downloaded_file_path.lower().endswith((".mp4", ".mkv", ".mov"))
                if is_video and not remove_rights:
                    wm_text = get_setting(user_id, "video_watermark_text", "Qˢᴹ")
                    wm_size = get_setting(user_id, "watermark_size", 24)
                    wm_pos = get_setting(user_id, "watermark_position", "bottom-right")
                    
                    watermarked_path = str(DOWNLOAD_DIR) + f"/wm_{user_id}.mp4"
                    await status_msg.edit_text("💧 **جاري حرق الحقوق والصندوق الشفاف على الفيديو عبر FFmpeg...**")
                    
                    success = apply_video_watermark(downloaded_file_path, watermarked_path, wm_text, wm_size, wm_pos)
                    if success and os.path.exists(watermarked_path):
                        final_file_path = watermarked_path

                await status_msg.edit_text("📤 **جاري الرفع مع الصورة المصغرة والشعار والتعديلات...**")
                
                thumb_to_send = None
                if custom_thumb and not remove_rights and os.path.exists(str(custom_thumb)):
                    thumb_to_send = str(custom_thumb)

                if final_file_path.lower().endswith((".mp4", ".mkv", ".mov")):
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=final_file_path,
                        caption=final_caption,
                        thumb=thumb_to_send,
                        progress=progress_for_pyrogram,
                        progress_args=(status_msg, start_time, "جاري الرفع")
                    )
                else:
                    await client.send_document(
                        chat_id=message.chat.id,
                        document=final_file_path,
                        caption=final_caption,
                        thumb=thumb_to_send,
                        progress=progress_for_pyrogram,
                        progress_args=(status_msg, start_time, "جاري الرفع")
                    )
                
                for p in [downloaded_file_path, str(DOWNLOAD_DIR) + f"/wm_{user_id}.mp4"]:
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except:
                            pass
                            
                await status_msg.delete()
            else:
                text_content = target_msg.text or ""
                if hashtag and not remove_rights:
                    text_content = f"{text_content}\n\n{hashtag}"
                await status_msg.edit_text(f"📝 **النص المسحوب:**\n\n{text_content}")
                
        except Exception as e:
            logger.error(f"Error: {e}")
            await status_msg.edit_text(f"❌ **حدث خطأ أثناء السحب:**\n`{str(e)}`")
    else:
        if message.text:
            await message.reply_text("⚠️ أرسل رابط منشور تليجرام صحيح أو أكمل إرسال البيانات المطلوبة.")
@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    """معالج تفاعلات الأزرار (Inline Buttons Callbacks) شغال 100%"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # 1. تفعيل الإعدادات العامة (Toggle)
    if data.startswith("toggle_"):
        if data == "toggle_remove_rights":
            new_state = toggle_setting(user_id, "remove_thumb_rights")
            status_str = "مفعل 🟢" if new_state else "معطل 🔴"
            await callback_query.answer(f"تم تغيير الحالة: {status_str}", show_alert=False)
            try:
                await callback_query.message.edit_text(
                    "⚙️ **قسم إعدادات الحقوق والوسائط المتقدمة:**\n\nاختر التعديل المطلوب بدقة:",
                    reply_markup=rights_control_panel(user_id)
                )
            except Exception:
                pass
            return

        key_map = {
            "toggle_auto_mp3": "auto_mp3",
            "toggle_smart": "smart_compress",
            "toggle_rights": "private_rights",
            "toggle_hybrid": "hybrid_engine"
        }
        setting_key = key_map.get(data)
        if setting_key:
            new_state = toggle_setting(user_id, setting_key)
            status_str = "شغال 🟢" if new_state else "معطل 🔴"
            await callback_query.answer(f"تم تغيير الحالة: {status_str}", show_alert=False)
            try:
                await callback_query.message.edit_reply_markup(reply_markup=main_control_panel(user_id))
            except Exception:
                pass
                
    # 2. زر إعدادات الحقوق الرئيسي (الذي يفتح الأزرار الأربعة)
    elif data == "menu_rights":
        await callback_query.message.edit_text(
            "⚙️ **قسم إعدادات الحقوق والوسائط المتقدمة:**\n\nاختر التعديل المطلوب بدقة:",
            reply_markup=rights_control_panel(user_id)
        )

    # 3. الزر الأول: إزالة الحقوق والصورة (تمت معمجته بالأعلى عبر toggle_remove_rights)

    # 4. الزر الثاني: إضافة/تغيير الصورة المصغرة
    elif data == "rights_set_thumb":
        set_setting(user_id, "waiting_for_custom_thumb", True)
        await callback_query.message.edit_text(
            "🖼️ **إضافة صورة مصغرة مخصصة:**\n\n👉 أرسل الآن الصورة في الشات لتعيينها كصورة مصغرة للملفات:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_rights")]])
        )

    # 5. الزر الثالث: حقوق الفيديو (الحجم والموقع والتفاصيل)
    elif data == "rights_video_watermark":
        text_val = get_setting(user_id, "video_watermark_text", "Qˢᴹ")
        size_val = get_setting(user_id, "watermark_size", 24)
        pos_val = get_setting(user_id, "watermark_position", "bottom-right")
        
        await callback_query.message.edit_text(
            f"💧 **إعدادات حقوق الفيديو التفاعلية:**\n\n"
            f"📝 النص الحالي: `{text_val}`\n"
            f"📏 الحجم الحالي: `{size_val}`\n"
            f"📍 الموقع الحالي: `{pos_val}`\n\n"
            "اختر ما تفضل تعديله:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ تغيير نص الحقوق", callback_data="wm_edit_text")],
                [InlineKeyboardButton("📏 تغيير حجم الخط", callback_data="wm_edit_size")],
                [InlineKeyboardButton("📍 تغيير موقع الحقوق بالفيديو", callback_data="wm_edit_pos")],
                [InlineKeyboardButton("🔙 رجوع للإعدادات", callback_data="menu_rights")]
            ])
        )

    # 6. الزر الرابع: إضافة الهاشتاق والنص الأصلي
    elif data == "rights_extra_hashtag":
        current_tag = get_setting(user_id, "extra_hashtag", "#QSM")
        set_setting(user_id, "waiting_for_hashtag", True)
        await callback_query.message.edit_text(
            f"🏷️ **إضافة الهاشتاق والنص التلقائي:**\n\n"
            f"الحالي: `{current_tag}`\n\n"
            "👉 **أرسل الهاشتاق أو التوقيع الجديد في الشات ليضاف مع النصوص المسحوبة:**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_rights")]])
        )

    # --- فرعيات تعديل تفاصيل حقوق الفيديو ---
    elif data == "wm_edit_text":
        set_setting(user_id, "waiting_for_wm_text", True)
        await callback_query.message.edit_text(
            "✏️ **تعديل نص الحقوق:**\n\nأرسل النص الجديد الذي تريد ظهوره داخل الفيديو:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="rights_video_watermark")]])
        )
        
    elif data == "wm_edit_size":
        await callback_query.message.edit_text(
            "📏 **اختر حجم الخط للحقوق داخل الفيديو:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("صغير (16)", callback_data="set_size_16"), InlineKeyboardButton("متوسط (24)", callback_data="set_size_24")],
                [InlineKeyboardButton("كبير (36)", callback_data="set_size_36"), InlineKeyboardButton("كبير جداً (48)", callback_data="set_size_48")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="rights_video_watermark")]
            ])
        )
        
    elif data.startswith("set_size_"):
        val = int(data.split("_")[-1])
        set_setting(user_id, "watermark_size", val)
        await callback_query.answer(f"تم تغيير الحجم إلى: {val}", show_alert=False)
        await callback_query.message.edit_text(
            f"✅ **تم تحديث حجم الخط إلى:** `{val}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="rights_video_watermark")]])
        )
        
    elif data == "wm_edit_pos":
        await callback_query.message.edit_text(
            "📍 **اختر مكان ظهور الحقوق على الفيديو:**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↘️ أسفل اليمين", callback_data="set_pos_bottom-right"), InlineKeyboardButton("↙️ أسفل اليسار", callback_data="set_pos_bottom-left")],
                [InlineKeyboardButton("↗️ أعلى اليمين", callback_data="set_pos_top-right"), InlineKeyboardButton("↖️ أعلى اليسار", callback_data="set_pos_top-left")],
                [InlineKeyboardButton("🎯 المنتصف", callback_data="set_pos_center")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="rights_video_watermark")]
            ])
        )
        
    elif data.startswith("set_pos_"):
        pos_key = data.replace("set_pos_", "")
        set_setting(user_id, "watermark_position", pos_key)
        await callback_query.answer(f"تم تغيير الموقع: {pos_key}", show_alert=False)
        await callback_query.message.edit_text(
            f"✅ **تم ضبط موقع الحقوق في:** `{pos_key}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="rights_video_watermark")]])
        )

    # --- باقي الأزرار الرئيسية للبوت ---
    elif data == "menu_fetch":
        await callback_query.message.edit_text(
            "🔄 **قسم سحب المحتوى المتقدم:**\n\nاختر المصدر المطلوب للسحب الفوري:",
            reply_markup=fetch_menu_keyboard(user_id)
        )
    elif data == "set_mode_public":
        set_setting(user_id, "fetch_mode", "public")
        await callback_query.answer("تم تفعيل وضع: القنوات العامة 📢", show_alert=False)
        await callback_query.message.edit_text(
            "🔄 **قسم سحب المحتوى:**\n\nتم ضبط البوت على وضع **قناة عامة**. أرسل الرابط مباشرة.",
            reply_markup=fetch_menu_keyboard(user_id)
        )
    elif data == "set_mode_private":
        set_setting(user_id, "fetch_mode", "private")
        await callback_query.answer("تم تفعيل وضع: القنوات الخاصة 🔒", show_alert=False)
        await callback_query.message.edit_text(
            "🔄 **قسم سحب المحتوى:**\n\nتم ضبط البوت على وضع **قناة خاصة**. أرسل الرابط.",
            reply_markup=fetch_menu_keyboard(user_id)
        )
    elif data == "set_mode_group":
        set_setting(user_id, "fetch_mode", "group")
        await callback_query.answer("تم تفعيل وضع: القروبات 👥", show_alert=False)
        await callback_query.message.edit_text(
            "🔄 **قسم سحب المحتوى:**\n\nتم ضبط البوت على وضع **القروبات**. أرسل الرابط.",
            reply_markup=fetch_menu_keyboard(user_id)
        )
    elif data == "fetch_login_userbot":
        set_setting(user_id, "waiting_for_phone", True)
        set_setting(user_id, "waiting_for_otp", False)
        set_setting(user_id, "waiting_for_password", False)
        await callback_query.answer("وضع تسجيل الدخول مفعل", show_alert=False)
        await callback_query.message.edit_text(
            "🔑 **تسجيل دخول حساب المستخدم (Userbot):**\n\n👉 **أرسل رقم هاتفك بصيغة دولية (مثل: `+962xxxxxxxx`):**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="menu_fetch")]])
        )
    elif data == "menu_cron":
        await callback_query.message.edit_text("⏰ **الجدولة التلقائية:** نظام مهام Cron متقدم.", reply_markup=back_home_keyboard())
    elif data == "menu_stars":
        await callback_query.message.edit_text("⭐ **محفظة النجوم:** رصيدك الحالي: `0 نجمة`.", reply_markup=back_home_keyboard())
    elif data == "menu_account":
        await callback_query.message.edit_text(f"👤 **معلومات الحساب:**\n🆔 الآيدي: `{user_id}`", reply_markup=back_home_keyboard())
    elif data == "menu_referral":
        ref = f"https://t.me/{client.me.username}?start=ref_{user_id}"
        await callback_query.message.edit_text(f"🎁 **نظام الإحالة:**\nرابطك:\n`{ref}`", reply_markup=back_home_keyboard())
    elif data == "menu_stats":
        await callback_query.message.edit_text("📊 **إحصائياتك:** السيرفر يعمل بأعلى كفاءة.", reply_markup=back_home_keyboard())
    elif data == "menu_help":
        await callback_query.message.edit_text("❓ أرسل رابط المنشور مباشرة وسيتولى البوت الباقي.", reply_markup=back_home_keyboard())
    elif data == "menu_settings":
        await callback_query.message.edit_text("⚙️ **الإعدادات الشاملة:** تحكم كامل بخصائص البوت.", reply_markup=back_home_keyboard())
    elif data == "back_home":
        set_setting(user_id, "waiting_for_phone", False)
        set_setting(user_id, "waiting_for_otp", False)
        set_setting(user_id, "waiting_for_password", False)
        set_setting(user_id, "waiting_for_custom_thumb", False)
        set_setting(user_id, "waiting_for_hashtag", False)
        set_setting(user_id, "waiting_for_wm_text", False)
        await callback_query.message.edit_text(
            "🔥 **أهلاً بك مجدداً في لوحة التحكم الرئيسية (Qˢᴹ):**",
            reply_markup=main_control_panel(user_id)
        )

if __name__ == "__main__":
    logger.info("🤖 تشغيل البوت بالهيكلية المقسمة ومعالجة اليوزر بوت الحقيقية...")
    app.run()