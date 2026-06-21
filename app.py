import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from flask import Flask, request
import threading
import os

# ===== ТОКЕН =====
BOT_TOKEN = "8928296223:AAGldeC6kqg9ndpOeocTm6C1IURUCZTRR4s"
ADMINS = [5461117804]  # Список админов

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище данных
users = set()
history = {}
reply_mode = None
dnd_mode = False
pending_messages = []

# Flask для веб-сервера
app = Flask(__name__)

# ==========================================
# ПРОВЕРКА АДМИНА
# ==========================================
def is_admin(user_id):
    return user_id in ADMINS

# ==========================================
# 1. КОМАНДА /start
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if is_admin(message.from_user.id):
        status = "🔕 ВКЛ" if dnd_mode else "🔔 ВЫКЛ"
        
        await message.answer(
            f"🚀 **ЦЕНТР ПОДДЕРЖКИ**\n\n"
            f"📊 DND: {status}\n"
            f"👥 Админов: {len(ADMINS)}\n"
            f"📬 Накоплено: {len(pending_messages)}\n\n"
            f"📋 /chats - список чатов\n"
            f"🔇 /dnd - режим 'Не беспокоить'\n"
            f"📬 /check - накопленные сообщения\n"
            f"➕ /addadmin ID - добавить админа\n"
            f"➖ /deladmin ID - удалить админа\n"
            f"❌ /cancel - отменить ответ\n"
            f"🗑 /clear - очистить всё"
        )
    else:
        await message.answer("👋 Напишите вопрос, мы ответим!")

# ==========================================
# 2. ДОБАВИТЬ АДМИНА
# ==========================================
@dp.message(Command("addadmin"))
async def add_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа!")
        return
    
    try:
        new_id = int(message.text.split()[1])
        if new_id not in ADMINS:
            ADMINS.append(new_id)
            await message.answer(f"✅ Админ {new_id} добавлен!")
        else:
            await message.answer(f"⚠️ {new_id} уже админ")
    except:
        await message.answer("❌ Используй: `/addadmin 123456789`")

# ==========================================
# 3. УДАЛИТЬ АДМИНА
# ==========================================
@dp.message(Command("deladmin"))
async def del_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа!")
        return
    
    try:
        del_id = int(message.text.split()[1])
        if len(ADMINS) <= 1:
            await message.answer("⚠️ Нельзя удалить единственного админа!")
            return
        if del_id in ADMINS:
            ADMINS.remove(del_id)
            await message.answer(f"✅ Админ {del_id} удален!")
        else:
            await message.answer(f"⚠️ {del_id} не админ")
    except:
        await message.answer("❌ Используй: `/deladmin 123456789`")

