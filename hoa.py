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
        "🤖 Bot hoạt động rồi nè!\n\n"
        "4 lệnh chính:\n"
        "🍚 /ancom  -> trả lời hài hước\n"
        "💧 /uongnuoc HH:MM  -> đặt nhắc uống nước mỗi ngày\n"
        "🚽 /divesinh -> trả lời hài hước\n"
        "🏁 /xuongca -> còn bao lâu xuống ca (giờ VN)\n\n"
        "Hủy nhắc uống nước: /cancel"
    )

# ===== 1) /ancom =====
async def an_com(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "🍚 Ăn cơm đi boss ơi, đừng để bụng réo như loa phường!",
        "🍚 Cơm mà không ăn là cơm buồn đó nha 😂",
        "🍚 Đã ăn cơm chưa? Ăn xong nhớ để dành sức… làm tiếp nha!",
        "🍚 Ăn cơm đúng giờ thì mới có lực chiến với deadline 😎",
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
            f"💧 Ok luôn! Mình sẽ nhắc bạn uống nước lúc **{time_text}** mỗi ngày.\n"
            f"Nội dung nhắc: {message_text}"
        )

    except Exception:
        await update.message.reply_text(
            "Sai cú pháp rồi 😅\nVí dụ:\n"
            "`/uongnuoc 14:30`\n"
            "`/uongnuoc 14:30 Nhắc uống nước nha`"
        )

async def alarm_uongnuoc(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"💧 Đến giờ rồi! {context.job.data}\nNhấp vài ngụm cho tỉnh táo nè 😄"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_name = f"water_{update.message.chat_id}"
    jobs = context.job_queue.get_jobs_by_name(job_name)
    if jobs:
        for j in jobs:
            j.schedule_removal()
        await update.message.reply_text("✅ Đã hủy nhắc uống nước.")
    else:
        await update.message.reply_text("Không có nhắc uống nước nào để hủy.")

# ===== 3) /divesinh =====
async def di_ve_sinh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "🚽 Đi vệ sinh nhớ mang theo… niềm vui và đừng mang deadline theo nha 😆",
        "🚽 Có đi là có nhẹ người! Đi lẹ rồi comeback mạnh mẽ 💪",
        "🚽 Xả stress đúng nơi đúng chỗ, chuẩn bài!",
        "🚽 Đi cho thoải mái, về làm việc cho phấn khởi 😄",
    ]
    idx = (update.message.id or 0) % len(jokes)
    await update.message.reply_text(jokes[idx])

# ===== 4) /xuongca =====
async def xuong_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tính còn bao lâu xuống ca theo giờ VN.
    Mặc định ca kết thúc 17:30. Có thể đổi bằng env SHIFT_END="HH:MM"
    """
    shift_end_str = os.getenv("SHIFT_END", "17:30")
    try:
        end_h, end_m = parse_hhmm(shift_end_str)
    except Exception:
        end_h, end_m = 17, 30

    now = datetime.now(VN_TZ)
    end_today = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

    if now <= end_today:
        delta_sec = int((end_today - now).total_seconds())
        await update.message.reply_text(
            f"🏁 Còn **{fmt_td(delta_sec)}** nữa là xuống ca rồi!\n"
            "Cố xíu nữa thôi, sắp được tự do rồi 😎"
        )
    else:
        # đã qua giờ xuống ca -> báo đã hết ca
        await update.message.reply_text(
            "🏁 Hết ca rồi đó bạn ơi! Nếu còn làm thì là… làm vì đam mê đó nha 😅"
        )

# ===== Run bot =====
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing BOT_TOKEN env var")

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
