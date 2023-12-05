import os
import json

class BotConfig:
    def __init__(self, telegram_token, openai_api_key, predefined_image_path, max_attempts):
        self.telegram_token = telegram_token
        self.openai_api_key = openai_api_key
        self.predefined_image_path = predefined_image_path
        self.max_attempts = max_attempts

    @staticmethod
    def load_config():
        with open('config.json') as f:
            config_data = json.load(f)

        telegram_token = config_data.get('telegram_token')
        openai_api_key = config_data.get('openai_api_key')
        predefined_image_path = config_data.get('predefined_image_path')
        max_attempts = config_data.get('max_attempts')

        return BotConfig(telegram_token, openai_api_key, predefined_image_path, max_attempts)
        