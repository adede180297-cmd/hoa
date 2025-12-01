import os
import logging
import random
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
    parts = hhmm.strip().split(":")
    if len(parts) != 2:
        raise ValueError("Time must be HH:MM")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("Invalid hour/minute")
    return h, m

def fmt_td(seconds: int) -> str:
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

def pick(lst):
    return random.choice(lst)

# ===== Câu trả lời random (10 câu mỗi lệnh) =====
START_MSGS = [
    "Bot online rồi nha 😎 Dùng /ancom /uongnuoc HH:MM /divesinh /xuongca /noel /tet",
    "Chào bạn! Bot chạy ngon rồi đây 🤖 Gõ /start xem lệnh nha.",
    "Hoahoabot đã thức giấc 😆 Lệnh: /ancom /uongnuoc /divesinh /xuongca /noel /tet",
    "Bot sẵn sàng phục vụ! Nhớ uống nước và ăn cơm đúng giờ nha 😄",
    "Có mình ở đây rồi! Muốn nhắc gì cứ gõ lệnh 😌",
    "Hê lô hê lô, bot lên sóng! 📡 Dùng /start để xem lệnh.",
    "Xin chào! Bot này chuyên nhắc việc linh tinh cho bạn đó 😂",
    "Bot hoạt động ổn áp nhé! Cứ quăng lệnh là mình trả lời liền.",
    "Đã kết nối thành công 🤝 Thử /ancom hoặc /xuongca xem sao!",
    "Bot bật rồi nè! Điểm danh bằng /ancom đi bạn 😆",
]

ANCOM_JOKES = [
    "🍚 Ăn cơm đi bạn ơi, đói là dễ quạo lắm đó 😆",
    "🍚 Cơm mà không ăn là cơm khóc đó nha 😂",
    "🍚 Nạp cơm để còn chiến deadline chứ bạn 😎",
    "🍚 Đói bụng thì IQ tụt, đi ăn lẹ đi 😵‍💫",
    "🍚 Ăn cơm xong rồi tính tiếp, đừng tính lúc đói 😄",
    "🍚 Đi ăn cơm đi, bụng réo nghe mệt dùm luôn 😅",
    "🍚 Không ăn cơm là chiều nay yếu đuối đó nha 😤",
    "🍚 Ăn cơm đúng giờ = sống thọ + vui vẻ 😋",
    "🍚 Lát nữa hối hận vì đói thì muộn rồi, ăn thôi!",
    "🍚 Cơm nóng canh ngon đang đợi kìa, triển nè!",
]

DIVESINH_JOKES = [
    "🚽 Đi vệ sinh đi bạn, nhịn là phản khoa học 😆",
    "🚽 Tới giờ giải phóng rồi đó, đi lẹ cho nhẹ người 😄",
    "🚽 Đừng ôm nỗi buồn trong bụng, đi xả đi 😅",
    "🚽 Đi đi cho thoải mái, về làm mới hăng 😎",
    "🚽 Nhịn là hại thận đó nha 😤 Đi ngay!",
    "🚽 Nhanh gọn lẹ rồi comeback mạnh mẽ 😆",
    "🚽 Đi vệ sinh xong là tâm hồn trong sáng liền ✨",
    "🚽 Đầu óc đang lag à? Đi vệ sinh cái cho tỉnh 😄",
    "🚽 Đi phát cho nhẹ bụng, nhẹ luôn deadline 🤭",
    "🚽 Đi thôi, để bụng biểu tình là mệt lắm!",
]

