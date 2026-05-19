from telegram import Update
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes
import os 
import logging
import data_processing
from zoneinfo import ZoneInfo

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
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Parses input message and updates the database with the new recorded expense.
    Expected usage: /add <cost> <category> or /add <category> <cost>
    """

    #hard-coded categories 
    categories = ['Food', 'Shopping', 'Bills', 'Entertainment', 'Education']

    if not context.args:
        await update.message.reply_text(
            "Please provide a cost and optional category.\nUsage: /add <cost> [category]"
        )
        return 

    args = context.args

    if len(args) > 2:
        await update.message.reply_text(
            "Invalid input. Please provide only a cost and an optional category.\nUsage: /add <cost> [category]"
        )
        return  

    cat, cost = "Other", None

    for arg in args:
        try:
            cost = float(arg)
        except ValueError:
            if arg.title() in categories:
                cat = arg.title()

    if cost is None: 
        await update.message.reply_text(
            "Couldn't find a valid cost. Please enter a number.\nUsage: /add <cost> [category]"
        )
        return
    
    data_processing.add_expense(
        update.message.from_user.id,
        to_sgt(update.message.date),
        cat.title(),
        cost
    )

    await update.message.reply_text(f"Recorded: {cat.title()} — ${cost:.2f}")
    


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a text highlighting the user's expense for that specific day 
    """
    total = data_processing.filter_daily(update.message.from_user.id, 
                                         to_sgt(update.message.date))
    await update.message.reply_text(f"Total today: ${total:.2f}")

async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a text highlighting the user's total expenses for that specific month
    """
    total = data_processing.filter_monthly(update.message.from_user.id, 
                                           to_sgt(update.message.date))
    await update.message.reply_text(f"Total this month: ${total:.2f}")

def main() -> None:
    """Create new database and start the bot"""
    data_processing.init_db()

    app = Application.builder().token(my_token).build()

    #add command to the telegram bot
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("monthly", monthly))

    #run bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

def to_sgt(dt):
    return dt.astimezone(ZoneInfo("Asia/Singapore")).replace(tzinfo=None)

if __name__ == "__main__":
    main()