# ==========================================
# 4. DND
# ==========================================
@dp.message(Command("dnd"))
async def toggle_dnd(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    global dnd_mode
    dnd_mode = not dnd_mode
    
    if dnd_mode:
        await message.answer("🔕 **DND ВКЛЮЧЕН**\nСообщения копятся, проверяй /check")
    else:
        await message.answer(f"🔔 **DND ВЫКЛЮЧЕН**\nНакоплено: {len(pending_messages)}")

# ==========================================
# 5. CHECK
# ==========================================
@dp.message(Command("check"))
async def check_messages(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    if not pending_messages:
        await message.answer("📭 Нет накопленных сообщений")
        return
    
    text = f"📬 **Накоплено:** {len(pending_messages)}\n\n"
    for i, (user_id, msg_text, name, time) in enumerate(pending_messages[:10], 1):
        text += f"{i}. {name}: {msg_text[:30]}\n   ID: `{user_id}` | {time}\n\n"
    
    if len(pending_messages) > 10:
        text += f"... и еще {len(pending_messages) - 10}"
    
    await message.answer(text, parse_mode="Markdown")

# ==========================================
# 6. ОБРАБОТКА СООБЩЕНИЙ
# ==========================================
@dp.message()
async def handle_message(message: types.Message):
    global reply_mode, pending_messages
    
    user_id = message.from_user.id
    
    # === АДМИН ===
    if is_admin(user_id):
        if reply_mode:
            try:
                await bot.send_message(
                    reply_mode,
                    f"📩 **Ответ поддержки:**\n\n{message.text}"
                )
                await message.answer(f"✅ Ответ отправлен {reply_mode}")
                reply_mode = None
            except Exception as e:
                await message.answer(f"❌ Ошибка: {e}")
                reply_mode = None
        return
    
    # === ПОЛЬЗОВАТЕЛЬ ===
    users.add(user_id)
    
    if user_id not in history:
        history[user_id] = []
    history[user_id].append({
        'from': 'user',
        'text': message.text,
        'time': datetime.now().strftime("%H:%M")
    })
    
    name = message.from_user.full_name
    time_now = datetime.now().strftime("%H:%M:%S")
    
    # DND режим
    if dnd_mode:
        pending_messages.append((user_id, message.text, name, time_now))
        await message.answer("✅ Получено! Ответим скоро.")
        return
    
    # Отправляем всем админам
    for admin_id in ADMINS:
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{user_id}")],
                [InlineKeyboardButton(text="📋 История", callback_data=f"history_{user_id}")]
            ])
            
            await bot.send_message(
                admin_id,
                f"📩 **НОВОЕ СООБЩЕНИЕ**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 {name}\n"
                f"🆔 ID: `{user_id}`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💬 {message.text}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏰ {time_now}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer("✅ Получено! Ответим скоро.")

# ==========================================
# 7. /chats
# ==========================================
@dp.message(Command("chats"))
async def cmd_chats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа!")
        return
    
    if not users:
        await message.answer("📭 Нет активных чатов")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for user_id in users:
        try:
            user = await bot.get_chat(user_id)
            name = user.full_name[:20]
            last_msg = history.get(user_id, [])
            last_text = last_msg[-1]['text'][:15] if last_msg else "..."
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"💬 {name} | {last_text}",
                    callback_data=f"chat_{user_id}"
                )
            ])
        except:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"💬 ID:{user_id}",
                    callback_data=f"chat_{user_id}"
                )
            ])
    
    if pending_messages:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📬 Накопленные ({len(pending_messages)})", 
                callback_data="show_pending"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")
    ])
    
    await message.answer(
        f"📋 **Активные чаты** ({len(users)})\n\n"
        f"Статус DND: {'🔕 ВКЛ' if dnd_mode else '🔔 ВЫКЛ'}\n"
        f"Накоплено: {len(pending_messages)}\n"
        f"Админов: {len(ADMINS)}",
        reply_markup=keyboard
    )

