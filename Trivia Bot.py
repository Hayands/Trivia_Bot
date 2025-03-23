#Trivia_bot

import discord
import asyncio
import requests
import json
import html
from discord.ext import commands, tasks

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# Trivia Question Variables
trivia_question = None
trivia_answer = None

# Score File
SCORES_FILE = "scores.json"

# Trivia API function
def get_trivia_question():
    url = "https://opentdb.com/api.php?amount=1&category=27&difficulty=medium&type=multiple" 
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            question_data = data["results"][0]
            question = html.unescape(question_data["question"])
            answer = html.unescape(question_data["correct_answer"]).lower()
            return question, answer
    return None, None

# Load scores from JSON
def load_scores():
    try:
        with open(SCORES_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save scores to JSON
def save_scores(scores):
    with open(SCORES_FILE, "w") as file:
        json.dump(scores, file, indent=4)

# Update user score
def update_score(user_id):
    scores = load_scores()
    scores[str(user_id)] = scores.get(str(user_id), 0) + 1
    save_scores(scores)

# Bot event: When bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    post_trivia_question.start()  # Start trivia loop

# Task: Post Trivia Question at set interval
@tasks.loop(hours=1)  # Runs every hour
async def post_trivia_question():
    global trivia_question, trivia_answer
    channel = bot.get_channel() # channel ID  

    if channel:
        trivia_question, trivia_answer = get_trivia_question()
        if trivia_question:
            await channel.send(f"🎉 **Trivia Time!** 🎉\n{trivia_question}")
        else:
            await channel.send("⚠️ Could not fetch a trivia question. Try again later!")

# Event: Handle user answers
@bot.event
async def on_message(message):
    global trivia_answer

    if message.author == bot.user:
        return  # Ignore bot messages

    if trivia_answer and message.content.lower() == trivia_answer:
        await message.channel.send(f"✅ Correct, {message.author.mention}! 🎉")
        update_score(message.author.id)
        trivia_answer = None  # Reset question
    else:
        await bot.process_commands(message)  # Allow other commands

# Command: Show leaderboard
@bot.command()
async def leaderboard(ctx):
    scores = load_scores()
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"<@{user}>: {score}" for user, score in sorted_scores[:5]])

    if leaderboard_text:
        await ctx.send(f"🏆 **Leaderboard** 🏆\n{leaderboard_text}")
    else:
        await ctx.send("No scores recorded yet!")

# Command: Provide hint
@bot.command()
async def hint(ctx):
    if trivia_answer:
        hint_text = trivia_answer[0] + "..."  # First letter hint
        await ctx.send(f"💡 Hint: The answer starts with **{hint_text}**")
    else:
        await ctx.send("No active trivia question right now!")

# Run the bot 
bot.run("")  # Bot token
