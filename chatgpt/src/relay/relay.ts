import { randomUUID } from "node:crypto";
import type { RelayRequest, RelayResponse } from "./contract.js";
import { maxJsonBytes, maxRelayBytes, validateRelayRequest } from "./contract.js";
import { PortalBackendError } from "../backend-error.js";

interface Poll { deliver: (request: RelayRequest | null) => void; timer: ReturnType<typeof setTimeout>; }
interface Pending { userId: string; request: RelayRequest; delivered: boolean; resolve: (response: RelayResponse) => void; reject: (error: Error) => void; timer: ReturnType<typeof setTimeout>; }

/** Ephemeral responses only. A disconnected device cannot receive queued writes later. */
export class SidecarRelay {
  private polls = new Map<string, Poll>();
  private pending = new Map<string, Pending>();
  private seen = new Map<string, number>();
  poll(userId: string, deliver: Poll["deliver"]) {
    if (this.polls.has(userId)) throw new PortalBackendError("This device already has an active connection.");
    this.seen.set(userId, Date.now());
    for (const pending of this.pending.values()) {
      if (pending.userId === userId && !pending.delivered) {
        pending.delivered = true;
        deliver(pending.request);
        return () => {};
      }
    }
    const timer = setTimeout(() => { this.polls.delete(userId); deliver(null); }, 20_000);
    this.polls.set(userId, { deliver, timer });
    return () => {
      const poll = this.polls.get(userId);
      if (poll?.timer === timer) { clearTimeout(timer); this.polls.delete(userId); }
    };
  }
  request(userId: string, request: Omit<RelayRequest, "id">): Promise<RelayResponse> {
    validateRelayRequest(request);
    const poll = this.polls.get(userId);
    if (!poll && Date.now() - (this.seen.get(userId) ?? 0) > 25_000) {
      throw new PortalBackendError("Your local sidecar is disconnected. Start it and try again.");
    }
    const userJobs = [...this.pending.values()].filter(job => job.userId === userId).length;
    if (this.pending.size >= 100 || userJobs >= 12) throw new PortalBackendError("The study service is busy. Try again later.");
    if (request.path === "/api/alma/documents/current" &&
        [...this.pending.values()].filter(job => job.request.path === request.path).length >= 4) {
      throw new PortalBackendError("Document delivery is busy. Request a new link in a moment.");
    }
    if (poll) { this.polls.delete(userId); clearTimeout(poll.timer); }
    const id = randomUUID();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new PortalBackendError("Your device did not return a result. Check the university portal before repeating an action."));
      }, 30_000);
      this.pending.set(id, { userId, request: { ...request, id }, delivered: Boolean(poll), resolve, reject, timer });
      poll?.deliver({ ...request, id });
    });
  }
  complete(userId: string, id: string, response: RelayResponse) {
    const pending = this.pending.get(id);
    if (!pending || pending.userId !== userId || !pending.delivered) return false;
    this.pending.delete(id);
    clearTimeout(pending.timer);
    const limit = pending.request.path === "/api/alma/documents/current" ? maxRelayBytes : maxJsonBytes;
    if (response.data.length > Math.ceil(limit / 3) * 4) {
      pending.reject(new PortalBackendError("Your device returned too much data. Open the university service directly."));
      return true;
    }
    pending.resolve(response);
    return true;
  }
  close() {
    for (const poll of this.polls.values()) { clearTimeout(poll.timer); poll.deliver(null); }
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(new PortalBackendError("The connection closed. Check action status before trying again."));
    }
    this.polls.clear(); this.pending.clear(); this.seen.clear();
  }
  disconnect(userId: string) {
    const poll = this.polls.get(userId);
    if (poll) { clearTimeout(poll.timer); poll.deliver(null); this.polls.delete(userId); }
    this.seen.delete(userId);
    for (const [id, pending] of this.pending) {
      if (pending.userId !== userId) continue;
      clearTimeout(pending.timer); this.pending.delete(id);
      pending.reject(new PortalBackendError("Device disconnected. Check action status before trying again."));
    }
  }
}
