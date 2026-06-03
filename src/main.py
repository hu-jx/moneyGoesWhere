from telegram import Update
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes, ApplicationHandlerStop, TypeHandler
import os 
import logging
from zoneinfo import ZoneInfo
from datetime import datetime

import data_processing

###FUTURE EXPANSION: add "delete record" functions to delete specific records

load_dotenv()
my_token = os.getenv("TELEGRAM_BOT_KEY") #loads the api key from local environment file 

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MY_USER_ID = os.getenv("MY_USER_ID")

async def block_unauthorized(update, context):
    user_id = update.effective_user.id
    if not user_id:
        return
    # Check if the user is authorized
    if int(user_id) != int(MY_USER_ID):
        # Ignore or send an unauthorized message
        await update.message.reply_text("Unauthorized access. You are not allowed to use this bot.")
        raise ApplicationHandlerStop

#Defining command handlers for expenses tracking 
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Restarts the Telegram bot. If there is any pre-existing chat and record history, the data will be cleared.
    """
    data_processing.reset()
    data_processing.init_db()
    context.user_data.clear()

    await update.message.reply_text("Conversation and expenses history cleared.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Parses input message and updates the database with the new recorded expense.
    Expected usage: /add <cost> <category> or /add <category> <cost>
    """

    #hard-coded categories 
    categories = ['Food', 'Shopping', 'Bills', 'Entertainment', 'Education']

    if not context.args:
        await update.message.reply_text(
            "Please provide a cost and optional category.\n" + \
                "Usage: /add <cost> [category]"
        )
        return 

    args = context.args

    potential_cost_val = [arg for arg in args if is_valid_value(arg)]
    
    if (not potential_cost_val) or (len(potential_cost_val) > 1): 
        await update.message.reply_text(
            "Couldn't find a valid cost. Please enter a number.\n" + \
                "Usage: /add <cost> [category]"
        )
        return
    
    cost = float(potential_cost_val[0])
    cat = " ".join([arg for arg in args if (arg not in potential_cost_val)]).title() or "Other"
    
    data_processing.add_expense(
        update.message.from_user.id,
        to_sgt(update.message.date),
        cat,
        cost
    )

    await update.message.reply_text(f"Recorded: {cat} — ${cost:.2f}")
    

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a text highlighting the user's expense for that specific day 
    """
    now = to_sgt(update.message.date)
    total = data_processing.filter_daily(update.message.from_user.id, 
                                         now)
    table = data_processing.todays_records(update.message.from_user.id,
                                           now)
    if (not table):
        await update.message.reply_text(f"No records found for today {now.strftime('%Y-%m-%d')}")
        return 
    
    #Make table into string 
    str_table = ""
    for row in table:
        id, cat, cost, timestamp = row[0], row[2], row[3], str(row[-1])
        time = timestamp.split()[1]
        if row == table[-1]:
            str_table = str_table + f"No.{id}) At {time}: {cat} — ${cost:.2f}"
        else:
            str_table = str_table + f"No.{id}) At {time}: {cat} — ${cost:.2f}\n"
    await update.message.reply_text(f"Total today: ${total:.2f}\n\n" + \
                                    f"Today's ({str(now).split()[0]}) records are as follows: \n"+ \
                                    str_table)

async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a text highlighting the user's total expenses for that specific month
    """
    total = data_processing.filter_monthly(update.message.from_user.id, 
                                           to_sgt(update.message.date))
    table = data_processing.get_monthly(update.message.from_user.id, 
                                        to_sgt(update.message.date))
    if not table:
        await update.message.reply_text(f"Total this month: $0.00 \nNo records found this month")
        return 
    
    #Make table into string
    str_table = ""
    for row in table:
        id, cat, cost, timestamp = row[0], row[2], row[3], str(row[-1])
        date = timestamp.split()[0]
        if row == table[-1]:
            str_table = str_table + f"No.{id}) On {date}: {cat} — ${cost:.2f}"
        else:
            str_table = str_table + f"No.{id}) On {date}: {cat} — ${cost:.2f}\n"
    await update.message.reply_text(f"Total this month: ${total:.2f} \n\n" + \
                                    f"All records for this month are as follows:\n{str_table}")
    
