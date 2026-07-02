# ============================================
# 🐊 CÁ XẤU ROOM - MULTI-ROOM (PYTHON 3.7+)
# 🚀 Admin + Room (đa phòng) + Profile Bot
# ============================================
import random, json, os, logging, threading, time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚙️ THAY BẰNG TOKEN THẬT CỦA BẠN (lấy từ @BotFather)
ADMIN_TOKEN = "8874890400:AAH3wSYqmYewSnJzgSj-SX1-yBCDuxPQiB8"
ROOM_TOKEN = "7945714508:AAGeBzVYjLJjlSM7E2K0QA73i2FuPL6ToyM"
PROFILE_TOKEN = "8888675958:AAHkxzqCmKhI07tiPJIUjc5C2cQcnxexQwo"

# 🔑 THAY BẰNG ID TELEGRAM CỦA BẠN (lấy từ @userinfobot)
ADMIN_IDS = ["8823176709"]

# 📁 File dữ liệu (tự động tạo)
DATA_FILE = "caxau_data.json"
PENDING_FILE = "pending_transactions.json"
SETTINGS_FILE = "room_settings.json"
GIFTCODE_FILE = "giftcodes.json"
ROOMS_FILE = "rooms.json"

# ========== TIỆN ÍCH ==========
def create_table(headers, rows, title=""):
    table = ""
    if title:
        table += f"*{title}*\n"
    table += "┌" + "┬".join(["─" * (len(h) + 2) for h in headers]) + "┐\n"
    table += "│" + "│".join([f" {h} " for h in headers]) + "│\n"
    table += "├" + "┼".join(["─" * (len(h) + 2) for h in headers]) + "┤\n"
    for row in rows:
        row_data = [f" {str(cell).ljust(len(headers[i]))} " for i, cell in enumerate(row)]
        table += "│" + "│".join(row_data) + "│\n"
    table += "└" + "┴".join(["─" * (len(h) + 2) for h in headers]) + "┘"
    return f"```\n{table}\n```"

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== DATABASE CHUNG ==========
class SharedDB:
    def __init__(self):
        self.players = load_json(DATA_FILE)
        self.pending = load_json(PENDING_FILE)
        self.settings = load_json(SETTINGS_FILE) or self.default_settings()
        self.giftcodes = load_json(GIFTCODE_FILE)
        self.rooms = load_json(ROOMS_FILE) or self.default_rooms()

    def default_settings(self):
        return {
            "room_name": "CÁ XẤU ROOM",
            "min_deposit": 10000,
            "daily_bet_requirement": 50000,
            "daily_bonus": 1000
        }

    def default_rooms(self):
        return {
            "main": {
                "id": "main",
                "name": "Phòng Chính",
                "creator": "system",
                "members": [],
                "created_at": datetime.now().isoformat(),
                "settings": {"bet_amount": 10000, "game_duration": 30}
            }
        }

    def save(self):
        save_json(self.players, DATA_FILE)
        save_json(self.pending, PENDING_FILE)
        save_json(self.settings, SETTINGS_FILE)
        save_json(self.giftcodes, GIFTCODE_FILE)
        save_json(self.rooms, ROOMS_FILE)

    def update_vip(self, user_id):
        player = self.players.get(user_id)
        if not player:
            return 0
        total_dep = player.get('total_deposit', 0)
        new_level = 0
        if total_dep >= 5000000:
            new_level = 5
        elif total_dep >= 1000000:
            new_level = 4
        elif total_dep >= 500000:
            new_level = 3
        elif total_dep >= 200000:
            new_level = 2
        elif total_dep >= 50000:
            new_level = 1
        old_level = player.get('vip_level', 0)
        if new_level > old_level:
            player['vip_level'] = new_level
            bonus = {1:10000, 2:50000, 3:200000, 4:500000, 5:2000000}.get(new_level, 0)
            player['balance'] = player.get('balance', 0) + bonus
            return bonus
        return 0

db = SharedDB()

