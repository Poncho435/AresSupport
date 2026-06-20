import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

# ===== ТОКЕН =====
BOT_TOKEN = "8928296223:AAGldeC6kqg9ndpOeocTm6C1IURUCZTRR4s"
# ===== АДМИНИСТРАТОРЫ (список ID) =====
ADMINS = [5461117804]  # Ваш ID
# =======================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище данных
users = set()
history = {}
reply_mode = None
dnd_mode = False
pending_messages = []

# ==========================================
# ФУНКЦИЯ ПРОВЕРКИ АДМИНА
# ==========================================
def is_admin(user_id):
    return user_id in ADMINS

# ==========================================
# 1. КОМАНДА /start
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if is_admin(message.from_user.id):
        status = "🔕 ВКЛЮЧЕН" if dnd_mode else "🔔 ВЫКЛЮЧЕН"
        
        await message.answer(
            f"🚀 **ЦЕНТР ПОДДЕРЖКИ**\n\n"
            f"📊 Статус: {status}\n\n"
            f"📋 /chats - список активных чатов\n"
            f"🔇 /dnd - включить/выключить 'Не беспокоить'\n"
            f"📬 /check - проверить новые сообщения\n"
            f"❌ /cancel - отменить ответ\n"
            f"🗑 /clear - очистить историю\n"
            f"👥 /addadmin ID - добавить администратора\n"
            f"👥 /deladmin ID - удалить администратора\n\n"
            f"💡 В режиме 'Не беспокоить' сообщения копятся"
        )
    else:
        await message.answer(
            "👋 **Добро пожаловать в поддержку!**\n\n"
            "Напишите ваш вопрос, и мы свяжемся с вами в ближайшее время."
        )

# ==========================================
# 2. ДОБАВИТЬ АДМИНИСТРАТОРА
# ==========================================
@dp.message(Command("addadmin"))
async def add_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    
    try:
        new_admin = int(message.text.split()[1])
        if new_admin not in ADMINS:
            ADMINS.append(new_admin)
            await message.answer(f"✅ Администратор {new_admin} добавлен!")
        else:
            await message.answer(f"⚠️ {new_admin} уже в списке")
    except:
        await message.answer("❌ Используйте: `/addadmin 123456789`", parse_mode="Markdown")

# ==========================================
# 3. УДАЛИТЬ АДМИНИСТРАТОРА
# ==========================================
@dp.message(Command("deladmin"))
async def del_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    
    try:
        del_admin_id = int(message.text.split()[1])
        if del_admin_id in ADMINS and del_admin_id != 5461117804:
            ADMINS.remove(del_admin_id)
            await message.answer(f"✅ Администратор {del_admin_id} удален!")
        else:
            await message.answer(f"⚠️ Нельзя удалить главного админа или такого ID нет")
    except:
        await message.answer("❌ Используйте: `/deladmin 123456789`", parse_mode="Markdown")

# ==========================================
# 4. ВКЛЮЧЕНИЕ/ВЫКЛЮЧЕНИЕ DND
# ==========================================
@dp.message(Command("dnd"))
async def toggle_dnd(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    global dnd_mode
    dnd_mode = not dnd_mode
    
    if dnd_mode:
        await message.answer(
            "🔕 **Режим 'Не беспокоить' ВКЛЮЧЕН**\n\n"
            "✅ Сообщения от пользователей будут накапливаться\n"
            "📬 Для проверки используйте /check"
        )
    else:
        count = len(pending_messages)
        await message.answer(
            f"🔔 **Режим 'Не беспокоить' ВЫКЛЮЧЕН**\n\n"
            f"📬 Накоплено сообщений: {count}"
        )

# ==========================================
# 5. ПРОВЕРКА НАКОПЛЕННЫХ
# ==========================================
@dp.message(Command("check"))
async def check_messages(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    global pending_messages
    
    if not pending_messages:
        await message.answer("📭 **Нет новых сообщений**")
        return
    
    count = len(pending_messages)
    text = f"📬 **Накопленные сообщения** ({count})\n\n"
    
    for i, (user_id, msg_text, name, time) in enumerate(pending_messages[:10], 1):
        text += f"{i}. 👤 {name[:20]} | {msg_text[:30]}\n"
        text += f"   🆔 `{user_id}` | ⏰ {time}\n\n"
    
    if count > 10:
        text += f"... и еще {count - 10} сообщений\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметить все как прочитанные", callback_data="check_clear")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

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
                if reply_mode not in history:
                    history[reply_mode] = []
                history[reply_mode].append({
                    'from': 'admin',
                    'text': message.text or '📎 Файл',
                    'time': datetime.now().strftime("%H:%M")
                })
                
                await bot.send_message(
                    reply_mode,
                    f"📩 **Ответ поддержки:**\n\n{message.text}"
                )
                
                await show_dialog(message, reply_mode)
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
        'text': message.text or '📎 Файл',
        'time': datetime.now().strftime("%H:%M")
    })
    
    name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else ""
    time_now = datetime.now().strftime("%H:%M:%S")
    
    if dnd_mode:
        pending_messages.append((user_id, message.text or '📎 Файл', name, time_now))
        await message.answer("✅ **Сообщение получено!** Ответим скоро.")
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
                f"👤 {name} {username}\n"
                f"🆔 ID: `{user_id}`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💬 {message.text or '📎 Файл'}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏰ {time_now}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer(
        "✅ **Сообщение получено!**\n\n"
        "Наши операторы уже уведомлены. Мы ответим вам в ближайшее время."
    )