UONGNUOC_SET_MSGS = [
    "💧 Ok! Mình nhắc bạn uống nước giờ {t} mỗi ngày nha.",
    "💧 Đã đặt nhắc lúc {t}. Uống nước đều đều cho tỉnh 😄",
    "💧 Nhắc nước lúc {t} xịn sò luôn. Đừng để khô cổ nha!",
    "💧 Chuẩn! {t} mỗi ngày mình ping bạn liền 😎",
    "💧 Set kèo uống nước {t} thành công. Nhớ nghe lời bot 😆",
    "💧 Lịch uống nước {t} đã lưu. Tới giờ là réo liền!",
    "💧 Đặt nhắc {t} rồi đó. Uống nước cho đẹp da nha 😋",
    "💧 Oke bạn! Cứ tới {t} là mình nhắc liền tay.",
    "💧 Mình sẽ gõ cửa lúc {t} mỗi ngày, chuẩn giờ VN luôn.",
    "💧 Done! Nhắc uống nước {t} mỗi ngày nhé bạn.",
]

UONGNUOC_ALARM_MSGS = [
    "💧 Tới giờ uống nước rồi! {m}",
    "💧 Ping ping! Uống nước thôi nào 😄 {m}",
    "💧 Cốc nước đang gọi tên bạn đó 😆 {m}",
    "💧 Đến giờ nạp nước cho cơ thể! {m}",
    "💧 Uống nước đi, đừng để khô như cá mắm 😂 {m}",
    "💧 Giờ vàng uống nước nè! {m}",
    "💧 Tới lịch rồi bạn ơi, uống miếng nha 😋 {m}",
    "💧 Bot nhắc nhẹ: uống nước liền cho khỏe! {m}",
    "💧 Đừng quên uống nước nha! {m}",
    "💧 Nước vào là não chạy mượt liền 😎 {m}",
]

CANCEL_MSGS = [
    "✅ Đã hủy nhắc uống nước rồi nha.",
    "✅ Ok bạn, nhắc uống nước đã bị tắt 😄",
    "✅ Đã xóa lịch nhắc. Khi nào cần thì set lại nha!",
    "✅ Hủy xong rồi đó. Tự giác uống nước nhe 😆",
    "✅ Nhắc nước off. Nhớ đừng quên uống nha 😋",
    "✅ Lịch nhắc đã bay màu 🧹",
    "✅ Done, không nhắc nữa. Nhưng vẫn phải uống đó nha 😤",
    "✅ Hủy lịch thành công, bot nghỉ tay đây 😄",
    "✅ Okela, nhắc uống nước đã tắt.",
    "✅ Đã hủy. Khi nào khát thì gọi bot lại 😆",
]

NO_JOBS_MSGS = [
    "🤔 Chưa có lịch uống nước nào để hủy á.",
    "🤔 Bạn chưa set nhắc nước mà, hủy gì giờ 😆",
    "🤔 Không thấy lịch nào hết. Set trước rồi hủy sau nha 😄",
    "🤔 Trống trơn luôn. Bạn thử /uongnuoc HH:MM đi.",
    "🤔 Không có job nào cả. Bot nhìn thấy số 0 😂",
    "🤔 Chưa đặt thì sao hủy được bạn ơi 😅",
    "🤔 Lịch nhắc nước chưa tồn tại nha.",
    "🤔 Bạn chưa set giờ nhắc đâu, thử lại nhé!",
    "🤔 Không có nhắc để hủy. Bot cũng hơi buồn 😆",
    "🤔 Set nhắc rồi mới hủy được nè bạn.",
]

XUONGCA_BEFORE_MSGS = [
    "🏁 Còn {left} nữa là xuống ca rồi, ráng xíu 😎",
    "🏁 Down ca còn {left} thôi, cố lên bạn ơi 😄",
    "🏁 Sắp được về rồi! Còn {left} nè 😆",
    "🏁 {left} nữa là tự doooo 🥳",
    "🏁 Ráng thêm {left} nữa thôi, về ngủ cho đã!",
    "🏁 Còn {left}. Đếm từng giây cho chóng hết ca 😅",
    "🏁 Nhẫn nại nha, còn {left} là kết thúc ca!",
    "🏁 {left} nữa thôi, bot cũng nóng lòng giùm 😆",
    "🏁 Gần tới đích rồi! {left} nha bạn 😎",
    "🏁 Sắp hết ca, còn đúng {left}!",
]

