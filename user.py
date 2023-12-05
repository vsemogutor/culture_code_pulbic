class User:
    def __init__(self, user_id: int, user_name: str, telegram_name: str, position: str = '', company = '', image_submitted: str = '', attempts_left: int = 0, last_prompt: str = ''):
        self.user_id = user_id
        self.user_name = user_name
        self.telegram_name = telegram_name
        self.position = position
        self.company = company
        self.image_submitted = image_submitted
        self.attempts_left = attempts_left
        self.last_prompt = last_prompt

