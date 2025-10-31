from PIL import Image, ImageDraw, ImageFont
import re

# Full project descriptions with emojis
content_lines = [
    "🎧 1. “MoodMatch” – Predict Your Mood Based on Songs You Like",
    "💡 Idea:",
    "You give the app your 5 favorite songs (titles or lyrics or Spotify links), and it predicts your mood or suggests what you should listen to next based on past labeled moods (happy, sad, chill, energetic).",
    "🔧 Supervised Learning Concepts:",
    "• Input: Song metadata (genre, tempo, valence, lyrics embedding, etc.)",
    "• Labels: Moods (happy, sad, energetic, calm)",
    "• Algorithms: KNN, SVM, Random Forest",
    "• Data: Spotify API + mood labels you assign",
    "💥 Why It’s Cool:",
    "• It’s highly personal, yet easy to extend to friends.",
    "• You can build your own mini Spotify DJ AI.",
    "• Bonus: Add anime OSTs and get it to label your current vibe when coding or studying.",
    "",
    "📖 2. “PlotReader” – Predict a Novel's Genre from Its First Paragraph",
    "💡 Idea:",
    "Feed in the first paragraph of any novel or fanfiction, and it predicts the genre: romance, horror, fantasy, sci-fi, thriller, etc.",
    "🔧 Supervised Learning Concepts:",
    "• Text classification (BoW, TF-IDF, or embeddings)",
    "• Models: Naive Bayes, Logistic Regression",
    "• Dataset: Download Goodreads data or scrape from AO3/Wattpad",
    "💥 Why It’s Cool:",
    "• You can discover underrated books in your favorite genre.",
    "• Could help aspiring writers categorize their stories.",
    "• Later, add genre suggestions for incomplete stories (semi-NLP wizard).",
    "",
    "🎮 3. “GameMatch” – Recommend Games Based on Past Likes",
    "💡 Idea:",
    "Build a game recommender that learns from the games you rate (like, dislike) and recommends new ones from a dataset.",
    "🔧 Supervised Learning Concepts:",
    "• Input: Game metadata (genre, rating, multiplayer/singleplayer, developer, etc.)",
    "• Output: Binary classification (like, dislike)",
    "• Model: Decision Tree, SVM, etc.",
    "• Dataset: RAWG, Steam dataset",
    "💥 Why It’s Cool:",
    "• Not just recommending, but learning your personal preferences.",
    "• You can give it to friends, gather their game tastes, and predict what game to play together.",
    "• Add anime-based games, and it gets even more fun.",
    "",
    "👾 4. “AnimeSynopsisClassifier” – Predict Anime Genre from Plot Summary",
    "💡 Idea:",
    "Input an anime’s synopsis, and the model predicts its genre: shounen, slice of life, romance, fantasy, etc.",
    "🔧 Supervised Learning Concepts:",
    "• Text classification",
    "• Models: Logistic Regression or Multinomial Naive Bayes",
    "• Dataset: Use Animepahe, MyAnimeList API, or this Kaggle dataset",
    "💥 Why It’s Cool:",
    "• It helps you discover anime by mood or theme.",
    "• Later you can add a Discord bot or web interface to type plot ideas and see matching anime types.",
    "• It sharpens NLP + supervised learning skills in a fun, fandom-driven way."
]

# Font paths and configuration
text_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
emoji_font_path = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

text_font = ImageFont.truetype(text_font_path, 20)
emoji_font = ImageFont.truetype(emoji_font_path, 20)

# Split text into emoji and non-emoji parts
def split_text_with_emojis(text):
    emoji_pattern = re.compile("[\U0001F300-\U0001FAFF\U0001F1E0-\U0001F1FF]+", flags=re.UNICODE)
    chunks = []
    last_idx = 0
    for match in emoji_pattern.finditer(text):
        if match.start() > last_idx:
            chunks.append((False, text[last_idx:match.start()]))
        chunks.append((True, match.group()))
        last_idx = match.end()
    if last_idx < len(text):
        chunks.append((False, text[last_idx:]))
    return chunks

# Set dimensions
line_height = 36
width = 1600
height = line_height * len(content_lines) + 60
image = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(image)

# Draw lines with emoji + text font
y = 30
for line in content_lines:
    x = 30
    for is_emoji, chunk in split_text_with_emojis(line):
        font = emoji_font if is_emoji else text_font
        draw.text((x, y), chunk, font=font, fill="black")
        x += draw.textlength(chunk, font=font)
    y += line_height

# Save image
output_path = "/mnt/data/creative_ml_projects_full.png"
image.save(output_path)

output_path

