import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
from dotenv import load_dotenv
import telegram

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Categories
CATEGORIES = ["Бытовая техника", "Мебель", "Одежда", "Другое"]


# Ensure directories exist for each category
for category in CATEGORIES:
    os.makedirs(category, exist_ok=True)

# Define persistent keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🛒 Купить товары"), KeyboardButton("➕ Продать товар")],
        [KeyboardButton("📦 Мои товары"), KeyboardButton("🛍 Купленные товары")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("❓ Помощь")]
    ],
    resize_keyboard=True
)

# Utility functions
def load_user_data(user_id):
    try:
        with open(f"user_data_{user_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_user_data(user_id, data):
    with open(f"user_data_{user_id}.json", "w") as f:
        json.dump(data, f)

def remove_expired_items():
    current_time = datetime.now()
    for user_file in os.listdir("."):
        if user_file.startswith("user_data_") and user_file.endswith(".json"):
            user_id = user_file.split("_")[2].split(".")[0]
            user_items = load_user_data(user_id)
            user_items = [
                item for item in user_items
                if datetime.strptime(item['created_at'], '%Y-%m-%d') >= current_time - timedelta(days=30)
            ]
            save_user_data(user_id, user_items)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать на рынок! Пожалуйста, используйте меню ниже для навигации:",
        reply_markup=MAIN_KEYBOARD
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Доступные команды:
/start - Открыть главное меню
/help - Показать это сообщение помощи

Вы также можете использовать постоянные кнопки меню ниже для навигации.
"""
    await update.message.reply_text(help_text, reply_markup=MAIN_KEYBOARD)

# Utility function to clear user state
def clear_user_state(context):
    if 'add_product_step' in context.user_data:
        del context.user_data['add_product_step']
    if 'current_product' in context.user_data:
        del context.user_data['current_product']

async def handle_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clear user state at the start of every new command
    clear_user_state(context)
    text = update.message.text

    command_map = {
        "🛒 Купить товары": handle_buy,
        "➕ Продать товар": handle_sell_start,
        "📦 Мои товары": handle_my_items_text,
        "🛍 Купленные товары": handle_purchased_items_text,
        "👤 Профиль": handle_profile_text,
        "❓ Помощь": help_command
    }

    handler = command_map.get(text)
    if handler:
        await handler(update, context)
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки меню для навигации.",
            reply_markup=MAIN_KEYBOARD
        )

# Start the "Sell Item" process and set up context only when selected
async def handle_sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Initialize the "Sell Item" process steps
    context.user_data['add_product_step'] = 'choose_category'
    context.user_data['current_product'] = {}

    keyboard = [
        [InlineKeyboardButton(category, callback_data=f'sell_category_{category}')]
        for category in CATEGORIES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        "Давайте добавим ваш товар!\n\n"
        "1️⃣ Выберите категорию\n"
        "2️⃣ Введите название\n"
        "3️⃣ Установите цену\n"
        "4️⃣ Введите контактный номер\n"
        "5️⃣ Загрузите фото\n\n"
        "Пожалуйста, выберите категорию:"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup
        )

import re

async def handle_product_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'add_product_step' not in context.user_data or context.user_data['add_product_step'] != 'ask_contact':
        await update.message.reply_text(
            "Пожалуйста, начните процесс продажи с помощью меню.",
            reply_markup=MAIN_KEYBOARD
        )
        return

    contact_number = update.message.text

    # Validate the contact number: only digits, between 8 and 15 characters
    if not re.fullmatch(r'\d{8,15}', contact_number):
        await update.message.reply_text(
            "Пожалуйста, введите корректный контактный номер (8–15 цифр)."
        )
        return

    # Save the validated contact number and proceed to the next step
    context.user_data['current_product']['contact_number'] = contact_number
    context.user_data['add_product_step'] = 'ask_photo'  # Move to the next step
    await update.message.reply_text(
        "Отлично! Теперь, пожалуйста, отправьте фото вашего товара."
    )

# Buy flow function
async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(category, callback_data=f'category_{category}')]
        for category in CATEGORIES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if callback_query and message exist and have text
    if update.callback_query and update.callback_query.message and update.callback_query.message.text:
        # Edit the existing message text if it contains text
        await update.callback_query.edit_message_text(
            "Выберите категорию для просмотра:",
            reply_markup=reply_markup
        )
    else:
        # Send a new message if there is no text to edit or callback_query is None
        await update.effective_chat.send_message(
            "Выберите категорию для просмотра:",
            reply_markup=reply_markup
        )

async def show_items_in_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    category = query.data.split('_')[1]
    items_to_display = []
    
    for user_file in os.listdir("."):
        if user_file.startswith("user_data_") and user_file.endswith(".json"):
            user_id = user_file.split("_")[2].split(".")[0]
            user_items = load_user_data(user_id)
            items_to_display.extend([item for item in user_items if item['category'] == category])

    if not items_to_display:
        await query.edit_message_text(
            f"Товары в категории {category} не найдены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад к категориям", callback_data='back_to_categories')
            ]])
        )
        return

    await query.edit_message_text(f"Загрузка товаров в категории {category}...")
    
    for index, item in enumerate(items_to_display):
        text = f"*{item['name']}*\nЦена: {item['price']} ₽\nКонтакт: {item.get('contact_number', 'Не указан')}"
        keyboard = [[
            InlineKeyboardButton("🛒 Купить сейчас", callback_data=f"confirm_buy_{index}_{category}"),
            InlineKeyboardButton("◀️ Назад", callback_data='buy')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        photo_path = item.get("photo")
        if photo_path and os.path.exists(photo_path):
            await query.message.reply_photo(
                photo=open(photo_path, 'rb'),
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text(
                text + "\n\n(Фото не доступно)",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

async def handle_sell_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    category = query.data.split('_')[2]
    context.user_data['current_product'] = {'category': category}
    context.user_data['add_product_step'] = 'ask_name'
    await query.edit_message_text(
        "Отлично! Теперь, пожалуйста, введите название вашего товара."
    )

async def handle_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'add_product_step' not in context.user_data:
        await update.message.reply_text(
            "Пожалуйста, начните процесс продажи с помощью меню.",
            reply_markup=MAIN_KEYBOARD
        )
        return

    context.user_data['current_product']['name'] = update.message.text
    context.user_data['add_product_step'] = 'ask_price'
    await update.message.reply_text(
        "Пожалуйста, введите цену в рублях (только цифры):"
    )

async def handle_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text)
        context.user_data['current_product']['price'] = price
        context.user_data['add_product_step'] = 'ask_contact'  # Set the next step to ask for contact number
        await update.message.reply_text(
            "Пожалуйста, введите ваш контактный номер, чтобы покупатели могли связаться с вами."
        )
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите корректную цену (только цифры)."
        )

from telegram import InputFile

async def handle_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'add_product_step' not in context.user_data or context.user_data['add_product_step'] != 'ask_photo':
        await update.message.reply_text(
            "Пожалуйста, начните процесс продажи с помощью меню.",
            reply_markup=MAIN_KEYBOARD
        )
        return

    # Check if the message contains a photo
    if update.message.photo:
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()

        # Set up the photo storage path and save the photo
        user_id = update.message.from_user.id
        category = context.user_data['current_product']['category']
        photo_dir = f"{category}/{user_id}"
        os.makedirs(photo_dir, exist_ok=True)
        photo_path = f"{photo_dir}/{uuid.uuid4().hex}.jpg"

        # Download and save the photo
        await photo_file.download_to_drive(photo_path)

        # Save item data with the photo path
        context.user_data['current_product'].update({
            'photo': photo_path,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        })
        
        # Store item data in user’s file
        user_items = load_user_data(user_id)
        user_items.append(context.user_data['current_product'])
        save_user_data(user_id, user_items)
        
        # Clear context and confirm
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Ваш товар успешно добавлен!",
            reply_markup=MAIN_KEYBOARD
        )
    elif update.message.video or update.message.document:
        # Handle unsupported file types
        await update.message.reply_text(
            "Неподдерживаемый тип файла. Пожалуйста, загрузите фото (JPEG или PNG)."
        )
    else:
        # In case no file or unsupported file type is sent
        await update.message.reply_text(
            "Пожалуйста, загрузите фото для добавления товара."
        )

# My Items handlers
async def handle_my_items_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # Use effective_user to get the user ID
    user_items = load_user_data(user_id)
    
    if not user_items:
        await update.effective_chat.send_message(
            "Вы еще не добавили ни одного товара.",
            reply_markup=MAIN_KEYBOARD
        )
        return
    
    categories = list({item['category'] for item in user_items})
    keyboard = [
        [InlineKeyboardButton(category, callback_data=f'my_items_category_{category}')]
        for category in categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_chat.send_message(
        "Выберите категорию, чтобы просмотреть ваши товары:",
        reply_markup=reply_markup
    )

async def show_my_items_in_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    category = query.data.split('_')[-1]
    
    user_items = [
        item for item in load_user_data(user_id)
        if item['category'] == category
    ]
    
    if not user_items:
        await query.edit_message_text(
            f"Товары в категории {category} не найдены.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data='my_items')
            ]])
        )
        return
    
    await query.edit_message_text(f"Ваши товары в категории {category}:")
    
    for index, item in enumerate(user_items):
        text = f"*{item['name']}*\nЦена: {item['price']} ₽"
        keyboard = [[
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{index}_{category}"),
            InlineKeyboardButton("◀️ Назад", callback_data='my_items')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        photo_path = item.get("photo")
        if photo_path and os.path.exists(photo_path):
            await query.message.reply_photo(
                photo=open(photo_path, 'rb'),
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text(
                text + "\n\n(Фото не доступно)",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

# Profile handlers
async def handle_profile_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_items = load_user_data(user_id)
    purchased_items = load_user_data(f"purchased_{user_id}")
    
    profile_text = (
        "*Ваш профиль*\n"
        f"Активные объявления: {len(user_items)}\n"
        f"Купленные товары: {len(purchased_items)}\n"
    )
    
    await update.message.reply_text(
        profile_text,
        parse_mode='Markdown',
        reply_markup=MAIN_KEYBOARD
    )

# Purchased items handlers
async def handle_purchased_items_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # Get user ID reliably
    purchased_items = load_user_data(f"purchased_{user_id}")

    # Determine whether the function was called from a message or callback query
    message = update.message if update.message else update.callback_query.message

    if not purchased_items:
        await message.reply_text(
            "Вы еще не купили ни одного товара.",
            reply_markup=MAIN_KEYBOARD
        )
        return
    
    # Send an initial message about purchased items
    await message.reply_text("Ваши купленные товары:")
    
    # Display each purchased item with text or photo
    for item in purchased_items:
        text = f"*{item['name']}*\nЦена: {item['price']} ₽"
        photo_path = item.get("photo")
        
        if photo_path and os.path.exists(photo_path):
            await message.reply_photo(
                photo=open(photo_path, 'rb'),
                caption=text,
                parse_mode='Markdown'
            )
        else:
            await message.reply_text(
                text + "\n\n(Фото не доступно)",
                parse_mode='Markdown'
            )

# Purchase flow
async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_index, category = query.data.split('_')[2:4]
    
    keyboard = [[
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"buy_{item_index}_{category}"),
        InlineKeyboardButton("❌ Отменить", callback_data="buy")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if the callback query message has text or is a photo
    if query.message.text:
        # Edit the existing message text if it contains text
        await query.edit_message_text(
            "Вы уверены, что хотите купить этот товар?",
            reply_markup=reply_markup
        )
    else:
        # Send a new message if there is no text to edit
        await query.message.reply_text(
            "Вы уверены, что хотите купить этот товар?",
            reply_markup=reply_markup
        )

async def handle_buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    item_index, category = query.data.split('_')[1:3]
    
    # Find the item in seller's listings
    found_item = None
    for user_file in os.listdir("."):
        if user_file.startswith("user_data_") and user_file.endswith(".json"):
            seller_id = user_file.split("_")[2].split(".")[0]
            seller_items = load_user_data(seller_id)
            category_items = [item for item in seller_items if item['category'] == category]
            
            if int(item_index) < len(category_items):
                found_item = category_items[int(item_index)]
                break
    
    if not found_item:
        await query.edit_message_text(
            "Извините, этот товар больше недоступен.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад к категориям", callback_data='buy')
            ]])
        )
        return
    
    # Add to user's purchased items
    purchased_items = load_user_data(f"purchased_{user_id}")
    purchased_items.append(found_item)
    save_user_data(f"purchased_{user_id}", purchased_items)
    
    await query.edit_message_text(
        "✅ Покупка успешно завершена! Вы можете просмотреть этот товар в разделе купленных товаров.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Просмотреть купленные товары", callback_data='purchased_items'),
            InlineKeyboardButton("Продолжить покупки", callback_data='buy')
        ]])
    )

# Delete item handler
async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    item_index, category = int(query.data.split('_')[1]), query.data.split('_')[2]
    
    user_items = load_user_data(user_id)
    category_items = [item for item in user_items if item['category'] == category]

    if int(item_index) >= len(category_items):
        await query.edit_message_text(
            "Товар не найден.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data='my_items')
            ]])
        )
        return

    item_to_delete = category_items[item_index]
    
    # Remove photo if exists
    photo_path = item_to_delete.get("photo")
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

    # Remove item from user's listings
    user_items.remove(item_to_delete)
    save_user_data(user_id, user_items)

    # Check if the message contains text or a photo and handle accordingly
    try:
        await query.edit_message_text(
            "✅ Товар успешно удален!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад к Моим Товарам", callback_data='back_to_my_items')
            ]])
        )
    except telegram.error.BadRequest:
        # If there's no text to edit, send a new message
        await query.message.reply_text(
            "✅ Товар успешно удален!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад к Моим Товарам", callback_data='back_to_my_items')
            ]])
        )

# Main callback query handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    handlers = {
        'buy': handle_buy,
        'sell': handle_sell_start,
        'my_items': handle_my_items_text,
        'purchased_items': handle_purchased_items_text,
        'profile': handle_profile_text,
        'my_items': handle_my_items_text
    }

    if query.data in handlers:
        await handlers[query.data](update, context)
    elif query.data.startswith('category_'):
        await show_items_in_category(update, context)
    elif query.data.startswith('sell_category_'):
        await handle_sell_category(update, context)
    elif query.data.startswith('confirm_buy_'):
        await confirm_purchase(update, context)
    elif query.data.startswith('buy_'):
        await handle_buy_item(update, context)
    elif query.data.startswith('my_items_category_'):
        await show_my_items_in_category(update, context)
    elif query.data.startswith('delete_'):
        await delete_item(update, context)
    elif query.data == 'back_to_my_items':
        await handle_my_items_text(update, context)
    elif query.data == 'back_to_categories':
        await handle_buy(update, context)

# Text message handler
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'add_product_step' in context.user_data:
        if context.user_data['add_product_step'] == 'ask_name':
            await handle_product_name(update, context)
        elif context.user_data['add_product_step'] == 'ask_price':
            await handle_product_price(update, context)
        elif context.user_data['add_product_step'] == 'ask_contact':
            await handle_product_contact(update, context)
        elif context.user_data['add_product_step'] == 'ask_photo':
            await handle_product_photo(update, context)
    else:
        await handle_menu_command(update, context)

async def handle_unsupported_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'add_product_step' in context.user_data and context.user_data['add_product_step'] == 'ask_photo':
        await update.message.reply_text(
            "Неподдерживаемый тип файла. Пожалуйста, загрузите фото (JPEG или PNG)."
        )
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте параметры меню для продолжения."
        )

def main():
    # Создаем приложение и передаем токен вашего бота
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_product_photo))
    application.add_handler(MessageHandler(filters.ATTACHMENT, handle_unsupported_file))  # Обрабатывает видео и документы
    
    # Запуск бота
    print("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