# ========== QUẢN LÝ PHÒNG ==========
class RoomManager:
    @staticmethod
    def create_room(room_id, name, creator_id):
        if room_id in db.rooms:
            return False, "ID phòng đã tồn tại"
        db.rooms[room_id] = {
            "id": room_id,
            "name": name,
            "creator": creator_id,
            "members": [creator_id],
            "created_at": datetime.now().isoformat(),
            "settings": {"bet_amount": 10000, "game_duration": 30}
        }
        db.save()
        return True, room_id

    @staticmethod
    def join_room(room_id, user_id):
        room = db.rooms.get(room_id)
        if not room:
            return False, "Phòng không tồn tại"
        if user_id in room['members']:
            return False, "Bạn đã trong phòng"
        room['members'].append(user_id)
        db.save()
        return True, room['name']

    @staticmethod
    def leave_room(room_id, user_id):
        room = db.rooms.get(room_id)
        if not room:
            return False, "Phòng không tồn tại"
        if user_id not in room['members']:
            return False, "Bạn không ở trong phòng"
        room['members'].remove(user_id)
        db.save()
        return True, room['name']

    @staticmethod
    def list_user_rooms(user_id):
        return [room for room in db.rooms.values() if user_id in room['members']]

    @staticmethod
    def list_all_rooms():
        return list(db.rooms.values())

    @staticmethod
    def get_room(room_id):
        return db.rooms.get(room_id)

