// Rendert scene.html Bild für Bild als PNG. Aufruf: node render.js <fontsDir> <outDir> [fps] [nur-Zeiten,kommagetrennt]
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");
(async () => {
  const [fontsDir, outDir, fpsArg, only] = process.argv.slice(2);
  const fps = Number(fpsArg || 30), dur = 20;
  fs.mkdirSync(outDir, { recursive: true });
  // Seite mit Schriften in ein temporäres Verzeichnis neben die Fonts kopieren
  const work = path.resolve(outDir, "..", "page");
  fs.mkdirSync(work, { recursive: true });
  fs.copyFileSync(path.join(__dirname, "scene.html"), path.join(work, "scene.html"));
  fs.rmSync(path.join(work, "fonts"), { force: true, recursive: true });
  fs.symlinkSync(path.resolve(fontsDir), path.join(work, "fonts"));
  const browser = await chromium.launch({ args: ["--allow-file-access-from-files"] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto("file://" + path.join(work, "scene.html"));
  await page.evaluate(() => window.ready);
  const times = only ? only.split(",").map(Number) : [...Array(fps * dur).keys()].map(i => i / fps);
  for (let i = 0; i < times.length; i++) {
    const url = await page.evaluate(t => { draw(t); return document.getElementById("c").toDataURL("image/png"); }, times[i]);
    const name = only ? `t${times[i].toFixed(2)}.png` : `f${String(i).padStart(4, "0")}.png`;
    fs.writeFileSync(path.join(outDir, name), Buffer.from(url.split(",")[1], "base64"));
  }
  await browser.close();
})();
