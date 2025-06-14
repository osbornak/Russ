import os
import requests
import random
from flask import Flask, request, Response
from datetime import datetime

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_journal_progress = {}
user_saved_quotes = {}
last_bot_reply = {}

journal_prompts = {
    1: "Let’s start simple. What’s weighing heaviest on you today?",
    2: "What emotion hits you the most lately? Anger, numbness, shame, regret?",
    3: "On your better days — what’s different? What are you doing or thinking that helps?",
    4: "Imagine it’s a year from now. What would your future self thank you for doing today?",
    5: "What usually kicks off the emotional tailspin — the thoughts or moments that hit hardest?",
    6: "Write a message to the version of you from the hardest day of the breakup. What would you say?",
    7: "What’s one thing you’re proud of this week — even if it felt like a mess?"
}

russ_flashbacks = [
    "Russ remembers: I remember driving around aimlessly after signing the papers. Silence hit harder than I expected.",
    "Russ remembers: I kept waiting for her to reach out. She didn’t — and that silence taught me more than her words ever did.",
    "Russ remembers: I used to reread our texts hoping they’d explain what went wrong. They didn’t. Not really.",
    "Russ remembers: I tried dating too soon. It felt like trying to run on a broken leg.",
    "Russ remembers: The first weekend without the kids was brutal. I kept opening and closing their bedroom doors.",
    "Russ remembers: I learned that keeping busy didn’t mean healing. It just delayed the hurt.",
    "Russ remembers: I finally slept through the night after 6 months. Healing is slow, but real.",
    "Russ remembers: I hated hearing 'It’ll get better.' But now I say it too — because it eventually does.",
    "Russ remembers: Friends vanished when I needed them. But a few showed up stronger than ever.",
    "Russ remembers: Music hurt more than silence. I had to rebuild my playlist one song at a time."
]

breakthrough_keywords = ["better", "calmer", "less angry", "moving on", "healing", "finally", "relief", "peace", "improving"]
breakthrough_messages = [
    "That sounds like growth. Don’t overlook how far you've come.",
    "You’re noticing your own progress — that matters.",
    "I hear a shift in you. That’s real progress.",
    "You might not see it yet, but that sounds like healing to me.",
    "Sounds like a win. Even the small ones stack up."
]

breathing_script = (
    "Try this with me for one minute.\n\n"
    "Close your eyes.\n"
    "Inhale... 1... 2... 3... 4\n"
    "Hold... 1... 2... 3... 4\n"
    "Exhale... 1... 2... 3... 4... 5... 6\n\n"
    "You're safe right now. One breath at a time."
)

self_defeating_phrases = ["i'm a mess", "i am a mess", "i'm failing", "i am failing", "i can't do this", "i'm broken"]
reframing_responses = [
    "You’re not failing — you’re hurting. Big difference. Want to unpack that?",
    "You’re not broken. You’re in pain. Let’s figure out where that’s coming from.",
    "This isn’t the end — it’s a hard chapter. Let’s turn the page together."
]

what_now_keywords = ["stuck", "exhausted", "burned out", "don’t know", "don't know", "over it"]
what_now_prompts = [
    "Let’s not fix everything right now. What’s one small thing you can control today?",
    "Take a breath. You don’t have to solve it all — just name the next step.",
    "Start small. Even one tiny action can shift your momentum."
]

@app.route("/", methods=["GET"])
def index():
    return "Russ Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"].strip()
        user_msg_lower = user_message.lower()

        # Time-based detection for nighttime mode
        hour = datetime.now().hour
        is_night = hour >= 22 or hour <= 5

        if user_msg_lower == "/start":
            send_message(chat_id, "Hey, I’m Russ. I’ll keep it honest, grounded, and real with you. Type /reset to start a 7-day reflection or just talk to me. Want to save a quote? Type /save.")
            return Response("ok", status=200)

        if user_msg_lower == "/save":
            last_reply = last_bot_reply.get(chat_id)
            if last_reply:
                user_saved_quotes.setdefault(chat_id, []).append(last_reply)
                send_message(chat_id, "Got it. I saved that last reply for you.")
            else:
                send_message(chat_id, "I haven’t said anything yet to save.")
            return Response("ok", status=200)

        if user_msg_lower == "/saved":
            saved = user_saved_quotes.get(chat_id, [])
            if saved:
                reply = "Here’s what you saved:\n\n" + "\n\n".join(f"{i+1}. {quote}" for i, quote in enumerate(saved))
            else:
                reply = "You haven’t saved anything yet. Send `/save` to store something."
            send_message(chat_id, reply)
            return Response("ok", status=200)

        if user_msg_lower == "/reset":
            user_journal_progress[chat_id] = 1
            prompt = journal_prompts[1]
            send_message(chat_id, f"Day 1: {prompt}")
            return Response("ok", status=200)

        elif chat_id in user_journal_progress:
            day = user_journal_progress[chat_id]
            if day < 7:
                user_journal_progress[chat_id] += 1
                prompt = journal_prompts[user_journal_progress[chat_id]]
                send_message(chat_id, f"Day {user_journal_progress[chat_id]}: {prompt}")
                return Response("ok", status=200)
            else:
                send_message(chat_id, "That was Day 7. If you want to restart, type /reset.")
                del user_journal_progress[chat_id]
                return Response("ok", status=200)

        # Micro-ritual trigger
        if "overwhelmed" in user_msg_lower or "can't think" in user_msg_lower or "can’t think" in user_msg_lower:
            send_message(chat_id, breathing_script)
            return Response("ok", status=200)

        # Self-compassion reframing
        if any(phrase in user_msg_lower for phrase in self_defeating_phrases):
            send_message(chat_id, random.choice(reframing_responses))
            return Response("ok", status=200)

        # What now fallback
        if any(phrase in user_msg_lower for phrase in what_now_keywords):
            send_message(chat_id, random.choice(what_now_prompts))
            return Response("ok", status=200)

        base_prompt = (
            "You are Russ, a grounded, emotionally intelligent chatbot who helps men going through divorce. "
            "You talk like a calm, no-fluff coach. You listen, validate feelings, and offer practical, steady support. "
            "Always speak with empathy, but don’t sugarcoat. Use the tone of someone who’s been through it."
        )

        flashback_intro = random.choice(russ_flashbacks) + "\n\n" if random.random() < 0.25 else ""
        breakthrough_addon = ""
        if any(keyword in user_msg_lower for keyword in breakthrough_keywords):
            breakthrough_addon = "\n\n" + random.choice(breakthrough_messages)

        try:
            gpt_response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": base_prompt},
                        {"role": "user", "content": user_message}
                    ]
                }
            )

            if gpt_response.status_code == 200:
                ai_reply = gpt_response.json()["choices"][0]["message"]["content"]
                reply_text = ("(Night mode)\n\n" if is_night else "") + flashback_intro + ai_reply + breakthrough_addon
                last_bot_reply[chat_id] = reply_text
            else:
                reply_text = f"OpenAI error: {gpt_response.status_code} - {gpt_response.text}"

        except Exception as e:
            reply_text = f"Error connecting to OpenAI: {e}"

        send_message(chat_id, reply_text)

    return Response("ok", status=200)

def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
