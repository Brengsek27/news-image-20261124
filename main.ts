import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const entryPath = path.join(__dirname, 'entry.png');

if (!fs.existsSync(entryPath)) {
    console.error('ERROR: entry.png does not exist');
    process.exit(1);
}

const stats = fs.statSync(entryPath);
if (stats.size >= 1048576) {
    console.error(`ERROR: entry.png is ${stats.size} bytes, >= 1048576`);
    process.exit(1);
}

const buffer = fs.readFileSync(entryPath);
const pngSignature = [137, 80, 78, 71, 13, 10, 26, 10];
for (let i = 0; i < pngSignature.length; i++) {
    if (buffer[i] !== pngSignature[i]) {
        console.error('ERROR: Invalid PNG signature');
        process.exit(1);
    }
}

const width = buffer.readUInt32BE(16);
const height = buffer.readUInt32BE(20);
if (width !== 1024 || height !== 1024) {
    console.error(`ERROR: PNG dimensions are ${width}x${height}, not 1024x1024`);
    process.exit(1);
}
const outputPath = path.resolve(process.cwd(), 'output');
if (!fs.existsSync(outputPath)) {
    fs.mkdirSync(outputPath, { recursive: true });
}

const outputEntryPath = path.join(outputPath, 'entry.png');
fs.copyFileSync(entryPath, outputEntryPath);

const outputStats = fs.statSync(outputEntryPath);
console.log(`Success: Copied entry.png to ${outputEntryPath} (${outputStats.size} bytes)`);
