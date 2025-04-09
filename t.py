
import json
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

BOT_TOKEN = "7846035245:AAFQ7sAkLt_D8LFIdWDx2N6cgr0dTp5wvnU"
OWNER_ID = 7814078698
OWNER_USERNAME = "@MRSKYX0"

USER_DATA_FILE = "users.json"
TICKET_DATA_FILE = "tickets.json"
CREDIT_DATA_FILE = "credits.json"
PLAN_FILE = "plan.txt"

forward_map = {}
user_ids = set()
tickets = {}
credits = {}
current_plan = "No plan set."

def load_data():
    global user_ids, tickets, credits, current_plan
    try:
        with open(USER_DATA_FILE, "r") as f:
            user_ids.update(json.load(f))
    except:
        pass
    try:
        with open(TICKET_DATA_FILE, "r") as f:
            tickets.update(json.load(f))
    except:
        pass
    try:
        with open(CREDIT_DATA_FILE, "r") as f:
            credits.update(json.load(f))
    except:
        pass
    try:
        with open(PLAN_FILE, "r") as f:
            current_plan = f.read()
    except:
        pass

def save_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(list(user_ids), f)
    with open(TICKET_DATA_FILE, "w") as f:
        json.dump(tickets, f)
    with open(CREDIT_DATA_FILE, "w") as f:
        json.dump(credits, f)
    with open(PLAN_FILE, "w") as f:
        f.write(current_plan)

def get_keyboard(is_owner=False):
    base_buttons = [
        ["ðŸ“¥ Start", "ðŸ“– Help"],
        ["ðŸŽ« Support", "ðŸ“‚ Check Status"],
        ["ðŸ’³ KD", "ðŸ“„ Plan"]
    ]
    if is_owner:
        base_buttons.append(["ðŸ“¢ Broadcast", "âœï¸ Update Ticket", "âœ… Approve"])
    return ReplyKeyboardMarkup(base_buttons, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_owner = user.id == OWNER_ID
    keyboard = get_keyboard(is_owner)
    await update.message.reply_text("ðŸ¤– Welcome to Killer Bot!", reply_markup=keyboard)
    if not is_owner:
        user_ids.add(user.id)
        save_data()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ðŸ›  All Commands:\n"
        "/start\n/help\n/support <issue>\n/check_status <ticket_id>\n"
        "/kd <card>|<mm>|<yy>|<cvv>\n/plan\n/update_ticket <ticket_id> <status>\n"
        "/approve <user_id> <days> <coins>")

async def support_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    ticket_id = str(random.randint(100000, 999999))
    tickets[ticket_id] = {"user_id": user.id, "status": "Pending"}
    save_data()
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("In Progress", callback_data=f"inprogress_{ticket_id}"),
        InlineKeyboardButton("Completed", callback_data=f"complete_{ticket_id}")
    ]])
    await context.bot.send_message(OWNER_ID, f"ðŸŽ« Ticket ID: {ticket_id}\nUser: @{user.username or user.id}\nIssue: {message.text}", reply_markup=buttons)
    await update.message.reply_text(f"âœ… Ticket created. ID: {ticket_id}")

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.strip().split()
    if len(parts) < 2:
        await update.message.reply_text("Usage: /check_status <ticket_id>")
        return
    ticket_id = parts[-1]
    ticket = tickets.get(ticket_id)
    if ticket and ticket["user_id"] == update.effective_user.id:
        await update.message.reply_text(f"ðŸ“‚ Ticket Status: {ticket['status']}")
    else:
        await update.message.reply_text("âŒ Ticket not found or unauthorized.")

async def handle_status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    ticket_id = data.split("_")[1]
    if "inprogress" in data:
        tickets[ticket_id]["status"] = "In Progress"
    elif "complete" in data:
        tickets[ticket_id]["status"] = "Completed"
    save_data()
    await query.answer("Status Updated")
    await query.edit_message_reply_markup()

async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        _, user_id, days, coins = update.message.text.split()
        user_id = int(user_id)
        expire = (datetime.now() + timedelta(days=int(days))).strftime("%Y-%m-%d")
        credits[str(user_id)] = {"coins": int(coins), "expire": expire}
        save_data()
        await update.message.reply_text(f"âœ… Approved user {user_id} with {coins} coins for {days} days.")
    except:
        await update.message.reply_text("âŒ Usage: /approve <user_id> <days> <coins>")

async def kd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in credits or credits[user_id]["coins"] <= 0:
        await update.message.reply_text("âŒ No coins available.")
        return
    text = update.message.text.replace("/kd", "").strip()
    parts = text.split("|")
    if len(parts) != 4:
        await update.message.reply_text("âŒ Usage: /kd <card>|<mm>|<yy>|<cvv>")
        return
    credits[user_id]["coins"] -= 1
    save_data()
    msg = await update.message.reply_text("â³ Processing...")
    await asyncio.sleep(7)
    elapsed = random.randint(2, 5)
    await msg.edit_text(
        f"âŒ Declined\nCard: {parts[0]}|{parts[1]}|{parts[2]}|{parts[3]}\n"
        f"ðŸ’¬ Response: Killed successfully\nâ± Time: {elapsed}s\nðŸ™ Thank you!"
    )

async def update_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        _, ticket_id, new_status = update.message.text.split(maxsplit=2)
        if ticket_id in tickets:
            tickets[ticket_id]["status"] = new_status
            save_data()
            await update.message.reply_text(f"âœ… Ticket {ticket_id} updated to {new_status}.")
        else:
            await update.message.reply_text("âŒ Ticket ID not found.")
    except:
        await update.message.reply_text("âŒ Usage: /update_ticket <ticket_id> <new_status>")

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(current_plan)

async def update_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    new_text = update.message.text.replace("update plan", "", 1).strip()
    if new_text:
        global current_plan
        current_plan = new_text
        save_data()
        await update.message.reply_text("âœ… Plan updated.")
    else:
        await update.message.reply_text("âŒ Usage: update plan <text>")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    msg = update.message.text.replace("broadcast", "", 1).strip()
    if not msg:
        await update.message.reply_text("âŒ Usage: broadcast <message>")
        return
    count = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(uid, f"ðŸ“¢ Broadcast:\n\n{msg}")
            count += 1
        except:
            continue
    await update.message.reply_text(f"âœ… Sent to {count} users.")

def main():
    load_data()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("support", support_ticket))
    app.add_handler(CommandHandler("check_status", check_status))
    app.add_handler(CommandHandler("approve", approve_user))
    app.add_handler(CommandHandler("kd", kd_command))
    app.add_handler(CommandHandler("update_ticket", update_ticket))
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("update_plan", update_plan))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(handle_status_update))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ðŸ“¥ Start$"), start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ðŸ“– Help$"), help_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ðŸŽ« Support$"), support_ticket))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ðŸ“‚ Check Status$"), check_status))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ðŸ’³ KD$"), kd_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ðŸ“„ Plan$"), plan_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^ðŸ“¢ Broadcast$"), broadcast))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^âœï¸ Update Ticket$"), update_ticket))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^âœ… Approve$"), approve_user))
    print("ðŸ¤– Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
