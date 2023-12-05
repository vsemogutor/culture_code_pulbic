from bot_config import BotConfig
from telegram.ext import Application
from game import Game
import gettext


# Set up localization
language_translation = gettext.translation("messages", "locales", languages=['ru_RU'])
language_translation.install()


def main():            
    # Load bot configuration
    config = BotConfig.load_config()

    application = Application.builder().token(token=config.telegram_token).build()

    # Instantiate the bot handler
    game = Game(config)
    game.start(application)
    print("Bot has started")

if __name__ == '__main__':
    main()
