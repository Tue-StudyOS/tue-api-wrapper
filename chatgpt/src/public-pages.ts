import { escapeHtml } from "./auth/consent-page.js";
import publisher from "../publisher.json" with { type: "json" };
export function publicPage(path: string) {
  const support = publisher.email;
  const contact = support ? `<a href="mailto:${escapeHtml(support)}">${escapeHtml(support)}</a>` : "Support contact must be configured before deployment.";
  const pages: Record<string, [string, string]> = {
    "/": ["Tübingen Study Hub", `<p>Independent study assistant by Sebastian Boehler for University of Tübingen students. Not an official university service.</p>
      <p>View your timetable, tasks, grades, course catalogue, learning spaces, documents, university mail and mensa menus. Prepare course registrations and confirm them in the plugin.</p>
      <p>Private features require your local university API sidecar and a connected account. Your university password stays on your device.</p>`],
    "/support": ["Support", `<p>Contact Sebastian Boehler: ${contact}.</p><p>Start the local Python API on your device, then run the linked sidecar with the production service URL. Enter its link password only on this service's account connection page.</p>
      <p>If your device is offline, private data is unavailable. If an action times out, check the university portal before trying again. You can use Alma, ILIAS or Moodle directly.</p>
      <p>To disconnect and delete the account link, run the sidecar command with --disconnect. This invalidates OAuth access, device access and future private downloads.</p>`],
    "/privacy": ["Privacy", `<p>Publisher and contact: Sebastian Boehler, ${contact}.</p><p>University passwords and login cookies stay in the local Python API on your device. The relay sends requested study data and action inputs through this service to ChatGPT. University mail, grades and documents can contain personal information. Connect only your own account.</p>
      <p>The service stores an opaque account ID, hashed device and link credentials, OAuth client records and grants in SQLite. Client records expire after 90 days. Access tokens expire after one hour; refresh grants expire after 30 days. Expired records are removed within five minutes.</p>
      <p>Action confirmations expire after ten minutes. Document links are single-use and expire after two minutes. Action and download records can contain selected university resource identifiers. Portal response data stays in memory during a request and is not saved to this database.</p>
      <p>Account links remain until you disconnect your sidecar. Disconnection removes link credentials and invalidates remaining grants. Expiring action and grant records are then deleted automatically. Infrastructure backups and network logs require a deployment retention policy. Disable request bodies, access-token and download-path logging.</p>
      <p>ChatGPT processes requested data under OpenAI's applicable privacy terms. University services apply their own policies. Contact the publisher for access or deletion requests.</p>`],
    "/terms": ["Terms of use", `<p>This independent service is operated by Sebastian Boehler. Contact: ${contact}.</p><p>Use your own university account and follow the rules of each university service. University records and portal messages are authoritative. Check registration and enrolment results in the relevant portal.</p>
      <p>Service availability depends on your connected device, university systems and ChatGPT. An error or timeout does not prove a university action failed. Do not repeat an uncertain action without checking its status.</p>
      <p>You control whether to connect, request private information and confirm actions. Read and accept university agreements on the university website. Disconnect your device when you no longer want access.</p>`],
  };
  const [title, body] = pages[path] ?? pages["/"];
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/pages.css"><title>${title}</title><body><main><h1>${title}</h1>${body}<nav><a href="/">Home</a> · <a href="/support">Support</a> · <a href="/privacy">Privacy</a> · <a href="/terms">Terms</a></nav></main></body></html>`;
}
