# 🐊 Cá Xấu Room – Hệ thống Bot Telegram Đa Phòng

**Cá Xấu Room** là hệ thống bot Telegram gồm 3 bot hoạt động song song: **Admin**, **Room** (đa phòng), và **Profile** (chơi ẩn danh). Hỗ trợ quản lý người chơi, nạp/rút, tạo phòng chơi theo nhóm, thưởng VIP, giftcode, thống kê…

---

## 🚀 Tính năng chính

### 🛡️ Admin Bot
- Dashboard tổng quan
- Duyệt / từ chối giao dịch nạp tiền
- Xem danh sách người chơi, thống kê cược ngày
- Tạo giftcode, quản lý phòng (tạo phòng mới)
- Cài đặt giới hạn nạp, yêu cầu cược, thưởng hàng ngày
- Tự động nâng cấp VIP khi tổng nạp đạt mốc

### 🏠 Room Bot (đa phòng)
- Tự động tham gia phòng chính (`main`)
- Xem tất cả phòng (`/rooms`)
- Tham gia (`/join`) và rời phòng (`/leave`)
- Bắt đầu phiên chơi 30 giây trong một phòng (`/play <id>`)
- Cược TÀI / XỈU qua nút bấm, hiển thị danh sách người đã cược
- Mỗi phòng có mức cược riêng (cấu hình `bet_amount`)

### 👤 Profile Bot
- Chơi Tài Xỉu ẩn danh với lệnh `/tx <tiền> T` hoặc `X`
- Nạp tiền bằng lệnh `/nap`, tạo yêu cầu chờ Admin duyệt
- Nhận thưởng hàng ngày `/daily`
- Nhập giftcode `/code <mã>`

---

## 📋 Yêu cầu

- Python **3.7 trở lên**
- Tài khoản Telegram và 3 bot được tạo qua [@BotFather](https://t.me/BotFather)
- Dịch vụ cloud miễn phí [Render](https://render.com) (hoặc VPS riêng)

---

## 📦 Cài đặt & Triển khai

### 1. Tạo 3 bot Telegram
- Chat với [@BotFather](https://t.me/BotFather), gửi `/newbot` để tạo 3 bot:
  - Admin bot (tên bất kỳ, username dạng `xxxBot`)
  - Room bot
  - Profile bot
- Lưu **token** của mỗi bot (dạng `123456:ABC...`)

### 2. Lấy Admin ID
- Chat với [@userinfobot](https://t.me/userinfobot), gửi `/start` để lấy `Id` của bạn.

### 3. Đưa code lên GitHub
- Tạo repository mới trên GitHub (ví dụ: `caxau-room`).
- Tạo file `bot.py`, dán toàn bộ code.
- **Sửa 4 dòng**:
  ```python
  ADMIN_TOKEN = "token_admin"
  ROOM_TOKEN = "token_room"
  PROFILE_TOKEN = "token_profile"
  ADMIN_IDS = ["id_cua_ban"]
