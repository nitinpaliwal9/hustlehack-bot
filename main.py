import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# === Your Keys ===
TELEGRAM_BOT_TOKEN = "7801820890:AAFvK8cGpjeJDCice0Ou9DOo_H5sRYDwuGc"
OPENROUTER_API_KEY = "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"

# === Enable Logs ===
logging.basicConfig(level=logging.INFO)

# === Conversation Stages ===
QUESTIONS = [
    "🎯 What's your main goal?",
    "📚 What's your current skill level? (Beginner / Intermediate / Pro)",
    "⏰ How many hours per week can you dedicate?",
    "📌 Do you prefer hands-on practice, videos, or reading?",
    "⚙️ Are you focusing on personal growth or building a startup?",
    "🧰 Do you want AI tools, prompt templates, or both?",
    "🗓️ Do you have a deadline or target month?"
]

ANSWERS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ANSWERS[user_id] = {"step": 0, "answers": []}
    await update.message.reply_text("👋 Welcome to HustleHack AI Roadmapper!\nLet's build your 4-week AI-powered roadmap. Ready?")
    await update.message.reply_text(QUESTIONS[0])
    return 1

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = ANSWERS.get(user_id)

    if not data:
        await update.message.reply_text("Please type /start to begin.")
        return ConversationHandler.END

    step = data["step"]
    data["answers"].append(update.message.text)

    step += 1
    if step < len(QUESTIONS):
        data["step"] = step
        await update.message.reply_text(QUESTIONS[step])
        return 1
    else:
        await update.message.reply_text("⏳ Generating your roadmap...")
        full_prompt = "\n".join(
            [f"Q{i+1}: {q}\nA: {a}" for i, (q, a) in enumerate(zip(QUESTIONS, data["answers"]))]
        )

        roadmap = get_roadmap(full_prompt)
        await update.message.reply_text("✅ Here's your personalized roadmap:")
        await update.message.reply_text(roadmap)

        del ANSWERS[user_id]
        return ConversationHandler.END

def get_roadmap(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You're an expert roadmap generator for creators, students, and founders."},
            {"role": "user", "content": f"Based on this information, create a detailed 4-week AI roadmap:\n{prompt}"}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        print("✅ OpenRouter response:", result)  # This helps debug

        return result["choices"][0]["message"]["content"]

    except Exception as e:
        print("❌ OpenRouter ERROR:", e)
        return "⚠️ Sorry, something went wrong while generating your roadmap. Please try again later."


# === App Setup ===
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]},
)

app.add_handler(conv_handler)

if __name__ == "__main__":
    print("🤖 Bot is running...")
    app.run_polling()