# ==========================================
# 8. ПОКАЗАТЬ НАКОПЛЕННЫЕ (КНОПКА)
# ==========================================
@dp.callback_query(lambda c: c.data == "show_pending")
async def show_pending(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    if not pending_messages:
        await callback.answer("Нет накопленных", show_alert=True)
        return
    
    text = f"📬 **Накопленные** ({len(pending_messages)})\n\n"
    for i, (user_id, msg_text, name, time) in enumerate(pending_messages, 1):
        text += f"{i}. {name} | {time}\n   💬 {msg_text}\n   🆔 `{user_id}`\n\n"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

# ==========================================
# 9. ОТКРЫТЬ ЧАТ
# ==========================================
@dp.callback_query(lambda c: c.data.startswith("chat_"))
async def open_chat(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    await show_dialog(callback.message, user_id)
    await callback.answer()

# ==========================================
# 10. ПОКАЗАТЬ ДИАЛОГ
# ==========================================
async def show_dialog(message, user_id):
    try:
        user = await bot.get_chat(user_id)
        name = user.full_name
    except:
        name = f"Пользователь {user_id}"
    
    msgs = history.get(user_id, [])
    
    dialog_text = f"💬 **Чат с {name}**\n"
    dialog_text += f"🆔 ID: `{user_id}`\n"
    dialog_text += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if not msgs:
        dialog_text += "📭 История пуста\n"
    else:
        for msg in msgs[-10:]:
            icon = "👤" if msg['from'] == 'user' else "🤖"
            dialog_text += f"{icon} [{msg['time']}] {msg['text']}\n"
    
    dialog_text += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
    dialog_text += f"📊 Всего: {len(msgs)} сообщений"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Ответить", callback_data=f"reply_{user_id}")],
        [InlineKeyboardButton(text="📜 Вся история", callback_data=f"history_{user_id}")],
        [InlineKeyboardButton(text="❌ Закрыть чат", callback_data=f"close_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    
    await message.edit_text(dialog_text, reply_markup=keyboard, parse_mode="Markdown")

# ==========================================
# 11. ОТВЕТИТЬ (КНОПКА)
# ==========================================
@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def reply_to_user(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    global reply_mode, pending_messages
    user_id = int(callback.data.split("_")[1])
    reply_mode = user_id
    pending_messages = [p for p in pending_messages if p[0] != user_id]
    
    await callback.message.edit_text(
        f"✍️ **Режим ответа**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Пользователь: `{user_id}`\n\n"
        f"Напишите сообщение для отправки.\n"
        f"❌ Отмена: /cancel",
        parse_mode="Markdown"
    )
    await callback.answer("✅ Напишите ответ!")

# ==========================================
# 12. ИСТОРИЯ (КНОПКА)
# ==========================================
@dp.callback_query(lambda c: c.data.startswith("history_"))
async def show_full_history(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    msgs = history.get(user_id, [])
    
    if not msgs:
        await callback.answer("История пуста", show_alert=True)
        return
    
    text = f"📜 **Вся история**\n━━━━━━━━━━━━\n\n"
    for msg in msgs:
        icon = "👤" if msg['from'] == 'user' else "🤖"
        text += f"{icon} [{msg['time']}] {msg['text']}\n"
    
    await callback.message.edit_text(text)
    await callback.answer()

# ==========================================
# 13. ОСТАЛЬНЫЕ КНОПКИ
# ==========================================
@dp.callback_query(lambda c: c.data == "refresh")
async def refresh(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await cmd_chats(callback.message)
    await callback.answer("🔄 Обновлено!")

@dp.callback_query(lambda c: c.data == "back")
async def back_to_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    await cmd_chats(callback.message)

@dp.callback_query(lambda c: c.data.startswith("close_"))
async def close_chat(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    users.discard(user_id)
    
    await callback.answer("✅ Чат закрыт", show_alert=True)
    await callback.message.delete()
    await cmd_chats(callback.message)

# ==========================================
# 14. ОТМЕНА
# ==========================================
@dp.message(Command("cancel"))
async def cancel_reply(message: types.Message):
    global reply_mode
    if is_admin(message.from_user.id):
        reply_mode = None
        await message.answer("❌ Отменено")

# ==========================================
# 15. ОЧИСТИТЬ ВСЁ
# ==========================================
@dp.message(Command("clear"))
async def clear_all(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    global pending_messages
    users.clear()
    history.clear()
    pending_messages = []
    await message.answer("🗑 Все очищено")

# ==========================================
# 16. ВЕБ-СЕРВЕР ДЛЯ RENDER
# ==========================================
@app.route('/')
def home():
    return "🤖 Бот работает!", 200

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/health')
def health():
    return {"status": "ok", "users": len(users), "admins": len(ADMINS)}, 200

# ==========================================
# 17. ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ
# ==========================================
def run_bot():
    asyncio.run(main())

async def main():
    print("=" * 50)
    print("🤖 БОТ ПОДДЕРЖКИ (ПОЛНАЯ ВЕРСИЯ)")
    print(f"👥 Админы: {ADMINS}")
    print("📋 Команды:")
    print("   /start - главное меню")
    print("   /chats - список чатов")
    print("   /dnd - режим 'Не беспокоить'")
    print("   /check - накопленные сообщения")
    print("   /addadmin ID - добавить админа")
    print("   /deladmin ID - удалить админа")
    print("   /cancel - отменить ответ")
    print("   /clear - очистить всё")
    print("=" * 50)
    
    # Удаляем вебхук и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)

# ==========================================
# 18. ОСНОВНОЙ ЗАПУСК
# ==========================================
if __name__ == "__main__":
    # Запускаем Flask веб-сервер в отдельном потоке
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем веб-сервер
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
