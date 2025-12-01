import os
import logging
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# ===== Helpers =====
def parse_hhmm(hhmm: str) -> tuple[int, int]:
    """Parse 'HH:MM' -> (hour, minute)"""
    parts = hhmm.strip().split(":")
    if len(parts) != 2:
        raise ValueError("Time must be HH:MM")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("Invalid hour/minute")
    return h, m

def fmt_td(seconds: int) -> str:
    """Format seconds -> 'X giờ Y phút Z giây' """
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h: parts.append(f"{h} giờ")
    if m: parts.append(f"{m} phút")
    parts.append(f"{s} giây")
    return " ".join(parts)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Bot hoahoabot đã online!** 🤖\n\n"
        "📌 4 lệnh chính nè:\n"
        "🍚 /ancom  → kêu bạn đi ăn cơm kiểu hài hài\n"
        "💧 /uongnuoc HH:MM  → đặt nhắc uống nước mỗi ngày\n"
        "🚽 /divesinh → nhắc đi vệ sinh cho nhẹ người 😆\n"
        "🏁 /xuongca → đếm ngược còn bao lâu được về (giờ VN)\n\n"
        "🧹 Hủy nhắc uống nước: /cancel"
    )

# ===== 1) /ancom =====
async def an_com(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "🍚 **Tới giờ ăn cơm rồi đóoo!** 🍚\n\n"
        "Bụng mà réo lên là não lag liền nha 😵‍💫\n"
        "Ăn xong rồi chiến tiếp cho máu 😎\n\n"
        "🔥 Đi ăn cơm thôi boss!",
        
        "🍚 **Ăn cơm điiii!** 🍚\n\n"
        "Cơm chờ lâu là cơm buồn đó nha 😂\n"
        "Ăn no mới có lực đánh deadline chứ 😤\n\n"
        "👉 Lượn nhẹ đi ăn nào!",
        
        "🍚 **Check in bữa cơm cái nè** 🍚\n\n"
        "Đói quá là dễ cáu… dễ nghỉ việc lắm 😆\n"
        "Ăn cho vui vẻ rồi quay lại làm tiếp nha!\n\n"
        "😋 Mời bạn dùng bữa!"
    ]
    idx = (update.message.id or 0) % len(jokes)
    await update.message.reply_text(jokes[idx])

# ===== 2) /uongnuoc HH:MM =====
async def uong_nuoc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /uongnuoc 14:30
    hoặc /uongnuoc 14:30 Uống nước nhaa
    -> bot nhắc hằng ngày giờ đó
    """
    try:
        if not context.args:
            raise ValueError("missing args")

        time_text = context.args[0]
        message_text = " ".join(context.args[1:]) or "Uống nước nhaa 💧"
        hour, minute = parse_hhmm(time_text)

        # mỗi chat chỉ giữ 1 lịch uống nước (đặt lại sẽ ghi đè)
        job_name = f"water_{update.message.chat_id}"
        old_jobs = context.job_queue.get_jobs_by_name(job_name)
        for j in old_jobs:
            j.schedule_removal()

        context.job_queue.run_daily(
            callback=alarm_uongnuoc,
            time=dtime(hour, minute, tzinfo=VN_TZ),  # timezone VN
            chat_id=update.message.chat_id,
            data=message_text,
            name=job_name,
        )

        await update.message.reply_text(
            "💧 **Đã set nhắc uống nước!** 💧\n\n"
            "Bot sẽ canh giờ cho bạn như canh nồi lẩu 😄\n"
            "Uống đều đều cho da đẹp người xinh nhaaaa ✨\n\n"
            f"⏰ Giờ nhắc: **{time_text}** mỗi ngày\n"
            f"📝 Nội dung: {message_text}"
        )

    except Exception:
        await update.message.reply_text(
            "❌ **Sai cú pháp rồi bạn ơi!**\n\n"
            "Ví dụ nè:\n"
            "`/uongnuoc 14:30`\n"
            "`/uongnuoc 14:30 Nhắc uống nước nha`"
        )

async def alarm_uongnuoc(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=(
            "💧 **Tới giờ uống nước rồi nè!** 💧\n\n"
            f"📌 {context.job.data}\n"
            "Nhấp vài ngụm cho tỉnh táo, đừng để khô như cá mắm nha 😆"
        )
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_name = f"water_{update.message.chat_id}"
    jobs = context.job_queue.get_jobs_by_name(job_name)
    if jobs:
        for j in jobs:
            j.schedule_removal()
        await update.message.reply_text(
            "🧹 **Ok! Đã hủy nhắc uống nước.**\n\n"
            "Khi nào cần nhắc lại thì gọi mình nha 💙"
        )
    else:
        await update.message.reply_text(
            "🤔 **Chưa có nhắc nào để hủy á.**\n\n"
            "Bạn set bằng `/uongnuoc HH:MM` trước đã nhé!"
        )

# ===== 3) /divesinh =====
async def di_ve_sinh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "🚽 **Đi vệ sinh thôi nào!** 🚽\n\n"
        "Đừng cố nhịn nha, nhịn là bụng biểu tình đó 😵‍💫\n"
        "Đi xong nhẹ người, quay lại chiến tiếp 😎\n\n"
        "🏃‍♂️ Let's goooo!",
        
        "🚽 **Tới giờ giải phóng nội tâm** 🚽\n\n"
        "Xả stress đúng nơi đúng chỗ = cuộc đời hạnh phúc 😆\n\n"
        "✨ Chúc bạn nhẹ bụng!"
    ]
    idx = (update.message.id or 0) % len(jokes)
    await update.message.reply_text(jokes[idx])

# ===== 4) /xuongca =====
async def xuong_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tính còn bao lâu xuống ca theo giờ VN.
    Mặc định ca kết thúc 20:00 (8h tối).
    Có thể đổi bằng env SHIFT_END="HH:MM"
    """
    shift_end_str = os.getenv("SHIFT_END", "20:00")
    try:
        end_h, end_m = parse_hhmm(shift_end_str)
    except Exception:
        end_h, end_m = 20, 0

    now = datetime.now(VN_TZ)
    end_today = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

    if now <= end_today:
        delta_sec = int((end_today - now).total_seconds())
        await update.message.reply_text(
            "🏁 **Đếm ngược xuống ca nèeee!** 🏁\n\n"
            "Bot đang hưng phấn năng lượng cùng bạn ⚡\n"
            "Ráng thêm xíu nữa là được tự do rồi đóooo 😎\n\n"
            f"⏳ Còn: **{fmt_td(delta_sec)}**"
        )
    else:
        await update.message.reply_text(
            "🏁 **Hết ca rồi đó bạn ơi!** 🏁\n\n"
            "Nếu bạn còn làm thì là… làm vì đam mê đó nha 😅\n"
            "Nhớ nghỉ ngơi nữa nèee ❤️"
        )

# ===== Run bot =====
def main():
    # CÁCH 2: dán token trực tiếp ở đây
    token = "PASTE_YOUR_REAL_TOKEN_HERE"

    if not token or token == "PASTE_YOUR_REAL_TOKEN_HERE":
        raise RuntimeError("Bạn chưa dán token thật vào biến token!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ancom", an_com))
    app.add_handler(CommandHandler("uongnuoc", uong_nuoc))
    app.add_handler(CommandHandler("divesinh", di_ve_sinh))
    app.add_handler(CommandHandler("xuongca", xuong_ca))
    app.add_handler(CommandHandler("cancel", cancel))

    logging.info("Bot is starting (polling)...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
