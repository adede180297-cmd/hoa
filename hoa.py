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

def fmt_td_days(seconds: int) -> str:
    """Format seconds -> 'X ngày Y giờ Z phút T giây' """
    if seconds < 0:
        seconds = 0
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{days} ngày {hours} giờ {minutes} phút {secs} giây"

def pick(lst):
    return random.choice(lst)

# ===== Random replies (10 câu mỗi lệnh) =====
START_MSGS = [
    "🤖 Bot hoahoabot online rồi nha!\n\nMuốn ăn cơm thì /ancom,\nnhắc nước thì /uongnuoc HH:MM nhé 😄",
    "Hello bạn!\n\nBot sẵn sàng phục vụ 😎\nThử /ancom hoặc /xuongca đi nè!",
    "Ping ping! Bot đã thức giấc 🐣\n\nLệnh chính: /ancom /uongnuoc /divesinh /xuongca /noel /tet /hoa",
    "Bot đang trực 24/7 nè 😆\n\nCứ quăng lệnh là mình rep liền!",
    "Kết nối thành công 🤝\n\nUống nước nhớ gọi /uongnuoc nha bạn!",
    "Hoahoabot xuất hiện!\n\nĐói thì /ancom,\nbuồn ngủ thì uống nước 😄",
    "Bot đã online 📡\n\nLật bài bằng /start để xem lệnh nhé!",
    "Xin chào!\n\nMình là bot nhắc việc linh tinh cho bạn 😂",
    "Bot bật rồi nha 😎\n\nThử /noel, /tet hoặc /hoa xem vui không!",
    "Có mình ở đây rồi!\n\nĐừng quên ăn cơm và uống nước đúng giờ 😋",
]

ANCOM_JOKES = [
    "🍚 **Tới giờ ăn cơm rồi đóoo!** 🍚\n\nBụng mà réo lên là não lag liền nha 😵‍💫\nĂn xong rồi chiến tiếp cho máu 😎\n\n🔥 Đi ăn cơm thôi boss!",
    "🍽️ **Ăn cơm điiii!** 🍽️\n\nĐói là dễ cáu, dễ muốn nghỉ làm lắm đó 😂\nNạp năng lượng rồi hẵng chửi deadline nha 😆\n\n👉 Lượn nhẹ đi ăn nào!",
    "🥢 **Cơm nước tới nơi rồi nè!** 🥢\n\nKhông ăn là chiều nay yếu đuối liền 😅\nĂn no mới có lực gánh team chứ 😎\n\n✨ Ăn thôi bạn!",
    "🍚 **Báo động bụng đói!** 🍚\n\nDạ dày kêu inh ỏi rồi đó nghe không 😆\nĂn sớm sống khỏe, ăn trễ sống… run 😵‍💫\n\n🔥 Đi ăn liền!",
    "🍛 **Ăn cơm cái nha!** 🍛\n\nĐói là tụt mood, tụt mood là tụt năng suất 😅\nNạp cơm vô để não chạy mượt hơn 😎\n\n🍚 Triển thôi!",
    "🍜 **Tới giờ nạp năng lượng rồi!** 🍜\n\nBỏ bữa là dạ dày buồn đó nha 😂\nĂn xong quay lại chiến tiếp cho căng 😆\n\n👉 Ăn lẹ nào!",
    "🍲 **Cơm gọi tên bạn kìa!** 🍲\n\nĐể bụng đói là dễ mơ thấy… cơm 😂\nĂn no rồi làm gì cũng trơn tru 😎\n\n🔥 Đi ăn đây!",
    "🍚 **Ăn cơm đúng giờ nha bạn!** 🍚\n\nĐói quá là não đơ liền 😵‍💫\nĂn xong rồi tính tiếp cho tỉnh 😄\n\n✨ Ăn thôi!",
    "🥘 **Ăn đi rồi nói chuyện tiếp!** 🥘\n\nĐói là dễ nói bậy lắm đó 😆\nNạp cơm vô rồi hẵng combat deadline 😎\n\n👉 Lên kèo ăn cơm!",
    "🍚 **Cơm canh sẵn rồi đó!** 🍚\n\nBụng đói là năng lượng off 😅\nĂn xong auto vui vẻ liền 😄\n\n🔥 Đi ăn cơm thôi!",
]

