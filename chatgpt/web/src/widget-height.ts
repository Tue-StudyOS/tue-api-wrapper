export function notifyRenderedHeight(root: HTMLElement) {
  const height = Math.ceil(root.getBoundingClientRect().height);
  if (window.openai?.notifyIntrinsicHeight) {
    window.openai.notifyIntrinsicHeight(height);
  } else if (window.parent !== window) {
    window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/size-changed", params: {
      height, width: Math.ceil(root.getBoundingClientRect().width),
    } }, "*");
  }
}

export function watchRenderedHeight(root: HTMLElement) {
  const observer = new ResizeObserver(() => notifyRenderedHeight(root));
  observer.observe(root);
  window.addEventListener("pagehide", () => observer.disconnect(), { once: true });
}
