import { buildPortalApiUrl } from "../../../../lib/portal-api";

export async function POST(request: Request): Promise<Response> {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ detail: "Invalid JSON payload." }, { status: 400 });
  }

  let response: Response;
  try {
    response = await fetch(buildPortalApiUrl("/api/feedback/issues"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store"
    });
  } catch {
    return Response.json(
      { detail: "Could not reach the Python backend. Start it or set PORTAL_API_BASE_URL correctly." },
      { status: 503 }
    );
  }

  const contentType = response.headers.get("content-type") ?? "text/plain";
  const text = await response.text();
  return new Response(text, { status: response.status, headers: { "content-type": contentType } });
}