# ========== BOT ADMIN ==========
class AdminBot:
    async def start(self, update, context):
        user_id = str(update.effective_user.id)
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Bạn không có quyền Admin!")
            return
        total_players = len(db.players)
        total_balance = sum(p.get('balance', 0) for p in db.players.values())
        total_rooms = len(db.rooms)
        text = create_table(
            ["CHỈ SỐ", "GIÁ TRỊ"],
            [["👥 Người chơi", total_players],
             ["💰 Tổng số dư", f"{total_balance:,}đ"],
             ["🏠 Số phòng", total_rooms],
             ["⏳ Chờ duyệt", len(db.pending)]],
            "🐊 CÁ XẤU ROOM - ADMIN"
        )
        await update.message.reply_text(text, reply_markup=self.main_menu(), parse_mode='Markdown')

    def main_menu(self):
        keyboard = [
            [InlineKeyboardButton("👥 DS người chơi", callback_data="admin_players"),
             InlineKeyboardButton("💰 Duyệt giao dịch", callback_data="admin_pending")],
            [InlineKeyboardButton("🎁 Tạo giftcode", callback_data="admin_giftcode"),
             InlineKeyboardButton("📊 Thống kê", callback_data="admin_stats")],
            [InlineKeyboardButton("🏠 Quản lý phòng", callback_data="admin_rooms"),
             InlineKeyboardButton("⚙️ Cài đặt", callback_data="admin_settings")],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def button_handler(self, update, context):
        query = update.callback_query
        await query.answer()
        user_id = str(update.effective_user.id)
        if user_id not in ADMIN_IDS:
            return
        data = query.data

        if data == "admin_players":
            players_list = list(db.players.items())[:10]
            if not players_list:
                await query.edit_message_text("Chưa có người chơi.", reply_markup=self.main_menu())
                return
            rows = [[uid, p.get('username','?'), f"{p.get('balance',0):,}đ", f"VIP{p.get('vip_level',0)}"] for uid, p in players_list]
            text = create_table(["ID", "User", "Số dư", "VIP"], rows, "Danh sách người chơi")
            await query.edit_message_text(text, reply_markup=self.main_menu(), parse_mode='Markdown')

        elif data == "admin_pending":
            if not db.pending:
                await query.edit_message_text("✅ Không có giao dịch chờ.", reply_markup=self.main_menu())
                return
            for trans_id, trans in list(db.pending.items())[:5]:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Duyệt", callback_data=f"app_{trans_id}"),
                     InlineKeyboardButton("❌ Từ chối", callback_data=f"rej_{trans_id}")]
                ])
                await context.bot.send_message(chat_id=update.effective_chat.id,
                    text=f"🔑 Mã GD: {trans_id}\n👤 {trans['user_id']}\n💰 {trans['amount']:,}đ", reply_markup=kb)

        elif data.startswith("app_"):
            trans_id = data[4:]
            trans = db.pending.pop(trans_id, None)
            if trans:
                uid = trans['user_id']
                if uid not in db.players:
                    db.players[uid] = {"balance":0,"username":"","total_deposit":0,"daily_bet":0,"vip_level":0}
                db.players[uid]['balance'] = db.players[uid].get('balance', 0) + trans['amount']
                db.players[uid]['total_deposit'] = db.players[uid].get('total_deposit', 0) + trans['amount']
                db.update_vip(uid)
                db.save()
                await query.edit_message_text(f"✅ Đã duyệt {trans['amount']:,}đ cho {uid}")

        elif data.startswith("rej_"):
            trans_id = data[4:]
            db.pending.pop(trans_id, None)
            db.save()
            await query.edit_message_text("❌ Đã từ chối giao dịch.")

        elif data == "admin_giftcode":
            code = f"CAXAU-{random.randint(1000,9999)}"
            db.giftcodes[code] = {"amount":50000, "uses":0, "max_uses":10}
            db.save()
            await query.edit_message_text(f"🎁 Đã tạo giftcode: `{code}` (50k, 10 lượt)", parse_mode='Markdown', reply_markup=self.main_menu())

        elif data == "admin_stats":
            today = datetime.now().strftime("%Y-%m-%d")
            today_bet = sum(p.get('daily_bet',0) for p in db.players.values() if p.get('last_bet_date')==today)
            text = create_table(["Thống kê hôm nay"], [[f"Tổng cược: {today_bet:,}đ"]])
            await query.edit_message_text(text, reply_markup=self.main_menu(), parse_mode='Markdown')

        elif data == "admin_rooms":
            rooms = db.rooms.values()
            rows = [[r['id'], r['name'], len(r['members'])] for r in rooms]
            text = create_table(["ID", "Tên phòng", "Thành viên"], rows, "🐊 Quản lý phòng")
            await query.edit_message_text(text + "\nDùng /createroom [id] [tên] để tạo phòng mới.", reply_markup=self.main_menu(), parse_mode='Markdown')

        elif data == "admin_settings":
            await query.edit_message_text("⚙️ /setmin [số] - Nạp tối thiểu\n/setdaily [số] - Cược/ngày\n/setbonus [số] - Thưởng daily", reply_markup=self.main_menu())

    async def create_room_cmd(self, update, context):
        if str(update.effective_user.id) not in ADMIN_IDS: return
        if len(context.args) < 2:
            await update.message.reply_text("Dùng: /createroom [id] [tên]")
            return
        room_id = context.args[0]
        name = " ".join(context.args[1:])
        ok, msg = RoomManager.create_room(room_id, name, "admin")
        if ok:
            await update.message.reply_text(f"✅ Đã tạo phòng `{room_id}` - {name}")
        else:
            await update.message.reply_text(f"❌ {msg}")

    async def set_min(self, update, context):
        if str(update.effective_user.id) not in ADMIN_IDS: return
        try:
            val = int(context.args[0])
            db.settings['min_deposit'] = val
            db.save()
            await update.message.reply_text(f"✅ Nạp tối thiểu: {val:,}đ")
        except:
            await update.message.reply_text("Dùng: /setmin 50000")

    async def set_daily(self, update, context):
        if str(update.effective_user.id) not in ADMIN_IDS: return
        try:
            val = int(context.args[0])
            db.settings['daily_bet_requirement'] = val
            db.save()
            await update.message.reply_text(f"✅ Yêu cầu cược/ngày: {val:,}đ")
        except:
            await update.message.reply_text("Dùng: /setdaily 50000")

    async def set_bonus(self, update, context):
        if str(update.effective_user.id) not in ADMIN_IDS: return
        try:
            val = int(context.args[0])
            db.settings['daily_bonus'] = val
            db.save()
            await update.message.reply_text(f"✅ Thưởng hàng ngày: {val:,}đ")
        except:
            await update.message.reply_text("Dùng: /setbonus 2000")

    def run(self):
        app = Application.builder().token(ADMIN_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("createroom", self.create_room_cmd))
        app.add_handler(CommandHandler("setmin", self.set_min))
        app.add_handler(CommandHandler("setdaily", self.set_daily))
        app.add_handler(CommandHandler("setbonus", self.set_bonus))
        app.add_handler(CallbackQueryHandler(self.button_handler))
        print("🔵 Admin Bot started")
        app.run_polling()