async def edit_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Updates the record of the specified id with the new contents. 
    Expected Usage: /edit_by_id <numerical id>, <field to update>: <new value>, <field to update>: <new value>, ...
    Possible field inputs (regardless of capitalisation): date, category or cat, cost. 
    """
    usr = update.message.from_user.id
    fields = ['date', 'category', 'cost', 'cat']
    try: 
        args = update.message.text.split("/edit_by_id ")[1].split(", ")
        record_id = args[0]
        if not record_id.isnumeric() or len(args) < 2:
            await update.message.reply_text("Invalid format. No updates made.")
            return 
    except IndexError: 
        await update.message.reply_text("No updates given. No update was made.")
        return 
    except Exception: 
        await update.message.reply_text("No updates given. No update was made.")
    for arg in args[1:]:
        changes = [string.strip().lower() for string in arg.split(":")]
        if len(changes) < 2:
            await update.message.reply_text("Invalid format. No update was made.")
            return
        field, val = changes
        if field not in fields:
            await update.message.reply_text("Invalid field input given. No update was made.")
            return
        if field == 'cost':
            if not is_valid_value(val):
                await update.message.reply_text("Invalid value input for cost given. No update was made.")
                return
            else:
                val = float(val)
        try: 
            data_processing.update_record(usr, int(record_id), field, val)
            await update.message.reply_text(f"Record number {record_id} has been updated")
        except Exception as e:

            await update.message.reply_text(f"An error occurred: {str(e)}")

async def delete_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usr = update.message.from_user.id
    if not context.args:
        await update.message.reply_text(f"No record ID given")
        return
    elif not context.args[0].isnumeric():
        await update.message.reply_text(f"Invalid record ID given")
        return
    elif len(context.args) > 1:
         await update.message.reply_text(f"Deletion can only be done one record at a time for now. Please try again.")
         return
    record_id = context.args[0]
    
    try: 
        data_processing.delete(usr, record_id)
        await update.message.reply_text(f"Record number {record_id} has been deleted")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a clear guide on how to use the bot's features."""
    help_text = (
        "*Welcome to moneyGoesWhere, a money tracker bot!*\n\n"
        "Here are the available commands you can use:\n"
        "• /start — Initialize the bot\n\n"
        "• /help — Show this instruction guide\n\n"
        "• /add - Adds new record to existing expenses.\n"
        "Expected usage: '/add <cost> <category>'\n\n"
        "• /today - Returns the total amount spent on current date in SGT and all records created in the current date\n\n"
        "• /monthly - Returns the total amount spent in the current month in SGT and all records created in the current month\n\n"
        "• /restart - Clears pre-existing chat and expenses data history\n\n"
        r"• /edit\_by\_id — Modify an existing expense record"
        "\n*How to edit a record:*\n"
        "`/edit_by_id <id>, <field>: <value>`\n"
        "Example: `/edit_by_id 12, cost: 45.50`\n\n"
        r"• /delete\_by\_id — Delete an existing expense record."
        "\nExpected usage: `/delete_by_id <id>`"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")

def main() -> None:
    """Creates database if it does not exists already in local disk and start the bot"""
    data_processing.init_db()
    app = Application.builder().token(my_token).build()

    #check authorization before running bot (for admin only currently)
    app.add_handler(TypeHandler(Update, block_unauthorized), group=-1)

    #add command to the telegram bot
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("monthly", monthly))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("edit_by_id", edit_by_id))
    app.add_handler(CommandHandler("delete_by_id", delete_by_id))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", help_command))

    #run bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

def to_sgt(dt):
    return dt.astimezone(ZoneInfo("Asia/Singapore")).replace(tzinfo=None)

def is_valid_value(arg: int):
    try:
        float(arg)
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    main()