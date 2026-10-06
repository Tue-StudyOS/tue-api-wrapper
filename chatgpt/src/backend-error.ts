export class PortalBackendError extends Error {
  constructor(message: string) { super(message); this.name = "PortalBackendError"; }
}
