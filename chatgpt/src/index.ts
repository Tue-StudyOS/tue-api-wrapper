import { createStudyHttpApp } from "./http-app.js";
import { StateStore } from "./auth/state-store.js";

const port = Number(process.env.PORT ?? 8080);
const origin = new URL(process.env.APP_BASE_URL ?? "http://127.0.0.1:8080");
if (origin.username || origin.password || origin.pathname !== "/" || origin.search || origin.hash ||
    (origin.protocol !== "https:" && !(origin.protocol === "http:" && ["127.0.0.1", "localhost", "[::1]"].includes(origin.hostname)))) {
  throw new Error("APP_BASE_URL must be a public HTTPS origin or a loopback development origin.");
}
if (process.env.NODE_ENV === "production" && (!process.env.APP_BASE_URL || origin.protocol !== "https:")) {
  throw new Error("Production requires a public HTTPS APP_BASE_URL.");
}
const store = new StateStore(process.env.STUDY_STATE_PATH ?? "./data/study.sqlite");
const { app, relay } = createStudyHttpApp(origin, store);
const cleanup = setInterval(() => store.prune(), 300_000).unref();
const server = app.listen(port, () => console.log(`Tübingen Study Hub listening on port ${port}`));
function shutdown() {
  clearInterval(cleanup); relay.close();
  server.close(() => { store.close(); process.exit(0); });
  setTimeout(() => process.exit(1), 5000).unref();
}
process.once("SIGTERM", shutdown);
process.once("SIGINT", shutdown);