DIVESINH_JOKES = [
    "🚽 **Tới giờ đi vệ sinh rồi đó!** 🚽\n\nNhịn hoài coi chừng bụng biểu tình 😅\nĐi xong nhẹ người, làm việc mới hăng 😎\n\n👉 Đi liền!",
    "🚽 **Xả stress thôi nào!** 🚽\n\nGiữ trong bụng lâu là không ổn đâu 😂\nĐi xong là thấy đời tươi liền 😆\n\n✨ Triển!",
    "🚽 **Đi vệ sinh đi bạn ơi!** 🚽\n\nNhịn là phản khoa học đó nha 😤\nNhẹ bụng nhẹ đầu, khỏe re 😄\n\n👉 Lượn thôi!",
    "🚽 **Tới giờ giải phóng nội tâm!** 🚽\n\nĐi xong là tinh thần phơi phới liền 😆\nĐừng cố chịu đựng nha 😅\n\n🔥 Đi lẹ!",
    "🚽 **Bụng kêu rồi đó!** 🚽\n\nĐừng để nó kêu thành nhạc remix 😆\nĐi cái cho thoải mái nè 😄\n\n👉 Đi ngay!",
    "🚽 **Đi cho nhẹ người nha!** 🚽\n\nNhịn lâu là mệt lắm đó 😵‍💫\nĐi xong quay về chiến tiếp 😎\n\n✨ Let's go!",
    "🚽 **Giờ vàng đi vệ sinh!** 🚽\n\nXả đúng nơi đúng lúc, cuộc đời yên vui 😆\nNhẹ bụng rồi làm gì cũng ngon 😄\n\n👉 Đi nha!",
    "🚽 **Tới giờ rồi còn gì!** 🚽\n\nNhịn là hại thận đó nha 😤\nĐi xong auto tỉnh táo 😎\n\n🔥 Đi thôi!",
    "🚽 **Không đi là bụng giận đó!** 🚽\n\nĐi xong còn có mood làm việc nữa 😄\nNhẹ cái là vui liền 😆\n\n👉 Đi lẹ!",
    "🚽 **Đi phát cho khỏe!** 🚽\n\nBụng nhẹ = tâm trạng nhẹ 😋\nĐi xong quay lại mình chờ 😎\n\n✨ Triển luôn!",
]

UONGNUOC_SET_MSGS = [
    "💧 Ok! Mình nhắc bạn uống nước lúc {t} mỗi ngày nha.",
    "💧 Đã đặt nhắc {t}. Tới giờ mình réo liền 😄",
    "💧 Set kèo uống nước {t} xong rồi đó 😎",
    "💧 Lịch uống nước {t} đã lưu. Nhớ nghe lời bot 😆",
    "💧 Đặt nhắc {t} thành công. Uống đều nha 😋",
    "💧 Done! {t} mỗi ngày mình nhắc một phát.",
    "💧 Oke bạn, tới {t} là ping ping liền.",
    "💧 Nhắc uống nước {t} ok rồi nha!",
    "💧 Mình sẽ nhắc bạn lúc {t} chuẩn giờ VN.",
    "💧 Lịch uống nước {t} đã set.",
]

UONGNUOC_ALARM_MSGS = [
    "💧 Tới giờ uống nước rồi! {m}",
    "💧 Ping ping! Uống nước nè 😄 {m}",
    "💧 Cốc nước đang gọi tên bạn đó 😆 {m}",
    "💧 Nạp nước cho cơ thể thôi! {m}",
    "💧 Đừng để khô cổ nha 😂 {m}",
    "💧 Giờ vàng uống nước! {m}",
    "💧 Tới lịch rồi đó 😋 {m}",
    "💧 Bot nhắc nhẹ: uống nước liền nha {m}",
    "💧 Nhấp vài ngụm cho tỉnh táo nè {m}",
    "💧 Uống nước cái nè, não chạy mượt liền 😎 {m}",
]

