import assert from "node:assert/strict";
import { test } from "node:test";
import { PortalBackendError } from "../src/backend-http.js";
import { runReadTool, runWidgetTool } from "../src/tool-runtime.js";

for (const run of [runReadTool, runWidgetTool]) {
  test(`${run.name} flags backend errors`, async () => {
    const result = await run(async () => { throw new PortalBackendError("Access denied."); });
    assert.equal(result.isError, true);
    assert.match(JSON.stringify(result.content), /Access denied/);
    assert.match(JSON.stringify(result.content), /browser\/computer/);
    assert.match(JSON.stringify(result.content), /check whether it already succeeded/);
  });
  test(`${run.name} contains unexpected failures without exposing private details`, async () => {
    const result = await run(async () => { throw new TypeError("password in upstream payload"); });
    assert.equal(result.isError, true);
    assert.doesNotMatch(JSON.stringify(result), /password/);
  });
  test(`${run.name} preserves successful results`, async () => {
    assert.deepEqual(await run(async () => ({ structuredContent: { items: [] } })), { structuredContent: { items: [] } });
  });
}
