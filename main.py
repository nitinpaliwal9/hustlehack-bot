import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import os

TELEGRAM_BOT_TOKEN = os.getenv("7801820890:AAFvK8cGpjeJDCice0Ou9DOo_H5sRYDwuGc")
OPENROUTER_API_KEY = os.getenv("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")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Define conversation states
GOAL, SKILL, TIME, DOMAIN, EXPERIENCE, OUTPUT, STYLE, CONFIRM = range(8)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to HustleHack AI Roadmapper!\nLet’s build your 4-week AI-powered roadmap.\n\nWhat’s your goal? (e.g., Learn AI tools for marketing)")
    return GOAL

async def ask_skill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {"goal": update.message.text}
    reply_keyboard = [["Beginner", "Intermediate", "Pro"]]
    await update.message.reply_text("What’s your current skill level?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SKILL

async def ask_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["skill"] = update.message.text
    await update.message.reply_text("How many hours per week can you spend on this? (e.g., 5h, 10h)")
    return TIME

async def ask_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["time"] = update.message.text
    await update.message.reply_text("Which field or domain are you targeting? (e.g., content creation, startups, freelancing)")
    return DOMAIN

async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["domain"] = update.message.text
    await update.message.reply_text("Do you have any prior experience in this field? (Yes/No)")
    return EXPERIENCE

async def ask_output(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["experience"] = update.message.text
    await update.message.reply_text("What kind of output do you want at the end of 4 weeks? (e.g., launch a tool, land a client, build portfolio)")
    return OUTPUT

async def ask_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["output"] = update.message.text
    await update.message.reply_text("What learning style works best for you? (e.g., hands-on, video-based, written guides)")
    return STYLE

async def generate_roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id]["style"] = update.message.text
    await update.message.reply_text("⏳ Generating your roadmap... Please wait.")

    u = user_data[update.effective_user.id]
    prompt = f"""
    Build a 4-week AI-powered learning and execution roadmap for the following:
    Goal: {u['goal']}
    Skill Level: {u['skill']}
    Time Available: {u['time']} per week
    Domain: {u['domain']}
    Prior Experience: {u['experience']}
    Output Expected: {u['output']}
    Preferred Style: {u['style']}

    Include weekly breakdowns with topics, tools, micro-tasks, prompts, and a motivational message.
    """

    roadmap = get_roadmap(prompt)
    await update.message.reply_text(roadmap)
    return ConversationHandler.END


def get_roadmap(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You're a helpful roadmap generator."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        print("✅ OpenRouter response:", result)
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ OpenRouter ERROR:", e)
        return "⚠️ Sorry, something went wrong while generating your roadmap. Please try again later."

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled. You can restart anytime with /start.")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_skill)],
            SKILL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_time)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_domain)],
            DOMAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_experience)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_output)],
            OUTPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_style)],
            STYLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_roadmap)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
