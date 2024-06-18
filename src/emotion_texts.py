import random


class EmotionTexts:
    EMOTION_MESSAGES = {
        "SAD": [
            "It's okay to feel sad sometimes. Remember, brighter days are ahead.",
            "Take a deep breath. You're stronger than you think.",
            "Even the darkest clouds have a silver lining. Hang in there!",
        ],
        "ANGRY": [
            "Take a moment to breathe deeply. You’ve got this.",
            "Anger is a natural emotion. Let’s channel it into something positive.",
            "It's okay to feel angry. Try to find a calm moment to reflect.",
        ],
        "SURPRISE": [
            "Wow! That was unexpected! Embrace the surprise!",
            "Surprises can be exciting. Enjoy the moment!",
            "Life is full of surprises. Keep your curiosity alive!",
        ],
        "FEAR": [
            "It's okay to feel scared. You're not alone.",
            "Take a deep breath and face your fears one step at a time.",
            "Courage is not the absence of fear, but the triumph over it.",
        ],
        "HAPPY": [
            "Your smile is contagious! Keep spreading the joy!",
            "Happiness looks great on you. Keep shining!",
            "You´re glowing with positivity! Stay radiant!",
        ],
        "DISGUST": [
            "It's natural to feel disgust. Take a moment to breathe.",
            "Disgust can be overwhelming. Find a way to calm your mind.",
            "Remember, you have the strength to overcome unpleasant feelings.",
        ],
        "NEUTRAL": [
            "Feeling neutral is perfectly fine. Enjoy the calm.",
            "A neutral state of mind can be very peaceful.",
            "Balance and calmness are key. Stay centered.",
        ],
    }

    def get_text(self, emotion):
        if emotion in self.EMOTION_MESSAGES:
            return random.choice(self.EMOTION_MESSAGES[emotion])
        else:
            return "Unknown emotion."
