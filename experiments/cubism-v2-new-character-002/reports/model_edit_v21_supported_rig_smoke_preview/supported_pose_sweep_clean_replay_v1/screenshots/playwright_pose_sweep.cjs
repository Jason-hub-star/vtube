
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

function safeName(value) {
  return String(value).replace(/[^a-zA-Z0-9._-]/g, "_");
}

function hashData(data) {
  let hash = 2166136261 >>> 0;
  const step = 16;
  for (let i = 0; i < data.length; i += step) {
    hash ^= data[i];
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

async function setPose(page, parameters) {
  await page.evaluate((values) => {
    const project = window.__miniProject;
    const nextValues = {};
    for (const spec of project?.parameters || []) {
      nextValues[spec.id] = spec.default;
    }
    Object.assign(nextValues, values || {});
    if (window.__miniSetParameters) {
      window.__miniSetParameters(nextValues);
      return;
    }
    const rows = Array.from(document.querySelectorAll(".param-row"));
    for (const row of rows) {
      const input = row.querySelector("input");
      if (!input) continue;
      const paramId = row.dataset.paramId;
      if (!Object.prototype.hasOwnProperty.call(nextValues, paramId)) continue;
      input.value = String(nextValues[paramId]);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }, parameters || {});
  await page.waitForTimeout(120);
}

async function canvasMetrics(page, captureNeutral) {
  return await page.evaluate((shouldCaptureNeutral) => {
    const canvas = document.querySelector("#preview-canvas");
    const ctx = canvas.getContext("2d");
    const image = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = image.data;
    const neutral = window.__neutralCanvasData || null;
    let nonBackground = 0;
    let alphaPixels = 0;
    let diffPixels = 0;
    let totalAbsDiff = 0;
    let left = canvas.width;
    let top = canvas.height;
    let right = 0;
    let bottom = 0;
    for (let i = 0; i < data.length; i += 4) {
      const pixel = i / 4;
      const x = pixel % canvas.width;
      const y = Math.floor(pixel / canvas.width);
      const a = data[i + 3];
      if (a > 0) alphaPixels += 1;
      const isBackground =
        Math.abs(data[i] - 32) <= 2 &&
        Math.abs(data[i + 1] - 33) <= 2 &&
        Math.abs(data[i + 2] - 36) <= 2;
      if (!isBackground && a > 0) {
        nonBackground += 1;
        if (x < left) left = x;
        if (y < top) top = y;
        if (x > right) right = x;
        if (y > bottom) bottom = y;
      }
      if (neutral) {
        const dr = Math.abs(data[i] - neutral[i]);
        const dg = Math.abs(data[i + 1] - neutral[i + 1]);
        const db = Math.abs(data[i + 2] - neutral[i + 2]);
        const da = Math.abs(data[i + 3] - neutral[i + 3]);
        const diff = dr + dg + db + da;
        totalAbsDiff += diff;
        if (diff > 24) diffPixels += 1;
      }
    }
    if (shouldCaptureNeutral) {
      window.__neutralCanvasData = new Uint8ClampedArray(data);
    }
    return {
      width: canvas.width,
      height: canvas.height,
      hash: hashData(data),
      nonBackground,
      alphaPixels,
      diffPixels,
      totalAbsDiff,
      changedRatio: diffPixels / (canvas.width * canvas.height),
      contentBounds: nonBackground ? [left, top, right + 1, bottom + 1] : null,
    };

    function hashData(data) {
      let hash = 2166136261 >>> 0;
      const step = 16;
      for (let i = 0; i < data.length; i += step) {
        hash ^= data[i];
        hash = Math.imul(hash, 16777619) >>> 0;
      }
      return hash.toString(16).padStart(8, "0");
    }
  }, captureNeutral);
}

function verdictFor(poseName, metrics, neutralMetrics) {
  const messages = [];
  if (metrics.nonBackground < 1000) messages.push("canvas appears blank");
  if (!metrics.contentBounds) messages.push("content bounds missing");
  if (metrics.contentBounds) {
    const [left, top, right, bottom] = metrics.contentBounds;
    const margin = Math.max(metrics.width, metrics.height) * 0.02;
    if (left < -margin || top < -margin || right > metrics.width + margin || bottom > metrics.height + margin) {
      messages.push("content bounds exceed canvas");
    }
  }
  if (neutralMetrics && neutralMetrics.nonBackground > 0) {
    const alphaRatio = metrics.nonBackground / neutralMetrics.nonBackground;
    if (alphaRatio < 0.65) messages.push("visible content dropped too much");
  }
  if (poseName !== "neutral" && metrics.changedRatio < 0.0002) {
    messages.push("pose barely differs from neutral");
  }
  if (messages.some((item) => item.includes("blank") || item.includes("exceed"))) return { verdict: "FAIL", messages };
  if (messages.length) return { verdict: "REVISE", messages };
  return { verdict: "PASS", messages };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const viewport of config.viewports) {
      const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
      page.on("console", (message) => {
        if (message.type() === "error") console.error(`[browser:${viewport.name}] ${message.text()}`);
      });
      await page.goto(config.url, { waitUntil: "networkidle" });
      await page.waitForSelector("#preview-canvas");
      await page.evaluate(async () => {
        window.__miniProject = await fetch("/api/project").then((response) => response.json());
      });
      if (config.showOverlays) {
        for (const label of ["Mesh", "Deformers"]) {
          const button = page.getByRole("button", { name: label });
          if (await button.count()) await button.first().click();
        }
      }

      let neutralMetrics = null;
      const viewportResults = [];
      for (const pose of config.poses) {
        await setPose(page, pose.parameters);
        const metrics = await canvasMetrics(page, pose.name === "neutral");
        if (pose.name === "neutral") {
          neutralMetrics = { ...metrics };
        }
        const screenshot = path.join(config.outDir, `${safeName(viewport.name)}_${safeName(pose.name)}.png`);
        const scored = verdictFor(pose.name, metrics, neutralMetrics);
        if (config.captureElement === "canvas") {
          await page.locator("#preview-canvas").screenshot({ path: screenshot });
        } else {
          await page.screenshot({ path: screenshot, fullPage: true });
        }
        viewportResults.push({
          pose: pose.name,
          parameters: pose.parameters,
          screenshot,
          metrics,
          verdict: scored.verdict,
          messages: scored.messages,
        });
      }
      await page.close();
      results.push({ viewport, poses: viewportResults });
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: true, results }, null, 2));
})().catch((error) => {
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: false, error: String(error.stack || error) }, null, 2));
  process.exit(1);
});