XUONGCA_AFTER_MSGS = [
    "🏁 Hết ca rồi đó bạn ơi 😆",
    "🏁 Tới giờ về rồi! Ở lại là do đam mê nha 😅",
    "🏁 Ca xong rồi, nghỉ ngơi đi bạn 😄",
    "🏁 Đã qua giờ xuống ca, chúc mừng 🎉",
    "🏁 Hết ca rồi, bot cho bạn về 😎",
    "🏁 Giờ này mà còn làm thì… cứng thật 😆",
    "🏁 Down ca rồi nha, bật chế độ relax thôi!",
    "🏁 Ca kết thúc rồi, đi ăn chơi thôi nào 😋",
    "🏁 Hết ca! Nhớ giữ sức cho mai nha.",
    "🏁 Tạm biệt ca làm, chào tự dooo 🥳",
]

NOEL_MSGS = [
    "🎄 Còn {left} nữa là tới Noel rồi đó!",
    "🎄 Noel sắp tới! Đếm ngược: {left} 😆",
    "🎄 Còn {left} nữa được nghe Jingle Bells full volume 😄",
    "🎄 {left} nữa là ông già Noel ghé thăm 😎",
    "🎄 Gần tới Noel rồi, còn {left} nè!",
    "🎄 Đợi Noel hơi lâu, còn {left} thôi 😅",
    "🎄 Còn {left} nữa là ăn gà rán Noel 🥳",
    "🎄 {left} nữa thôi, chuẩn bị quà đi bạn 😋",
    "🎄 Noel tới nơi rồi! Còn {left}.",
    "🎄 Countdown Noel: {left} 🎅",
]

NOEL_AFTER_MSGS = [
    "🎄 Noel tới rồi đó! Chúc bạn Giáng Sinh vui vẻ 🎅",
    "🎄 Merry Christmas! Noel đang diễn ra nè 😆",
    "🎄 Tới Noel rồi, quẩy thôi bạn 😄",
    "🎄 Noel rồi đóoo! 🎁",
    "🎄 Giáng Sinh vui vẻ nha bạn 😎",
    "🎄 Noel đã tới, nhớ ăn gà rán 😋",
    "🎄 Hohoho! Noel rồi 🎅",
    "🎄 Noel đây rồi, đừng quên tặng quà nha!",
    "🎄 Christmas timeeee 🥳",
    "🎄 Noel rồi bạn ơi, chill thôi!",
]

TET_MSGS = [
    "🧧 Còn {left} nữa là tới Tết rồi đó!",
    "🧧 Tết sắp tới! Countdown: {left} 😆",
    "🧧 {left} nữa thôi là được lì xì 😄",
    "🧧 Còn {left} nữa là bánh chưng lên nồi 😎",
    "🧧 Gần Tết lắm rồi, còn {left} nè!",
    "🧧 Đợi Tết hơi lâu nhưng còn {left} thôi 😅",
    "🧧 {left} nữa là nghỉ dài ngày rồi 🥳",
    "🧧 Còn {left} nữa là về quê ăn Tết 😋",
    "🧧 Countdown Tết: {left}!",
    "🧧 Tết tới nơi rồi! Còn {left}.",
]

TET_AFTER_MSGS = [
    "🧧 Tết tới rồi! Chúc mừng năm mới 🎉",
    "🧧 Năm mới vui vẻ nha bạn 😄",
    "🧧 Tết rồi đóoo! Lì xì đâu 😆",
    "🧧 Chúc bạn ăn Tết thật đã 😎",
    "🧧 Tết đến rồi, chill thôi!",
    "🧧 Happy Lunar New Year 🥳",
    "🧧 Tết đây rồi, nhớ ăn bánh chưng 😋",
    "🧧 Năm mới phát tài phát lộc nha!",
    "🧧 Tết rồi bạn ơi, quẩy lên 🎉",
    "🧧 Xuân sang, chúc bạn mọi điều may mắn!",
]

