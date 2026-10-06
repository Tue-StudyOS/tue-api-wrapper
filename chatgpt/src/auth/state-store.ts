import { DatabaseSync } from "node:sqlite";
import { chmodSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { createHash, randomBytes } from "node:crypto";

export const secret = () => randomBytes(32).toString("base64url");
export const digest = (value: string) => createHash("sha256").update(value).digest("hex");

/** Small account, grant and confirmation records; university sessions stay local. */
export class StateStore {
  private db: DatabaseSync;
  constructor(path: string) {
    if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
    this.db = new DatabaseSync(path);
    if (path !== ":memory:") chmodSync(path, 0o600);
    this.db.exec(`PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;
      CREATE TABLE IF NOT EXISTS state (
        namespace TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
        expires INTEGER NOT NULL, PRIMARY KEY(namespace,key));`);
    this.prune();
  }
  put(namespace: string, key: string, value: unknown, expires: number) {
    this.db.prepare("INSERT OR REPLACE INTO state VALUES (?,?,?,?)")
      .run(namespace, key, JSON.stringify(value), expires);
  }
  get<T>(namespace: string, key: string): T | undefined {
    const row = this.db.prepare("SELECT value FROM state WHERE namespace=? AND key=? AND expires>?")
      .get(namespace, key, Date.now()) as { value: string } | undefined;
    return row ? JSON.parse(row.value) as T : undefined;
  }
  take<T>(namespace: string, key: string): T | undefined {
    const row = this.db.prepare("DELETE FROM state WHERE namespace=? AND key=? AND expires>? RETURNING value")
      .get(namespace, key, Date.now()) as { value: string } | undefined;
    return row ? JSON.parse(row.value) as T : undefined;
  }
  delete(namespace: string, key: string) {
    this.db.prepare("DELETE FROM state WHERE namespace=? AND key=?").run(namespace, key);
  }
  prune() { this.db.prepare("DELETE FROM state WHERE expires<=?").run(Date.now()); }
  close() { this.db.close(); }
}
