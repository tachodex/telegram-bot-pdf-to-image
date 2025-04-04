import os
import hashlib
import json
import fitz  # PyMuPDF
from dotenv import load_dotenv
load_dotenv()
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
import time
from flask import Flask
from threading import Thread

# Get credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Validate required environment variables
required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "ADMIN_ID"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Database file path
DB_FILE = "bot_database.json"

# Initialize database if not exists
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({"users": {}, "total_users": 0}, f)

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

def update_user_stats(user_id):
    db = load_db()
    if str(user_id) not in db["users"]:
        db["users"][str(user_id)] = {"conversations": 0}
        db["total_users"] += 1
    db["users"][str(user_id)]["conversations"] += 1
    save_db(db)

def clear_user_stats(user_id):
    db = load_db()
    if str(user_id) in db["users"]:
        db["users"][str(user_id)]["conversations"] = 0
        save_db(db)

# Dictionary to store temporary user data
user_data = {}

# Function to create a unique hash for a file
def create_file_hash(file_data):
    return hashlib.md5(file_data).hexdigest()

# Function to get the user's directory
def get_user_directory(user_id):
    user_hash = hashlib.md5(str(user_id).encode()).hexdigest()
    return os.path.join("user_data", user_hash)

# Ensure the user_data directory exists
os.makedirs("user_data", exist_ok=True)

# Initialize the Pyrogram Client
app = Client(
    "pdf_to_image_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# Flask app for keep-alive
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

def pdf_to_images(pdf_path, output_dir, pdf_hash):
    """
    Convert a PDF file to images using PyMuPDF (fitz).
    """
    images = []
    pdf_document = fitz.open(pdf_path)  # Open the PDF file

    # Iterate through each page
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)  # Load the page
        pix = page.get_pixmap()  # Render the page as an image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # Convert to PIL Image
        image_path = os.path.join(output_dir, f"{pdf_hash}_page_{page_num + 1}.jpg")
        img.save(image_path, "JPEG")  # Save the image
        images.append(image_path)

    return images

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    update_user_stats(message.from_user.id)
    await message.reply_text(
        "Welcome! Send me images, and I'll store them in a file directory and convert them into a images.\n\n"
        "Available commands:\n"
        "/start - Start\n"
        "/clear - Reset your images\n"
        "/usage - View your usage statistics\n\n"
        "Just send me images to get started!"
    )

@app.on_message(filters.command("stats") & filters.user(int(os.getenv("ADMIN_ID"))))
async def stats(client: Client, message: Message):
    db = load_db()
    await message.reply_text(f"Total users: {db['total_users']}")

@app.on_message(filters.command("usage"))
async def usage(client: Client, message: Message):
    db = load_db()
    user_id = str(message.from_user.id)
    count = db["users"].get(user_id, {}).get("conversations", 0)
    await message.reply_text(f"Your conversation count: {count}")

@app.on_message(filters.command("clear"))
async def clear_usage(client: Client, message: Message):
    clear_user_stats(message.from_user.id)
    await message.reply_text("Your usage stats have been cleared")

@app.on_message(filters.document)
async def handle_pdf(client: Client, message: Message):
    user_id = message.from_user.id
    update_user_stats(user_id)
    user_dir = get_user_directory(user_id)

    # Create the user's directory if it doesn't exist
    os.makedirs(user_dir, exist_ok=True)

    # Check if the file is a PDF
    if not message.document.file_name.endswith(".pdf"):
        await message.reply_text("Please send a valid PDF file.")
        return

    # Download the PDF file
    await message.reply_text("Downloading your PDF file...")
    pdf_data = await message.download(in_memory=True)  # Download the file in memory
    pdf_data.seek(0)  # Reset the file pointer
    pdf_bytes = pdf_data.read()  # Read the file content

    # Generate a unique hash for the PDF file
    pdf_hash = create_file_hash(pdf_bytes)
    pdf_path = os.path.join(user_dir, f"{pdf_hash}.pdf")

    # Save the PDF file to disk
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Convert PDF to images
    await message.reply_text("Converting PDF to images...")
    try:
        image_paths = pdf_to_images(pdf_path, user_dir, pdf_hash)
    except Exception as e:
        await message.reply_text(f"Error converting PDF: {e}")
        return

    # Send the images to the user
    for image_path in image_paths:
        await message.reply_photo(image_path)

    # Add a small delay to ensure file handles are released
    time.sleep(2)

    # Clean up
    for file in os.listdir(user_dir):
        file_path = os.path.join(user_dir, file)
        try:
            os.remove(file_path)
        except PermissionError:
            # If the file is still in use, skip it
            print(f"Skipping file {file_path} (still in use)")

    await message.reply_text("Conversion complete! All images have been sent.")

if __name__ == "__main__":
    # Start the Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True  # Daemonize the thread so it exits when the main program exits
    flask_thread.start()

    # Start the bot
    print("Bot is running...")
    app.run()
