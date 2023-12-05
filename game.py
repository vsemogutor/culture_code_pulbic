from telegram.ext import Application
from telegram.ext import Application, CommandHandler, MessageHandler
from telegram.ext import filters as Filters
from telegram import Update
from telegram.ext import CallbackContext
from game_session import GameSession
from user import User
import os

class Game:
    def __init__(self, config):
        self.sessions = {}
        self.config = config
        self.admin_list = []
        self.app = None

    def start(self, application: Application):
        self.app = application

        # Add command handlers
        application.add_handler(CommandHandler("start", self.handle_start))
        application.add_handler(CommandHandler("rules", self.handle_print_rules))
        application.add_handler(MessageHandler(Filters.TEXT & ~Filters.COMMAND, self.handle_message))
        application.add_handler(CommandHandler("admin", self.handle_admin_command))

        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def get_user_session(self, update: Update):
        user_id = update.message.from_user.id
        if user_id not in self.sessions:
            user = User(user_id, update.message.from_user.full_name, update.message.from_user.username)
            session = self.load_user_session(user)
            self.sessions[user_id] = session

        return self.sessions[user_id]
        
    def load_user_session(self, user):
        user_folder = f'user_data/{user.telegram_name}'
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        info_path = os.path.join(user_folder, 'info.txt')

        if not os.path.exists(info_path):
            user.image_submitted = ''
            user.attempts_left = self.config.max_attempts
            return GameSession(user, self.config)
        
        with open(info_path, 'r') as info_file:
            info_file.readline()
            info_file.readline()
            info_file.readline()

            user.image_submitted = info_file.readline().split(':')[1].strip()
            user.attempts_left = int(info_file.readline().split(':')[1].strip())
            user.last_prompt = info_file.readline().split(':')[1].strip()
            user.position = info_file.readline().split(':')[1].strip()
            user.company = info_file.readline().split(':')[1].strip()
            
        session = GameSession(user, self.config)
        return session

    async def handle_start(self, update: Update, context: CallbackContext):
        if update.message.from_user is None: 
            return
        
        session = self.get_user_session(update)
        await session.start(update, context)

    async def handle_message(self, update: Update, context: CallbackContext):
        session = self.get_user_session(update)
        await session.handle_message(update, context)

    async def handle_print_rules(self, update: Update, context: CallbackContext):
        session = self.get_user_session(update)
        await session.handle_print_rules(update, context)

    async def handle_admin_command(self, update: Update, context: CallbackContext):
        if update.message.from_user is None: 
            return
        
        if update.message.from_user.username not in self.admin_list:
            return
        
        if len(context.args) == 0:
            await update.message.reply_text("Please specify a command")
            return
        
        command = context.args[0]
        if command == "send_message_all" and len(context.args) > 1:
            await self.send_message_to_all_participants(context.args[1]);
        
    async def send_message_to_all_participants(self, message, image = None):
        participants = self.load_participants()
        for participant in participants:
            await self.app.bot.send_message(participant, message)
            if image is not None:
                await self.app.bot.send_photo(participant, image)

    def load_participants(self, repository_path = 'user_data'):
        participants = []

        for folder_name in os.listdir(repository_path):
            folder_path = os.path.join(repository_path, folder_name)

            if os.path.isdir(folder_path):
                user_info_file_path = os.path.join(folder_path, 'info.txt')

                if os.path.exists(user_info_file_path):
                    with open(user_info_file_path, 'r') as user_info_file:
                        for line in user_info_file:
                            if line.startswith('Id:'):
                                _, account_name = line.split(':', 1)
                                account_name = account_name.strip()
                                participants.append(account_name)
                                break

        return participants