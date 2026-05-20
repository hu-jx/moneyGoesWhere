from telegram import Update
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes
import os 
import logging
import data_processing
from zoneinfo import ZoneInfo
from datetime import datetime

###FUTURE EXPANSION: add "edit" and "delete record" functions -> complete CRUD###

load_dotenv()
my_token = os.getenv("TELEGRAM_BOT_KEY") #loads the api key from local environment file 

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

#Defining command handlers for expenses tracking 
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Restarts the Telegram bot. If there is any pre-existing chat and record history, the data will be cleared.
    """
    data_processing.delete()
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
    total = data_processing.filter_daily(update.message.from_user.id, 
                                         to_sgt(update.message.date))
    await update.message.reply_text(f"Total today: ${total:.2f}")

async def todays_records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a text showing all records from today if present. 
    Else, returns a message saying that there are no records today. 
    """
    now = to_sgt(update.message.date)
    table = data_processing.todays_records(update.message.from_user.id,
                                           now)
    if (not table):
        await update.message.reply_text(f"No records found for today {now.strftime('%Y-%m-%d')}")
        return 
    
    str_table = ""
    for row in table:
        cat, cost, timestamp = row[2], row[3], row[-1]
        date, time = timestamp.split()
        if row == table[-1]:
            str_table = str_table + f"At {time}: {cat} — ${cost:.2f}"
        else:
            str_table = str_table + f"At {time}: {cat} — ${cost:.2f}\n"
    await update.message.reply_text(f"Today's ({date}) records are as follows: \n"+ \
                                    str_table)

async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a text highlighting the user's total expenses for that specific month
    """
    total = data_processing.filter_monthly(update.message.from_user.id, 
                                           to_sgt(update.message.date))
    await update.message.reply_text(f"Total this month: ${total:.2f}")

def main() -> None:
    """Creates database if it does not exists already in local disk and start the bot"""
    data_processing.init_db()
    app = Application.builder().token(my_token).build()

    #add command to the telegram bot
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("monthly", monthly))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("get_today", todays_records))

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