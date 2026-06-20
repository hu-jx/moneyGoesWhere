# moneyGoesWhere - A Telegram bot for expenses managing
## Overview
Telegram is a widely used social messaging platform, frequently used by its users to check messages. Telegram bots allow for the app to have functionalities beyond just social interaction. As Telegram users are already familiar with the interface and would frequently use the app, this allows for an easily accessible avenue for expenses to be managed as well. This reduces any friction that may be present when individuals are trying to get into the habit of tracking their expenses, such as getting used to new UI of dedicated expenses tracking apps.  

## Functionalities
* Simple CRUD Actions - Adding, reading, updating (by record id) and deleting (by record id) expenses logs
  * Every expense record is made with just two pieces of information: A category/item name and a cost value. 
* Simple statistics overview of today and the current monthly totals when reading logs for expenses
* Privacy: Logs remain private via a locally stored SQLite database on the user's machine running the Telegram bot

## Installation
Minimum required versions: Python 3.9
1. Set up environment secrets as shown in the .env.example file.
2. Install and set up dependencies required via running the following command in your local machine's terminal
```bash
pip install-r requirements.txt
```
3. Run the main.py file via the following command in your local machine's terminal
```bash
python src/main.py
```

## 💭 Feedback and Contributing
Discussions - Add a Discussion post in the repository's Discussion tab 
Issues - Create a new issue in the repository's Issue tab
