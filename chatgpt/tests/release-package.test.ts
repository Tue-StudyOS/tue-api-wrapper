import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile } from "node:fs/promises";

test("release packaging rejects development URLs, placeholder origins and embedded credentials", async () => {
  // The packaging script runs with Node directly and has no runtime dependencies.
  const { releaseOrigin } = await import("../scripts/package-release.mjs");
  for (const value of ["http://plugin.example.org", "https://localhost", "https://YOUR_PRODUCTION_HOST", "https://example.com", "https://10.0.0.1", "https://user:secret@study.uni-tuebingen.de", "https://study.uni-tuebingen.de/path"]) assert.throws(() => releaseOrigin(value));
  assert.equal(releaseOrigin("https://study.uni-tuebingen.de/"), "https://study.uni-tuebingen.de");
});
test("source submission carries the requested publisher, original icon and all required cases", async () => {
  const manifest = JSON.parse(await readFile(new URL("../plugin.json", import.meta.url), "utf8"));
  const openai = manifest.extensions["com.openai"];
  assert.equal(manifest.author.name, "Sebastian Boehler");
  assert.equal(manifest.author.email, "s.boehler@student.uni-tuebingen.de");
  assert.equal(openai.review.test_cases.positive.length, 5);
  assert.equal(openai.review.test_cases.negative.length, 3);
  assert.ok(openai.interface.displayName.length <= 30);
  assert.ok(openai.interface.shortDescription.length <= 30);
  assert.match(await readFile(new URL(`../${openai.interface.logo}`, import.meta.url), "utf8"), /viewBox="0 0 256 256"/);
  for (const name of ["tuebingen-connect", "tuebingen-browser-recovery"]) assert.match(await readFile(new URL(`../skills/${name}/SKILL.md`, import.meta.url), "utf8"), /^---/);
});
