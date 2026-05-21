from pyrogram import Client, filters
import pdfplumber
from docx import Document
import re
import os
import traceback

# =========================
# VARIABLES
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

# =========================
# PYROGRAM CLIENT
# =========================

app = Client(
    "bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

print("✅ BOT STARTED")


# =========================
# START COMMAND
# =========================

@app.on_message(filters.command("start"))
async def start_command(client, message):

    await message.reply_text(
        "✅ Fancy Sort Bot Active\n\nSend PDF / DOCX / TXT"
    )


# =========================
# DEBUG MESSAGE
# =========================

@app.on_message(filters.text)
async def debug_text(client, message):

    print("TEXT RECEIVED")


# =========================
# EXTRACT NUMBERS
# =========================

def extract_numbers(text):

    return list(set(
        re.findall(r"\d{8,15}", text)
    ))


# =========================
# FANCY SCORE
# =========================

def score_number(number):

    score = 0

    # repeated digits
    if re.search(r"(\d)\1{2,}", number):
        score += 50

    # ascending
    if re.search(
        r"1234|2345|3456|4567|5678|6789",
        number
    ):
        score += 40

    # descending
    if re.search(
        r"9876|8765|7654|6543|5432|4321",
        number
    ):
        score += 40

    # repeated pair
    if re.search(r"(\d\d)\1+", number):
        score += 30

    # alternating
    if re.search(r"(\d)(\d)\1\2", number):
        score += 20

    return score


# =========================
# SORT FANCY
# =========================

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


# =========================
# READ PDF
# =========================

def read_pdf(path):

    text = ""

    with pdfplumber.open(path) as pdf:

        for page in pdf.pages:

            extracted = page.extract_text()

            if extracted:

                text += extracted + "\n"

    return text


# =========================
# READ DOCX
# =========================

def read_docx(path):

    doc = Document(path)

    text = ""

    for para in doc.paragraphs:

        text += para.text + "\n"

    return text


# =========================
# HANDLE DOCUMENT
# =========================

@app.on_message(filters.document)
async def handle_document(client, message):

    print("📥 FILE RECEIVED")

    msg = await message.reply_text(
        "⏳ Processing File..."
    )

    file_path = None

    try:

        # download
        file_path = await message.download()

        print("DOWNLOADED:", file_path)

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

        print("TEXT LENGTH:", len(text))

        numbers = extract_numbers(text)

        print("NUMBERS:", len(numbers))

        if not numbers:

            return await msg.edit(
                "❌ No Numbers Found"
            )

        sorted_numbers = sort_fancy(numbers)

        if not sorted_numbers:

            return await msg.edit(
                "❌ No Fancy Numbers Found"
            )

        output = ""

        for i, item in enumerate(
            sorted_numbers,
            start=1
        ):

            output += (
                f"{i}. +{item['number']}\n"
            )

        # split telegram messages
        chunks = [
            output[i:i + 4000]
            for i in range(
                0,
                len(output),
                4000
            )
        ]

        await msg.delete()

        for chunk in chunks:

            await message.reply_text(
                f"<code>{chunk}</code>",
                parse_mode="html"
            )

    except Exception as e:

        print(traceback.format_exc())

        await msg.edit(
            f"❌ ERROR:\n{e}"
        )

    finally:

        try:

            if file_path and os.path.exists(file_path):

                os.remove(file_path)

        except:
            pass


print("🚀 STARTING BOT")

app.run()
