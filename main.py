from pyrogram import Client, filters
import pdfplumber
from docx import Document
import re
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

app = Client(
    "fancy-bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

print("Bot Running...")


def extract_numbers(text):

    nums = re.findall(r'\d{8,15}', text)

    return list(set(nums))


def score_number(number):

    score = 0

    if re.search(r'(\d)\1{2,}', number):
        score += 50

    if re.search(r'1234|2345|3456|4567|5678|6789', number):
        score += 40

    if re.search(r'9876|8765|7654|6543|5432|4321', number):
        score += 40

    if re.search(r'(\d\d)\1+', number):
        score += 30

    if re.search(r'(\d)(\d)\1\2', number):
        score += 20

    return score


def sort_fancy(numbers):

    result = []

    for num in numbers:

        score = score_number(num)

        if score > 0:

            result.append({
                "number": num,
                "score": score
            })

    result.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return result


def read_pdf(path):

    text = ""

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:

            extracted = page.extract_text()

            if extracted:
                text += extracted + "\n"

    return text


def read_docx(path):

    doc = Document(path)

    text = ""

    for para in doc.paragraphs:

        text += para.text + "\n"

    return text


@app.on_message(filters.document)
async def handle_file(client, message):

    print("File Received")

    msg = await message.reply_text(
        "⏳ Processing File..."
    )

    file_path = await message.download()

    try:

        text = ""

        # PDF
        if file_path.lower().endswith(".pdf"):

            text = read_pdf(file_path)

        # DOCX
        elif file_path.lower().endswith(".docx"):

            text = read_docx(file_path)

        # TXT
        elif file_path.lower().endswith(".txt"):

            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:

                text = f.read()

        else:

            return await msg.edit(
                "❌ Unsupported File"
            )

        numbers = extract_numbers(text)

        if not numbers:

            return await msg.edit(
                "❌ No Numbers Found"
            )

        sorted_nums = sort_fancy(numbers)

        if not sorted_nums:

            return await msg.edit(
                "❌ No Fancy Numbers Found"
            )

        output = ""

        for i, item in enumerate(sorted_nums, start=1):

            output += (
                f"{i}. +{item['number']}\n"
            )

        chunks = [
            output[i:i+4000]
            for i in range(
                0,
                len(output),
                4000
            )
        ]

        await msg.delete()

        for part in chunks:

            await message.reply_text(
                f"<code>{part}</code>",
                parse_mode="html"
            )

    except Exception as e:

        print(e)

        await msg.edit(
            f"❌ Error:\n{e}"
        )

    finally:

        if os.path.exists(file_path):

            os.remove(file_path)


@app.on_message(filters.command("start"))
async def start_cmd(client, message):

    await message.reply_text(
        "✅ Fancy Sort Bot Active\n\nSend PDF / DOCX / TXT"
    )


app.run()
