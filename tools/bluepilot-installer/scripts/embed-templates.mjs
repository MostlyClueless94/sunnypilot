import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const templatesDir = path.join(root, "templates");
const outputPath = path.join(root, "src", "template-data.mjs");

async function encodeTemplate(filename) {
  const bytes = await readFile(path.join(templatesDir, filename));
  return bytes.toString("base64");
}

const [agnosBase64, neosBase64] = await Promise.all([
  encodeTemplate("installer_openpilot_agnos.bin"),
  encodeTemplate("installer_openpilot_neos.bin"),
]);

const output = `export const AGNOS_TEMPLATE_BASE64 = ${JSON.stringify(agnosBase64)};\nexport const NEOS_TEMPLATE_BASE64 = ${JSON.stringify(neosBase64)};\n`;

await mkdir(path.dirname(outputPath), { recursive: true });
await writeFile(outputPath, output);
