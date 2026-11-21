import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath, URL } from 'url';
import { Buffer } from 'buffer';
import * as path from 'path';

// Helper: compute CRC-32 (IEEE) using a lookup table
function makeCrcTable(): Uint32Array {
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[i] = c >>> 0;
  }
  return table;
}
const crcTable = makeCrcTable();
function crc32(buf: Buffer, start = 0, length = buf.length): number {
  let crc = 0xffffffff;
  for (let i = start; i < start + length; i++) {
    crc = crcTable[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

// Load entry.png
const imgUrl = new URL('./entry.png', import.meta.url);
const imgPath = fileURLToPath(imgUrl);
let data: Buffer;
try {
  data = readFileSync(imgPath);
} catch (e) {
  throw new Error('entry.png not found at expected location: ' + imgPath);
}

// Validate PNG signature
const signature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
if (!data.slice(0, 8).equals(signature)) {
  throw new Error('Invalid PNG signature');
}

let offset = 8;
let foundIHDR = false;
let foundIEND = false;
while (offset < data.length) {
  if (offset + 8 > data.length) {
    throw new Error('Unexpected EOF while reading chunk header');
  }
  const length = data.readUInt32BE(offset);
  const type = data.slice(offset + 4, offset + 8).toString('ascii');
  const chunkStart = offset + 8;
  const chunkEnd = chunkStart + length;
  const crcStart = chunkEnd;
  const crcEnd = crcStart + 4;
  if (crcEnd > data.length) {
    throw new Error(`Chunk ${type} extends beyond file length`);
  }
  // Verify CRC
  const computed = crc32(data, offset + 4, 4 + length);
  const stored = data.readUInt32BE(crcStart);
  if (computed !== stored) {
    throw new Error(`CRC mismatch in chunk ${type}`);
  }
  if (type === 'IHDR') {
    if (length !== 13) {
      throw new Error('IHDR chunk has invalid length');
    }
    const width = data.readUInt32BE(chunkStart);
    const height = data.readUInt32BE(chunkStart + 4);
    if (width !== 1024 || height !== 1024) {
      throw new Error(`IHDR dimensions must be 1024x1024, found ${width}x${height}`);
    }
    foundIHDR = true;
  }
  if (type === 'IEND') {
    if (length !== 0) {
      throw new Error('IEND chunk should have zero length');
    }
    foundIEND = true;
    // After IEND there should be no more data
    if (crcEnd !== data.length) {
      throw new Error('Extra data after IEND chunk');
    }
    break;
  }
  offset = crcEnd;
}
if (!foundIHDR) throw new Error('Missing IHDR chunk');
if (!foundIEND) throw new Error('Missing IEND chunk');
if (data.length > 1048576) {
  throw new Error(`PNG size ${data.length} exceeds 1,048,576 bytes limit`);
}

// Destination directory
const outDir = process.env.MAKEFUN_OUTPUT_DIR || '/output';
mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, 'entry.png');
writeFileSync(outPath, data);
console.log(`Copied entry.png to ${outPath} (${data.length} bytes)`);