CANCEL_MSGS = [
    "✅ Đã hủy nhắc uống nước rồi nha.",
    "✅ Ok bạn, tắt nhắc uống nước rồi 😄",
    "✅ Hủy lịch nhắc xong rồi đó.",
    "✅ Nhắc uống nước đã off 😆",
    "✅ Done, không nhắc nữa nha.",
    "✅ Lịch nhắc bay màu 🧹",
    "✅ Tắt nhắc thành công.",
    "✅ Okela, hủy nhắc rồi.",
    "✅ Hủy xong, tự giác uống nha 😋",
    "✅ Đã hủy nhắc nước.",
]

NO_JOBS_MSGS = [
    "🤔 Chưa có nhắc nào để hủy á.",
    "🤔 Bạn chưa đặt nhắc nước mà 😆",
    "🤔 Không thấy lịch nhắc nào hết.",
    "🤔 Set nhắc trước rồi hủy sau nha 😄",
    "🤔 Trống trơn luôn 😂",
    "🤔 Chưa đặt sao hủy được 😅",
    "🤔 Không có job nào cả.",
    "🤔 Bạn chưa set giờ nhắc đâu.",
    "🤔 Không có nhắc để hủy nè.",
    "🤔 Thử /uongnuoc HH:MM trước đã nhé.",
]

XUONGCA_BEFORE_MSGS = [
    "🏁 Còn {left} nữa là xuống ca 😎",
    "🏁 Down ca còn {left} thôi 😄",
    "🏁 Sắp được về! Còn {left} 😆",
    "🏁 {left} nữa là tự doooo 🥳",
    "🏁 Ráng thêm {left} nữa thôi 😅",
    "🏁 Còn {left} nè, chịu khó xíu!",
    "🏁 Gần tới giờ về rồi, còn {left} nha 😄",
    "🏁 Đếm ngược: {left}!",
    "🏁 {left} nữa thôi, bot nóng lòng giùm 😆",
    "🏁 Còn đúng {left} là hết ca!",
]

XUONGCA_AFTER_MSGS = [
    "🏁 Hết ca rồi đó bạn ơi 😆",
    "🏁 Tới giờ về rồi! Ở lại là do đam mê nha 😅",
    "🏁 Ca xong rồi, nghỉ ngơi đi bạn 😄",
    "🏁 Đã qua giờ xuống ca, chúc mừng 🎉",
    "🏁 Hết ca rồi, bot cho bạn về 😎",
    "🏁 Giờ này mà còn làm thì cứng thật 😆",
    "🏁 Down ca rồi nha, bật chế độ relax thôi!",
    "🏁 Ca kết thúc rồi, đi ăn chơi thôi 😋",
    "🏁 Hết ca! Nhớ giữ sức cho mai nha.",
    "🏁 Tạm biệt ca làm, chào tự dooo 🥳",
]

NOEL_MSGS = [
    "🎄 Còn {left} nữa là tới Noel rồi đó!",
    "🎄 Noel sắp tới! Đếm ngược: {left} 😆",
    "🎄 {left} nữa thôi là nghe Jingle Bells full volume 😄",
    "🎄 Còn {left} nữa là ông già Noel ghé thăm 😎",
    "🎄 Gần Noel lắm rồi, còn {left} nè!",
    "🎄 Đợi Noel hơi lâu nhưng còn {left} thôi 😅",
    "🎄 {left} nữa là ăn gà rán Noel 🥳",
    "🎄 {left} nữa thôi, chuẩn bị quà đi bạn 😋",
    "🎄 Countdown Noel: {left}!",
    "🎄 Noel tới nơi rồi! Còn {left}.",
]

