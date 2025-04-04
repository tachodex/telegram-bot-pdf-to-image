# Telegram Image to PDF Bot

A simple Telegram bot that converts images into PDF files.

## Features

- Converts images to PDF with one click
- Tracks your usage statistics
- Easy to use with simple commands

## How to Use

1. Start the bot by sending `/start`
2. Send any images you want to convert
3. The bot will combine them into a PDF file
4. Download your PDF when ready

## Available Commands

- `/start` - Get welcome message and instructions
- `/usage` - Check how many conversions you've done
- `/clear` - Reset your usage statistics

## Setup (For Developers)

1. Create a Telegram bot using [BotFather](https://t.me/botfather)
2. Get your API credentials:
   - API_ID from [my.telegram.org](https://my.telegram.org)
   - API_HASH from same site
3. Create a `.env` file with these details:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   ADMIN_ID=your_admin_id
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the bot:
   ```bash
   python telegram_pdf_to_img.py
   ```

## Requirements

- Python 3.6+
- Pyrogram
- Pillow (PIL)
- PyMuPDF (fitz)
- python-dotenv

## Support

For any issues, please create a [issue](https://github.com/tachodex/telegram-bot-pdf-to-image/issues/new).