# ========== BOT ROOM ĐA PHÒNG ==========
class RoomBot:
    def __init__(self):
        self.active_sessions = {}

    async def start(self, update, context):
        user_id = str(update.effective_user.id)
        my_rooms = RoomManager.list_user_rooms(user_id)
        if not my_rooms:
            RoomManager.join_room("main", user_id)
            my_rooms = [db.rooms["main"]]
        room_list = "\n".join([f"🏠 {r['name']} (`{r['id']}`)" for r in my_rooms])
        await update.message.reply_text(
            f"🐊 *CÁ XẤU ROOM*\nPhòng của bạn:\n{room_list}\n\n"
            "Dùng:\n`/rooms` - xem tất cả phòng\n`/join [id]` - tham gia phòng\n`/leave [id]` - rời phòng\n`/play [id]` - chơi trong phòng",
            parse_mode='Markdown'
        )

    async def list_rooms(self, update, context):
        rooms = RoomManager.list_all_rooms()
        if not rooms:
            await update.message.reply_text("Chưa có phòng nào.")
            return
        rows = [[r['id'], r['name'], len(r['members'])] for r in rooms]
        text = create_table(["ID", "Tên phòng", "Thành viên"], rows, "🐊 Danh sách phòng")
        await update.message.reply_text(text, parse_mode='Markdown')

    async def join_room(self, update, context):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text("Dùng: /join [id]")
            return
        room_id = context.args[0]
        ok, msg = RoomManager.join_room(room_id, user_id)
        if ok:
            await update.message.reply_text(f"✅ Đã tham gia phòng {msg}")
        else:
            await update.message.reply_text(f"❌ {msg}")

    async def leave_room(self, update, context):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text("Dùng: /leave [id]")
            return
        room_id = context.args[0]
        ok, msg = RoomManager.leave_room(room_id, user_id)
        if ok:
            await update.message.reply_text(f"✅ Đã rời phòng {msg}")
        else:
            await update.message.reply_text(f"❌ {msg}")

    async def play_room(self, update, context):
        user_id = str(update.effective_user.id)
        if not context.args:
            await update.message.reply_text("Dùng: /play [id]")
            return
        room_id = context.args[0]
        room = RoomManager.get_room(room_id)
        if not room or user_id not in room['members']:
            await update.message.reply_text("Bạn chưa tham gia phòng này.")
            return
        if room_id in self.active_sessions and self.active_sessions[room_id]['status'] == 'running':
            await update.message.reply_text("Phòng này đang có phiên chơi, hãy tham gia bằng cách nhấn nút bên dưới.")
            return

        session_id = f"S{random.randint(1000,9999)}"
        self.active_sessions[room_id] = {
            'session_id': session_id,
            'bets': [],
            'status': 'running',
            'message_id': None,
            'chat_id': update.effective_chat.id
        }
        msg = await update.message.reply_text(
            f"🐊 *{room['name']}* - Phiên #{session_id} (30s)\nCược: TÀI / XỈU",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 TÀI", callback_data=f"r_tai_{room_id}"),
                 InlineKeyboardButton("🎲 XỈU", callback_data=f"r_xiu_{room_id}")]
            ]),
            parse_mode='Markdown'
        )
        self.active_sessions[room_id]['message_id'] = msg.message_id
        context.job_queue.run_once(self.resolve_game, 30, data={'room_id': room_id})

    async def place_bet(self, update, context):
        query = update.callback_query
        await query.answer()
        data = query.data
        if not data.startswith("r_"):
            return
        _, bet_type, room_id = data.split('_')
        session = self.active_sessions.get(room_id)
        if not session or session['status'] != 'running':
            await query.answer("Phiên đã kết thúc hoặc không tồn tại!", show_alert=True)
            return
        user_id = str(update.effective_user.id)
        if any(b['user_id'] == user_id for b in session['bets']):
            await query.answer("Bạn đã cược rồi!", show_alert=True)
            return
        room = db.rooms.get(room_id)
        if not room or user_id not in room['members']:
            await query.answer("Bạn không trong phòng này!", show_alert=True)
            return
        player = db.players.get(user_id)
        bet_amount = room['settings'].get('bet_amount', 10000)
        if not player or player.get('balance', 0) < bet_amount:
            await query.answer(f"Không đủ tiền (cần {bet_amount:,}đ)!", show_alert=True)
            return
        player['balance'] -= bet_amount
        player['daily_bet'] = player.get('daily_bet', 0) + bet_amount
        player['last_bet_date'] = datetime.now().strftime("%Y-%m-%d")
        session['bets'].append({'user_id': user_id, 'type': bet_type, 'amount': bet_amount})
        db.save()
        await query.answer(f"Đã cược {bet_type.upper()} {bet_amount:,}đ")
        bet_list = "\n".join([f"@{b['user_id']}: {b['type'].upper()}" for b in session['bets']])
        try:
            await query.edit_message_text(
                f"🐊 {room['name']} - Phiên #{session['session_id']}\nNgười chơi đã cược:\n{bet_list}",
                reply_markup=query.message.reply_markup
            )
        except:
            pass

    async def resolve_game(self, context):
        job_data = context.job.data
        room_id = job_data['room_id']
        session = self.active_sessions.pop(room_id, None)
        if not session:
            return
        dice = [random.randint(1,6) for _ in range(3)]
        total = sum(dice)
        is_tai = total >= 11
        dice_display = " ".join(['⚀⚁⚂⚃⚄⚅'[d-1] for d in dice])
        result_text = f"🎲 {dice_display} = {total} → {'TÀI' if is_tai else 'XỈU'}\n"
        for bet in session['bets']:
            uid = bet['user_id']
            win = (bet['type'] == 'tai' and is_tai) or (bet['type'] == 'xiu' and not is_tai)
            if uid in db.players:
                if win:
                    db.players[uid]['balance'] += bet['amount'] * 2
                    result_text += f"✅ @{uid}: +{bet['amount']*2:,}đ\n"
                else:
                    result_text += f"❌ @{uid}: -{bet['amount']:,}đ\n"
        db.save()
        try:
            await context.bot.edit_message_text(
                chat_id=session['chat_id'],
                message_id=session['message_id'],
                text=result_text
            )
        except:
            pass

    def run(self):
        app = Application.builder().token(ROOM_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("rooms", self.list_rooms))
        app.add_handler(CommandHandler("join", self.join_room))
        app.add_handler(CommandHandler("leave", self.leave_room))
        app.add_handler(CommandHandler("play", self.play_room))
        app.add_handler(CallbackQueryHandler(self.place_bet))
        print("🟢 Room Bot (multi-room) started")
        app.run_polling()