NOEL_AFTER_MSGS = [
    "🎄 Noel tới rồi đó! Merry Christmas 🎅",
    "🎄 Noel rồi! Chúc bạn vui vẻ nha 😆",
    "🎄 Giáng Sinh vui vẻ nhé bạn 😄",
    "🎄 Noel đây rồi đóoo! 🎁",
    "🎄 Christmas timeeee 😎",
    "🎄 Noel tới rồi, nhớ ăn gà rán 😋",
    "🎄 Hohoho! Noel rồi 🎅",
    "🎄 Noel đang diễn ra nè, chill thôi!",
    "🎄 Merry Christmas! 🥳",
    "🎄 Noel rồi bạn ơi, quẩy lên!",
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
    "🧧 Happy Lunar New Year 🥳",
    "🧧 Tết đến rồi, chill thôi!",
    "🧧 Tết đây rồi, nhớ ăn bánh chưng 😋",
    "🧧 Năm mới phát tài phát lộc nha!",
    "🧧 Tết rồi bạn ơi, quẩy lên 🎉",
    "🧧 Xuân sang, chúc bạn may mắn!",
]

# ===== /hoa (10 bài thơ khen Hoa) =====
HOA_POEMS = [
    "🌸 Hoa ơi, tên đẹp như hoa nở,\nNụ cười em dịu nhẹ tháng ngày qua.\nAi nhìn thấy cũng lòng thêm rạng rỡ,\nChỉ mong hoài được cạnh một đóa hoa.",
    "🌼 Gọi em là Hoa, trời xanh cũng mát,\nGió ngang qua thơm ngát cả con đường.\nTính em hiền như mây chiều man mác,\nLàm tim này cứ vấn vương… vấn vương.",
    "🌺 Hoa là nắng sớm trong veo,\nLà câu chuyện nhỏ gieo vào bình yên.\nAi gặp một lần là nhớ,\nNhớ hoài cái vẻ dịu hiền dễ thương.",
    "🌻 Hoa cười một cái, ngày vui cả bữa,\nHoa nói một câu, trời nhẹ tênh tênh.\nEm như đóa hướng dương vừa chớm nở,\nĐứng đâu là sáng ở nơi mình.",
    "💐 Hoa không chỉ là tên gọi,\nMà còn là cả một trời đáng yêu.\nNhẹ nhàng như gió qua chiều,\nMà làm người khác thương nhiều không hay.",
    "🌷 Hoa bước qua, mùa xuân ghé lại,\nMắt em cười làm phố cũng thành thơ.\nAi bảo đời nhiều khi mệt mỏi,\nGặp em rồi, tự dưng thấy đợi chờ.",
    "🏵️ Hoa là hoa của lòng người,\nKhông cần rực rỡ vẫn tươi lạ thường.\nHiền như giọt nắng trên tường,\nMà sao ai cũng nhớ thương thật nhiều.",
    "🌹 Hoa đẹp chẳng phải vì son phấn,\nMà vì em sống chân thành, dễ thương.\nMột chút dịu dàng, một chút sâu thương,\nKhiến ai gặp cũng muốn vương… một đời.",
    "🌸 Hoa ơi, em là mùa trong mắt,\nLà giấc mơ lành giữa bộn bề lo.\nChỉ cần em cười là lòng bớt chật,\nNhư cánh hoa rơi cũng hóa thành thơ.",
    "🌼 Nếu hỏi ai là điều dễ mến,\nThì chắc chắn có tên của Hoa.\nVừa dịu dàng, vừa hay quan tâm lắm,\nHoa ở đâu, ở đó thấy ôn hòa."
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
        left_txt = fmt_td_days(left_sec)
        msg = pick(NOEL_MSGS).format(left=left_txt)
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(pick(NOEL_AFTER_MSGS))

async def tet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mặc định Tết 2026 là 17/02/2026. Muốn đổi năm thì sửa ở đây.
    tet_target = datetime(2026, 2, 17, 0, 0, 0, tzinfo=VN_TZ)
    now = datetime.now(VN_TZ)

    left_sec = int((tet_target - now).total_seconds())
    if left_sec > 0:
        left_txt = fmt_td_days(left_sec)
        msg = pick(TET_MSGS).format(left=left_txt)
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(pick(TET_AFTER_MSGS))

# ===== /hoa =====
async def hoa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick(HOA_POEMS))

# ===== Run bot =====
def main():
    token = "PASTE_YOUR_REAL_TOKEN_HERE"  # dán token thật (token mới) vào đây

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
    app.add_handler(CommandHandler("hoa", hoa))
    app.add_handler(CommandHandler("cancel", cancel))

    logging.info("Bot is starting (polling)...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
