import os
from telegram import Update
from telegram.ext import CallbackContext
from dalle_service import DalleService

class GameSession:
    STATE_NOT_STARTED = 'not_started'
    STATE_WAITING_FOR_POSITION = 'waiting_for_position'
    STATE_WAITING_FOR_COMPANY = 'waiting_for_company'
    STATE_WAITING_FOR_PROMPT = 'waiting_for_prompt'
    STATE_WAITING_FOR_CONFIRMATION = 'waiting_for_confirmation'

    def __init__(self, user, config, is_running = False):
        self.config = config
        self.user = user
        self.dalle_service = DalleService(config.openai_api_key)
        self.last_image = None
        self.attempts_left = user.attempts_left
        self.state = self.STATE_NOT_STARTED if not is_running else self.STATE_WAITING_FOR_PROMPT


    def submit_attempt(self, image):
        if self.attempts_left > 0 and not image is None and not self.user.image_submitted:
            self.attempts_left = 0
            self.save_user_image(image)
            self.user.image_submitted = image.image_name
            self.save_user_info()
            return True
        return False
    
    def has_attempts_left(self):
        return self.attempts_left > 0
    
    def get_predefined_image(self):
        return open(self.config.predefined_image_path, 'rb')

    def save_user_image(self, image):
        user_folder = f'user_data/{self.user.telegram_name}'
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        image_path = os.path.join(user_folder, f'{len(os.listdir(user_folder)) + 1}.jpg')
        with open(image_path, 'wb') as image_file:
            image_file.write(image.image_data)
        return image_path

    def save_user_info(self):
        user_folder = f'user_data/{self.user.telegram_name}'

        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        info_path = os.path.join(user_folder, 'info.txt')

        with open(info_path, 'w') as info_file:
            info_file.write(f"Name: {self.user.user_name}\n")
            info_file.write(f"Id: {self.user.user_id}\n")
            info_file.write(f"Telegram account: {self.user.telegram_name}\n")
            info_file.write(f"Image submitted: {self.user.image_submitted}\n")
            info_file.write(f"Attempts left: {self.attempts_left}\n")     
            info_file.write(f"Last prompt: {self.user.last_prompt}\n") 
            info_file.write(f"Position: {self.user.position}\n")   
            info_file.write(f"Company: {self.user.company}\n")          

    async def start(self, update: Update, context: CallbackContext):
        if self.state != self.STATE_NOT_STARTED:
            if (self.attempts_left > 0):
                await update.message.reply_text(_("Game is already running. Please enter a prompt for the image:"))
            else:
                await update.message.reply_text(_("You have no attempts left. Please come back tomorrow."))
            return
        
        self.state = self.STATE_WAITING_FOR_PROMPT
        await update.message.reply_text(_("Welcome to the 'Culture Code' game! Here are the rules..."))
        await update.message.reply_text(_("Game Rules"))
        # Send the predefined image
        with self.get_predefined_image() as image:
            await update.message.reply_photo(photo=image)
            
        await update.message.reply_text(_("Please enter a prompt for the image:"))

    async def handle_message(self, update: Update, context: CallbackContext):
        if self.state == self.STATE_WAITING_FOR_PROMPT:
            # Check if the user has already submitted an image today and have attempts
            if self.user.image_submitted:
                await update.message.reply_text(_("You have already submitted a result today. Please come back tomorrow."))
                return  
            if not self.has_attempts_left():
                await update.message.reply_text(_("You have no attempts left. Please come back tomorrow."))
                return  
        
            prompt = update.message.text

            # Generate image from DALLE-3
            try:
                await update.message.reply_text(_("Generating image..."))
                self.last_image = self.dalle_service.generate_image(prompt)
                self.user.last_prompt = prompt
                await update.message.reply_photo(photo=self.last_image.image_data)
                self.state = self.STATE_WAITING_FOR_CONFIRMATION

                if (self.attempts_left == 1):
                    await update.message.reply_text(_("This is your last attempt. Do you want to submit this image for validation? (yes/no)"))
                elif (self.attempts_left == 2):
                    await update.message.reply_text(_("You have 2 attempts left. Do you want to submit this image for validation? (yes/no)"))
                else:
                    await update.message.reply_text(_("Do you want to submit this image for validation? (yes/no)"))

            except Exception as e:
                await update.message.reply_text(str(e))
        elif self.state == self.STATE_WAITING_FOR_CONFIRMATION:
            if update.message.text.lower() == 'yes':
                if self.submit_attempt(self.last_image):
                    await update.message.reply_text(_("Congratulations, the image was submitted!"))
                    if not self.user.position:
                        await update.message.reply_text(_("Btw, what is your position in your company?"))
                        self.state = self.STATE_WAITING_FOR_POSITION
                        return
                else:
                    await update.message.reply_text(_("Something went wrong! Please enter another prompt:"))
                self.state = self.STATE_WAITING_FOR_PROMPT

            elif update.message.text.lower() == 'no':
                self.attempts_left -= 1
                self.save_user_info()
                if self.has_attempts_left():
                    await update.message.reply_text(_("Allright. Attempts left: ") + str(self.attempts_left) + ". " + _("Please enter another prompt:"))
                else:
                    await update.message.reply_text(_("You have no attempts left. Please come back tomorrow."))
                self.state = self.STATE_WAITING_FOR_PROMPT

            else:
                await update.message.reply_text(_("Please answer with 'yes' or 'no'"))
        elif self.state == self.STATE_WAITING_FOR_POSITION:
            self.user.position = update.message.text[:100]
            self.save_user_info()
            await update.message.reply_text(_("How interesting! And what is the name of your company?"))
            self.state = self.STATE_WAITING_FOR_COMPANY
        elif self.state == self.STATE_WAITING_FOR_COMPANY:
            self.user.company = update.message.text[:100]
            self.save_user_info()
            await update.message.reply_text(_("Understood. We will validate your image and send you the results soon. Thank you for participating! Please come back tomorrow \xF0\x9F\x98\x89."))
            self.state = self.STATE_WAITING_FOR_PROMPT
            
            

    async def handle_print_rules(self, update: Update, context: CallbackContext):
        await update.message.reply_text(_("Game Rules"))

    