# ========== BOT PROFILE ==========
class ProfileBot:
    async def start(self, update, context):
        user_id = str(update.effective_user.id)
        if user_id not in db.players:
            db.players[user_id] = {
                "balance": 10000,
                "username": update.effective_user.username or "unknown",
                "total_deposit": 0,
                "daily_bet": 0,
                "vip_level": 0
            }
            db.save()
        player = db.players[user_id]
        await update.message.reply_text(
            f"🐊 *CÁ XẤU ROOM - Profile*\n💰 Số dư: {player['balance']:,}đ\n"
            "`/tx 10000 T` - Cược Tài\n`/tx 10000 X` - Cược Xỉu\n"
            "`/nap` - Nạp tiền\n`/daily` - Nhận thưởng\n`/code MÃ` - Nhập giftcode",
            parse_mode='Markdown'
        )

    async def tx(self, update, context):
        user_id = str(update.effective_user.id)
        parts = update.message.text.split()
        if len(parts) < 3: return
        try:
            amount = int(parts[1])
        except: return
        choice = parts[2].upper()
        if choice not in ['T', 'X']: return
        player = db.players.get(user_id)
        if not player or player['balance'] < amount:
            await update.message.reply_text("Không đủ tiền."); return
        player['balance'] -= amount
        player['daily_bet'] = player.get('daily_bet',0) + amount
        player['last_bet_date'] = datetime.now().strftime("%Y-%m-%d")
        total = sum(random.randint(1,6) for _ in range(3))
        is_tai = total >= 11
        win = (choice=='T' and is_tai) or (choice=='X' and not is_tai)
        if win:
            player['balance'] += amount*2
            msg = f"🎲 {total} → Thắng +{amount*2:,}đ"
        else:
            msg = f"🎲 {total} → Thua -{amount:,}đ"
        db.save()
        await update.message.reply_text(msg + f"\n💰 Số dư: {player['balance']:,}đ")

    async def nap(self, update, context):
        user_id = str(update.effective_user.id)
        trans_id = f"NAP{random.randint(100000,999999)}"
        db.pending[trans_id] = {"user_id": user_id, "amount": 100000, "time": datetime.now().isoformat()}
        db.save()
        await update.message.reply_text(f"📤 Yêu cầu nạp 100k, mã `{trans_id}`. Admin sẽ duyệt.", parse_mode='Markdown')

    async def daily(self, update, context):
        user_id = str(update.effective_user.id)
        player = db.players.get(user_id)
        if not player: return
        today = datetime.now().strftime("%Y-%m-%d")
        if player.get('last_daily') == today:
            await update.message.reply_text("Hôm nay bạn đã nhận thưởng rồi.")
            return
        bonus = db.settings.get('daily_bonus', 1000)
        player['balance'] += bonus
        player['last_daily'] = today
        db.save()
        await update.message.reply_text(f"🎁 Nhận {bonus:,}đ. Số dư: {player['balance']:,}đ")

    async def code(self, update, context):
        user_id = str(update.effective_user.id)
        if not context.args: return
        code = context.args[0].upper()
        gift = db.giftcodes.get(code)
        if not gift:
            await update.message.reply_text("Mã không tồn tại."); return
        if gift['uses'] >= gift['max_uses']:
            await update.message.reply_text("Mã hết lượt."); return
        if user_id in gift.get('used_by', []):
            await update.message.reply_text("Bạn đã dùng mã này."); return
        player = db.players.get(user_id)
        if not player: return
        player['balance'] += gift['amount']
        gift['uses'] += 1
        gift.setdefault('used_by', []).append(user_id)
        db.save()
        await update.message.reply_text(f"🎁 Nhận {gift['amount']:,}đ. Số dư: {player['balance']:,}đ")

    def run(self):
        app = Application.builder().token(PROFILE_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("tx", self.tx))
        app.add_handler(CommandHandler("nap", self.nap))
        app.add_handler(CommandHandler("daily", self.daily))
        app.add_handler(CommandHandler("code", self.code))
        print("🟣 Profile Bot started")
        app.run_polling()

# ========== KHỞI ĐỘNG ==========
if __name__ == "__main__":
    print("🐊 CÁ XẤU ROOM - KHỞI ĐỘNG 3 BOT")
    bots = [AdminBot(), RoomBot(), ProfileBot()]
    threads = []
    for bot in bots:
        t = threading.Thread(target=bot.run, daemon=True)
        t.start()
        threads.append(t)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Đã dừng tất cả bot.")
