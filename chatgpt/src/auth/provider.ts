import { randomUUID } from "node:crypto";
import type { Response } from "express";
import type { OAuthServerProvider, AuthorizationParams } from "@modelcontextprotocol/sdk/server/auth/provider.js";
import type { OAuthClientInformationFull, OAuthTokens } from "@modelcontextprotocol/sdk/shared/auth.js";
import { InvalidGrantError, InvalidTokenError, InvalidScopeError, InvalidTargetError } from "@modelcontextprotocol/sdk/server/auth/errors.js";
import { StateStore, digest, secret } from "./state-store.js";
import { consentPage } from "./consent-page.js";

export interface Grant {
  userId: string; clientId: string; scopes: string[]; resource: string; group: string;
  redirectUri?: string; challenge?: string;
  expiresAt?: number;
}
export interface LoginAttempt { client: OAuthClientInformationFull; params: AuthorizationParams & { resource: string }; }
const accessLifetime = 3600;
const refreshLifetime = 30 * 86400_000;

export class StudyOAuthProvider implements OAuthServerProvider {
  constructor(readonly store: StateStore, readonly origin: URL) {}
  get resource() { return new URL("/mcp", this.origin); }
  clientsStore = {
    getClient: async (id: string) => this.store.get<OAuthClientInformationFull>("client", id),
    registerClient: async (metadata: Omit<OAuthClientInformationFull, "client_id" | "client_id_issued_at">) => {
      const client = { ...metadata, client_id: randomUUID(), client_id_issued_at: Math.floor(Date.now() / 1000) };
      this.store.put("client", client.client_id, client, Date.now() + 90 * 86400_000);
      return client;
    },
  };
  private validateResource(resource?: URL) {
    if (resource?.href !== this.resource.href) throw new InvalidTargetError("Use this plugin's MCP resource URL.");
  }
  async authorize(client: OAuthClientInformationFull, params: AuthorizationParams, res: Response) {
    this.validateResource(params.resource);
    if (params.scopes?.some(scope => scope !== "study")) throw new InvalidScopeError("Only the study scope is supported.");
    const nonce = secret();
    this.store.put("login", digest(nonce), { client, params: { ...params, resource: this.resource.href } }, Date.now() + 600_000);
    res.cookie("study_login", nonce, { httpOnly: true, secure: this.origin.protocol === "https:", sameSite: "lax", path: "/", maxAge: 600_000 });
    res.type("html").send(consentPage(client.client_name ?? "MCP client", nonce));
  }
  completeLogin(nonce: string, credential: string): string {
    const attempt = this.store.take<LoginAttempt>("login", digest(nonce));
    const account = this.store.get<{ userId: string }>("login-secret", digest(credential));
    if (!attempt || !account) throw new InvalidGrantError("Login expired or link password is invalid. Start again.");
    const code = secret();
    const grant: Grant = {
      userId: account.userId, clientId: attempt.client.client_id, scopes: ["study"],
      resource: this.resource.href, redirectUri: attempt.params.redirectUri,
      challenge: attempt.params.codeChallenge, group: randomUUID(),
    };
    this.store.put("code", digest(code), grant, Date.now() + 60_000);
    const redirect = new URL(attempt.params.redirectUri);
    redirect.searchParams.set("code", code);
    if (attempt.params.state !== undefined) redirect.searchParams.set("state", attempt.params.state);
    return redirect.href;
  }
  private readGrant(namespace: string, value: string, client: OAuthClientInformationFull): Grant {
    const grant = this.store.get<Grant>(namespace, digest(value));
    if (!grant || grant.clientId !== client.client_id) throw new InvalidGrantError("Grant expired or invalid.");
    return grant;
  }
  async challengeForAuthorizationCode(client: OAuthClientInformationFull, code: string) {
    return this.readGrant("code", code, client).challenge!;
  }
  async exchangeAuthorizationCode(client: OAuthClientInformationFull, code: string, _verifier?: string, redirectUri?: string, resource?: URL) {
    this.validateResource(resource);
    const grant = this.readGrant("code", code, client);
    if (redirectUri !== grant.redirectUri) throw new InvalidGrantError("Redirect URI does not match.");
    this.store.take("code", digest(code));
    this.store.put("group", grant.group, true, Date.now() + refreshLifetime);
    return this.tokens(grant);
  }
  async exchangeRefreshToken(client: OAuthClientInformationFull, refresh: string, scopes?: string[], resource?: URL) {
    if (resource) this.validateResource(resource);
    const replay = this.store.get<Grant>("spent-refresh", digest(refresh));
    if (replay?.clientId === client.client_id) {
      this.store.delete("group", replay.group);
      throw new InvalidGrantError("Refresh token reuse invalidated this connection. Connect again.");
    }
    const grant = this.readGrant("refresh", refresh, client);
    if (!this.store.get("group", grant.group) || !this.store.get("user", grant.userId)) throw new InvalidGrantError("Connection was revoked.");
    if (scopes?.some(scope => !grant.scopes.includes(scope))) throw new InvalidScopeError("Scope exceeds the connection grant.");
    this.store.take("refresh", digest(refresh));
    this.store.put("spent-refresh", digest(refresh), grant, Date.now() + refreshLifetime);
    return this.tokens({ ...grant, scopes: scopes?.length ? scopes : grant.scopes });
  }
  private tokens(grant: Grant): OAuthTokens {
    const access = secret(), refresh = secret();
    const value = { ...grant, challenge: undefined, redirectUri: undefined };
    this.store.put("access", digest(access), { ...value, expiresAt: Math.floor(Date.now() / 1000) + accessLifetime }, Date.now() + accessLifetime * 1000);
    this.store.put("refresh", digest(refresh), value, Date.now() + refreshLifetime);
    return { access_token: access, refresh_token: refresh, token_type: "Bearer", expires_in: accessLifetime, scope: grant.scopes.join(" ") };
  }
  async verifyAccessToken(token: string) {
    const grant = this.store.get<Grant>("access", digest(token));
    if (!grant || grant.resource !== this.resource.href || !this.store.get("group", grant.group) || !this.store.get("user", grant.userId)) throw new InvalidTokenError("Connection expired or revoked.");
    return { token, clientId: grant.clientId, scopes: grant.scopes, expiresAt: grant.expiresAt, resource: this.resource, extra: { userId: grant.userId } };
  }
  async revokeToken(client: OAuthClientInformationFull, request: { token: string }) {
    const grant = this.store.get<Grant>("access", digest(request.token)) ?? this.store.get<Grant>("refresh", digest(request.token));
    if (grant?.clientId === client.client_id) this.store.delete("group", grant.group);
  }
}