# ==========================================
# 7. КОМАНДА /chats
# ==========================================
@dp.message(Command("chats"))
async def cmd_chats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    
    if not users:
        await message.answer("📭 **Нет активных чатов**")
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
# 8. ПОКАЗАТЬ НАКОПЛЕННЫЕ
# ==========================================
@dp.callback_query(lambda c: c.data == "show_pending")
async def show_pending(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    if not pending_messages:
        await callback.answer("Нет накопленных сообщений", show_alert=True)
        return
    
    text = f"📬 **Накопленные сообщения** ({len(pending_messages)})\n\n"
    
    for i, (user_id, msg_text, name, time) in enumerate(pending_messages, 1):
        text += f"{i}. 👤 {name} | ⏰ {time}\n"
        text += f"   💬 {msg_text}\n"
        text += f"   🆔 `{user_id}`\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметить все как прочитанные", callback_data="check_clear")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# ==========================================
# 9. ОЧИСТИТЬ НАКОПЛЕННЫЕ
# ==========================================
@dp.callback_query(lambda c: c.data == "check_clear")
async def clear_pending(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    global pending_messages
    count = len(pending_messages)
    pending_messages = []
    
    await callback.answer(f"✅ Очищено {count} сообщений", show_alert=True)
    await cmd_chats(callback.message)

# ==========================================
# 10. ОТКРЫТЬ ДИАЛОГ
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
# 11. ПОКАЗАТЬ ДИАЛОГ
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
    dialog_text += f"📊 Всего сообщений: {len(msgs)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Ответить", callback_data=f"reply_{user_id}")],
        [InlineKeyboardButton(text="📜 Вся история", callback_data=f"history_{user_id}")],
        [InlineKeyboardButton(text="❌ Закрыть чат", callback_data=f"close_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back")]
    ])
    
    await message.edit_text(dialog_text, reply_markup=keyboard, parse_mode="Markdown")

# ==========================================
# 12. ОТВЕТИТЬ
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
# 13. ВСЯ ИСТОРИЯ
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
    
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (длинная история)"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"chat_{user_id}")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# ==========================================
# 14. ОСТАЛЬНЫЕ КОЛБЭКИ
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
# 15. ОТМЕНА
# ==========================================
@dp.message(Command("cancel"))
async def cancel_reply(message: types.Message):
    global reply_mode
    if is_admin(message.from_user.id):
        reply_mode = None
        await message.answer("❌ **Режим ответа отменен**")

# ==========================================
# 16. ОЧИСТИТЬ ВСЁ
# ==========================================
@dp.message(Command("clear"))
async def clear_all(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    global pending_messages
    users.clear()
    history.clear()
    pending_messages = []
    
    await message.answer("🗑 **Все данные очищены**")

# ==========================================
# 17. ЗАПУСК
# ==========================================
async def main():
    print("=" * 50)
    print("🔕 БОТ ПОДДЕРЖКИ")
    print(f"👤 Ваш ID: {ADMINS[0]}")
    print(f"👥 Всего админов: {len(ADMINS)}")
    print("📋 Команды:")
    print("   /start - главное меню")
    print("   /chats - список активных чатов")
    print("   /dnd - включить/выключить 'Не беспокоить'")
    print("   /check - проверить накопленные сообщения")
    print("   /addadmin ID - добавить администратора")
    print("   /deladmin ID - удалить администратора")
    print("   /cancel - отменить ответ")
    print("   /clear - очистить всё")
    print("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