# ===== Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick(START_MSGS))

async def an_com(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick(ANCOM_JOKES))

async def di_ve_sinh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick(DIVESINH_JOKES))

async def uong_nuoc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            raise ValueError("missing args")

        time_text = context.args[0]
        message_text = " ".join(context.args[1:]) or "Uống nước nhaa 💧"
        hour, minute = parse_hhmm(time_text)

        job_name = f"water_{update.message.chat_id}"
        old_jobs = context.job_queue.get_jobs_by_name(job_name)
        for j in old_jobs:
            j.schedule_removal()

        context.job_queue.run_daily(
            callback=alarm_uongnuoc,
            time=dtime(hour, minute, tzinfo=VN_TZ),
            chat_id=update.message.chat_id,
            data=message_text,
            name=job_name,
        )

        msg = pick(UONGNUOC_SET_MSGS).format(t=time_text)
        await update.message.reply_text(msg)

    except Exception:
        await update.message.reply_text(
            "Sai cú pháp 😅 Ví dụ: /uongnuoc 14:30 hoặc /uongnuoc 14:30 Nhắc uống nước nha"
        )

async def alarm_uongnuoc(context: ContextTypes.DEFAULT_TYPE):
    msg = pick(UONGNUOC_ALARM_MSGS).format(m=context.job.data)
    await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_name = f"water_{update.message.chat_id}"
    jobs = context.job_queue.get_jobs_by_name(job_name)
    if jobs:
        for j in jobs:
            j.schedule_removal()
        await update.message.reply_text(pick(CANCEL_MSGS))
    else:
        await update.message.reply_text(pick(NO_JOBS_MSGS))

async def xuong_ca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shift_end_str = os.getenv("SHIFT_END", "20:00")
    try:
        end_h, end_m = parse_hhmm(shift_end_str)
    except Exception:
        end_h, end_m = 20, 0

    now = datetime.now(VN_TZ)
    end_today = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

    if now <= end_today:
        left_sec = int((end_today - now).total_seconds())
        left = fmt_td(left_sec)
        msg = pick(XUONGCA_BEFORE_MSGS).format(left=left)
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(pick(XUONGCA_AFTER_MSGS))

async def noel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(VN_TZ)
    year = now.year
    target = datetime(year, 12, 25, 0, 0, 0, tzinfo=VN_TZ)
    if now > target:
        target = datetime(year + 1, 12, 25, 0, 0, 0, tzinfo=VN_TZ)

    left_sec = int((target - now).total_seconds())
    if left_sec > 0:
        msg = pick(NOEL_MSGS).format(left=fmt_td(left_sec))
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(pick(NOEL_AFTER_MSGS))

async def tet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mặc định Tết 2026 là 17/02/2026. Muốn đổi năm thì sửa ở đây.
    tet_target = datetime(2026, 2, 17, 0, 0, 0, tzinfo=VN_TZ)
    now = datetime.now(VN_TZ)

    left_sec = int((tet_target - now).total_seconds())
    if left_sec > 0:
        msg = pick(TET_MSGS).format(left=fmt_td(left_sec))
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(pick(TET_AFTER_MSGS))

# ===== Run bot =====
def main():
    token = "8587076270:AAHtFh3M6Xk4Hk_MP9FsEuvp7fedlvBe01A"  # dán token thật của bạn vào đây

    if not token or token == "PASTE_YOUR_REAL_TOKEN_HERE":
        raise RuntimeError("Bạn chưa dán token thật vào biến token!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ancom", an_com))
    app.add_handler(CommandHandler("uongnuoc", uong_nuoc))
    app.add_handler(CommandHandler("divesinh", di_ve_sinh))
    app.add_handler(CommandHandler("xuongca", xuong_ca))
    app.add_handler(CommandHandler("noel", noel))
    app.add_handler(CommandHandler("tet", tet))
    app.add_handler(CommandHandler("cancel", cancel))

    logging.info("Bot is starting (polling)...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
