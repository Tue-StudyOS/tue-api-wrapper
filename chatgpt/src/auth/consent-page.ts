export function escapeHtml(text: string) {
  return text.replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]!);
}
export function consentPage(client: string, nonce: string) {
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="stylesheet" href="/pages.css"><title>Connect Tübingen Study Hub</title><body><main><h1>Connect Tübingen Study Hub</h1>
  <p>${escapeHtml(client)} requests access to your linked study services.</p>
  <p>The connection can read study data and prepare actions. University actions require your confirmation in the plugin.</p>
  <p>Enter the link password printed by your local sidecar. Your university password stays on your device.</p>
  <form method="post" action="/connect"><input type="hidden" name="nonce" value="${escapeHtml(nonce)}">
  <label>Link password <input name="credential" type="password" autocomplete="current-password" required maxlength="128"></label>
  <button type="submit">Connect and allow access</button></form>
  <p><a href="/privacy">Privacy</a> · <a href="/support">Help connecting your device</a></p></main></body></html>`;
}
