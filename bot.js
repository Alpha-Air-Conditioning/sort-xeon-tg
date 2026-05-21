const TelegramBot = require("node-telegram-bot-api");
const fs = require("fs");
const pdfParse = require("pdf-parse");
const mammoth = require("mammoth");

const TOKEN = "8746414348:AAGk6GEPF0RI37eFEFQ9GMkWYtQn_vO-Vy8";

const bot = new TelegramBot(TOKEN, {
    polling: true
});

console.log("Bot Running...");

function extractNumbers(text) {

    const regex = /\d{8,15}/g;

    const found = text.match(regex) || [];

    return [...new Set(found)];
}

function scoreNumber(number) {

    let score = 0;

    // repeated digits
    if (/(\d)\1{2,}/.test(number))
        score += 50;

    // ascending
    if (/1234|2345|3456|4567|5678|6789/.test(number))
        score += 40;

    // descending
    if (/9876|8765|7654|6543|5432|4321/.test(number))
        score += 40;

    // double repeat
    if (/(\d\d)\1+/.test(number))
        score += 30;

    // alternating
    if (/(\d)(\d)\1\2/.test(number))
        score += 20;

    return score;
}

function sortFancy(numbers) {

    let result = [];

    numbers.forEach(num => {

        const score = scoreNumber(num);

        if (score > 0) {

            result.push({
                number: num,
                score
            });
        }
    });

    return result.sort((a, b) => b.score - a.score);
}

async function readDocument(path, mime) {

    // PDF
    if (mime.includes("pdf")) {

        const data = await pdfParse(
            fs.readFileSync(path)
        );

        return data.text;
    }

    // DOCX
    if (
        mime.includes("word") ||
        mime.includes("document")
    ) {

        const result =
            await mammoth.extractRawText({
                path
            });

        return result.value;
    }

    // TXT
    return fs.readFileSync(path, "utf8");
}

bot.on("document", async (msg) => {

    const chatId = msg.chat.id;

    const fileId = msg.document.file_id;

    const mime = msg.document.mime_type;

    await bot.sendMessage(
        chatId,
        "⏳ Sorting Numbers..."
    );

    try {

        const file =
            await bot.getFile(fileId);

        const fileUrl =
`https://api.telegram.org/file/bot${TOKEN}/${file.file_path}`;

        const response =
            await fetch(fileUrl);

        const buffer =
            Buffer.from(
                await response.arrayBuffer()
            );

        const localFile =
            `./${msg.document.file_name}`;

        fs.writeFileSync(localFile, buffer);

        const text =
            await readDocument(localFile, mime);

        const numbers =
            extractNumbers(text);

        const sorted =
            sortFancy(numbers);

        if (sorted.length === 0) {

            return bot.sendMessage(
                chatId,
                "❌ No Fancy Numbers Found"
            );
        }

        let output = "";

        sorted.forEach((x, i) => {

            output +=
`${i + 1}. +${x.number}\n`;
        });

        // telegram safe split
        const chunks = [];

        for (
            let i = 0;
            i < output.length;
            i += 4000
        ) {

            chunks.push(
                output.substring(i, i + 4000)
            );
        }

        for (const part of chunks) {

            await bot.sendMessage(
                chatId,
                `<code>${part}</code>`,
                {
                    parse_mode: "HTML"
                }
            );
        }

        fs.unlinkSync(localFile);

    } catch (err) {

        console.log(err);

        bot.sendMessage(
            chatId,
            "❌ Error Processing File"
        );
    }
});
