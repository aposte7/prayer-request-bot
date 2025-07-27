import os
from typing import Final, Dict

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import asyncio

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
TOPIC_ID = os.getenv('TELEGRAM_TOPIC_ID')
# also integer!

# === In-memory user data ===
user_data: Dict[int, Dict[str, str]] = {}


# === Utility Functions ===
async def delete_command_message(update: Update, delay: float = 0):
    if update.effective_chat.type != "private":
        try:
            await asyncio.sleep(delay)
            await update.message.delete()
        except Exception as e:
            print(f"Couldn't delete message: {e}")


async def smart_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode="Markdown"):
    if update.effective_chat.type == "private":
        await update.message.reply_text(text, parse_mode=parse_mode)
    else:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=TOPIC_ID,
            text=text,
            parse_mode=parse_mode
        )


# === Command Handlers ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data.setdefault(user_id, {"nickname": None})
    msg = """✨ *Welcome to Prayer Request Bot* ✨

Example:  
`/pray Please pray for my family's health`

🪪 *Optional nickname:*  
`/setnick Ano7`

❓ *More help:*  
/help - Show all commands"""
    await smart_send(update, context, msg)
    await delete_command_message(update)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """📚 *Bot Command Guide*

/start - Welcome message & examples  
/help - This help message  
/pray [request] - Submit prayer  
/setnick [name] - Set nickname  
/setnick remove - Remove nickname  
/mynick - Show current nickname"""
    await smart_send(update, context, msg)
    await delete_command_message(update)


async def set_nick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    user_data.setdefault(user_id, {"nickname": None})

    # Handle no arguments (or just bot mention)
    if not args:
        current_nick = user_data[user_id].get("nickname")
        msg = f"""🪪 *Nickname Info*

Current: `{current_nick}`""" if current_nick else "🪪 *No nickname set yet.*"

        msg += """

✍️ Set with: `/setnick your_nickname`  
🧹 Remove with: `/setnick remove`"""
        await smart_send(update, context, msg)
        await delete_command_message(update)
        return

    nickname = ' '.join(args).strip()

    if nickname.lower() == "remove":
        user_data[user_id]["nickname"] = None
        response = "✅ *Nickname removed*"
    elif len(nickname) > 20:
        response = "❌ Nickname too long. Max 20 characters."
    else:
        user_data[user_id]["nickname"] = nickname
        response = f"✅ *Nickname set to:* `{nickname}`"

    await smart_send(update, context, response)
    await delete_command_message(update)


async def my_nick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nickname = user_data.get(user_id, {}).get("nickname")

    if nickname:
        msg = f"""🪪 *Your Nickname*

Current: `{nickname}`

Change with `/setnick new_name`"""
    else:
        msg = """🪪 *Your Nickname*

No nickname set (optional)  
Add one with `/setnick name`  
Example: `/setnick FaithfulOne`"""
    await smart_send(update, context, msg)
    await delete_command_message(update)


async def pray_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    request = ' '.join(context.args).strip() if context.args else None

    if not request:
        msg = """❓ *How to submit prayers*

Format:  
`/pray your_request`  

Examples:  
`/pray Please pray for my family`"""
        await smart_send(update, context, msg)
        await delete_command_message(update)
        return

    nickname = user_data.get(user_id, {}).get("nickname")
    formatted_request = f"""*{nickname if nickname else 'Anonymous'}*

{request}

💖 Let us pray together"""

    confirmation = f"""📿 *Prayer Submitted*

Your request has been shared with our prayer community.  
{'Posted as: ' + nickname if nickname else 'Posted anonymously'}"""

    await smart_send(update, context, confirmation)
    await delete_command_message(update)

    try:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=TOPIC_ID,
            text=formatted_request,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error posting prayer: {e}")
        await smart_send(update, context, "⚠️ Couldn't post to prayer group. Please try again later.")


# === Fallback Message Handler ===
def handle_response(text: str) -> str:
    text = text.lower()
    if any(g in text for g in ["hello", "hi", "hey"]):
        return 'Hello! Send /help to see how I can assist you 🙏'
    elif any(t in text for t in ["thank", "thanks", "appreciate"]):
        return "You're welcome! May God bless you abundantly ❤️"
    elif "nickname" in text:
        return "Set a nickname with /setnick (optional)"
    elif "pray" in text:
        return "Submit prayer requests with /pray [your request]"
    return "I'm a prayer request bot. Send /help for guidance."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text

    # Log message
    print(f'Message from {update.message.from_user.id} in {message_type}: "{text}"')

    # Ignore non-private (group) messages unless bot is explicitly mentioned
    if message_type != 'private':
        # Only respond if bot is mentioned in a group
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, "").strip()
            response = handle_response(new_text)
            await context.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=TOPIC_ID,
                text=response
            )
        await delete_command_message(update)
        return

    response = handle_response(text)
    await update.message.reply_text(response)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text

    # Log message
    print(f'Message from {update.message.from_user.id} in {message_type}: "{text}"')

    # Ignore non-private (group) messages unless bot is explicitly mentioned
    if message_type != 'private':
        # Only respond if bot is mentioned in a group
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, "").strip()
            response = handle_response(new_text)
            await context.bot.send_message(
                chat_id=GROUP_ID,
                message_thread_id=TOPIC_ID,
                text=response
            )
        # Always delete the message for cleanup
        await delete_command_message(update)
        return

    # Respond normally in private chat
    response = handle_response(text)
    await update.message.reply_text(response)


# === Error Handler ===
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Error: {context.error}')
    if update and update.message:
        await smart_send(update, context,
                         "⚠️ An error occurred. Please try again later.\nIf the problem persists, contact support.")


if __name__ == "__main__":
    print("🚀 Starting Prayer Request Bot...")

    app = Application.builder().token(TOKEN).build()

    commands = [
        ('start', start_command),
        ('help', help_command),
        ('pray', pray_command),
        ('setnick', set_nick_command),
        ('mynick', my_nick_command),
    ]
    for command, handler in commands:
        app.add_handler(CommandHandler(command, handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(error)

    app.run_polling(
        poll_interval=3,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )
