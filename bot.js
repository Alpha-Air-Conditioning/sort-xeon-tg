const TelegramBot = require("node-telegram-bot-api");
const fs = require("fs");
const pdfParse = require("pdf-parse");
const mammoth = require("mammoth");

const TOKEN = process.env.BOT_TOKEN;

const bot = new TelegramBot(TOKEN, {
    polling: true
});

console.log("Bot Started...");

function extractNumbers(text) {

    const regex = /\d{8,15}/g;

    const numbers = text.match(regex) || [];

    return [...new Set(numbers)];
}

function fancyScore(number) {

    let score = 0;

    if (/(\d)\1{2,}/.test(number))
        score += 50;

    if (/1234|2345|3456|4567|5678|6789/.test(number))
        score += 40;

    if (/9876|8765|7654|6543|5432|4321/.test(number))
        score += 40;

    if (/(\d\d)\1+/.test(number))
        score += 30;

    if (/(\d)(\d)\1\2/.test(number))
        score += 20;

    return score;
}

function sortFancy(numbers) {

    let result = [];

    numbers.forEach(num => {

        const score = fancyScore(num);

        if (score > 0) {

            result.push({
                number: num,
                score
            });
        }
    });

    return result.sort((a, b) => b.score - a.score);
}

async function readFile(path, mime) {

    if (mime.includes("pdf")) {

        const data =
            await pdfParse(
                fs.readFileSync(path)
            );

        return data.text;
    }

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

    return fs.readFileSync(path, "utf8");
}

bot.on("document", async (msg) => {

    const chatId = msg.chat.id;

    const fileId = msg.document.file_id;

    const mime = msg.document.mime_type;

    await bot.sendMessage(
        chatId,
        "📥 File Received...\n⏳ Processing..."
    );

    try {

        const file =
            await bot.getFile(fileId);

        const url =
`https://api.telegram.org/file/bot${TOKEN}/${file.file_path}`;

        const response =
            await fetch(url);

        const buffer =
            Buffer.from(
                await response.arrayBuffer()
            );

        const localFile =
            `./${msg.document.file_name}`;

        fs.writeFileSync(localFile, buffer);

        const text =
            await readFile(localFile, mime);

        const numbers =
            extractNumbers(text);

        const fancy =
            sortFancy(numbers);

        if (fancy.length === 0) {

            return bot.sendMessage(
                chatId,
                "❌ No Fancy Numbers Found"
            );
        }

        let result =
            "✨ Fancy Numbers Sorted ✨\n\n";

        fancy.forEach((x, i) => {

            result +=
`${i + 1}. +${x.number}\n`;
        });

        // split long message
        const chunks = [];

        for (
            let i = 0;
            i < result.length;
            i += 4000
        ) {

            chunks.push(
                result.substring(i, i + 4000)
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
