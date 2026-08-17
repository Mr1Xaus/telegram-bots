import random
from typing import Tuple

class EventService:
    MATH_OPS = ["+", "-", "*"]

    @classmethod
    def generate_math_puzzle(cls) -> Tuple[str, str]:
        op = random.choice(cls.MATH_OPS)
        if op == "+":
            a, b = random.randint(10, 150), random.randint(10, 150)
            ans = a + b
        elif op == "-":
            a, b = random.randint(50, 200), random.randint(1, 50)
            ans = a - b
        else:
            a, b = random.randint(2, 12), random.randint(2, 12)
            ans = a * b
            
        question = f"⚡️ <b>Ивент 'Кто успел, тот и съел'!</b>\n\nРешите пример: <b>{a} {op} {b} = ?</b>\nНаграда: <b>+10 Rep</b>!"
        return question, str(ans)

    @classmethod
    def generate_word_puzzle(cls) -> Tuple[str, str]:
        words = ["TELEGRAM", "AIOGRAM", "REPUTATION", "DATABASE", "SCHEDULER", "MODERATION"]
        word = random.choice(words)
        scrambled = "".join(random.sample(word, len(word)))
        question = f"⚡️ <b>Ивент 'Кто успел, тот и съел'!</b>\n\nСоставьте слово из букв: <b>{scrambled}</b>\nНаграда: <b>+10 Rep</b>!"
        return question, word
