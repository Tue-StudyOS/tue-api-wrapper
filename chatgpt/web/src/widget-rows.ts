import type { AgendaItem, IliasTaskItem, IliasMembershipItem, AlmaExamRecord, DashboardPayload } from "../../src/types.js";
import type { DetailPayload, PanelCache } from "./widget-types.js";
import { escapeHtml, encodeData, formatDate, formatRelativeStart } from "./widget-format.js";

export function renderFallbackRow(message: string): string {
  return `
    <div class="widget-row compact">
      <strong>${escapeHtml(message)}</strong>
    </div>
  `;
}

export function renderDetailButton(detail: DetailPayload): string {
  return `
    <button class="widget-button ghost small" data-action="open-detail" data-detail="${encodeData(detail)}">
      Details
    </button>
  `;
}

function agendaLocation(item: AgendaItem): string | null {
  return item.room_details?.display_text ?? item.location ?? null;
}

function buildAgendaDetail(item: AgendaItem): DetailPayload {
  const room = item.room_details;
  const lines = [
    `Start: ${formatDate(item.start)}`,
    item.end ? `End: ${formatDate(item.end)}` : "End: not provided",
    item.description ? `Notes: ${item.description}` : "Notes: no extra description"
  ];
  if (room?.floor_default) {
    lines.push(`Floor: ${room.floor_default}`);
  }
  if (room?.building_default) {
    lines.push(`Building: ${room.building_default}`);
  }
  if (room?.campus_default) {
    lines.push(`Campus: ${room.campus_default}`);
  }
  return {
    title: item.summary,
    subtitle: agendaLocation(item) ?? "Alma schedule item",
    lines,
    href: room?.detail_url ?? undefined,
    hrefLabel: room?.detail_url ? "Open Alma room details" : undefined
  };
}

export function renderAgendaRow(item: AgendaItem, accent = "teal"): string {
  const relativeStart = formatRelativeStart(item.start);
  const location = agendaLocation(item);

  return `
    <div class="widget-row widget-agenda-row" data-accent="${accent}">
      <div class="widget-agenda-time">
        <strong>${escapeHtml(formatDate(item.start))}</strong>
        ${relativeStart ? `<span>${escapeHtml(relativeStart)}</span>` : ""}
      </div>
      <div class="widget-agenda-content">
        <strong>${escapeHtml(item.summary)}</strong>
        <p>${escapeHtml(location ?? "Location pending")}</p>
      </div>
      <div class="widget-row-actions">
        ${renderDetailButton(buildAgendaDetail(item))}
      </div>
    </div>
  `;
}

export function buildTaskDetail(item: IliasTaskItem): DetailPayload {
  return {
    title: item.title,
    subtitle: item.item_type ?? "ILIAS task",
    lines: [
      `Start: ${item.start ?? "-"}`,
      `End: ${item.end ?? "-"}`,
      "This item came from the authenticated ILIAS derived tasks overview."
    ],
    href: item.url,
    hrefLabel: "Open source"
  };
}

export function buildMembershipDetail(item: IliasMembershipItem): DetailPayload {
  return {
    title: item.title,
    subtitle: item.kind ?? "Learning space",
    lines: [
      item.description ?? "No description exposed by ILIAS.",
      ...item.properties
    ].filter(Boolean),
    href: item.url,
    hrefLabel: "Open source"
  };
}

export function buildExamDetail(item: AlmaExamRecord): DetailPayload {
  return {
    title: item.title,
    subtitle: item.number ?? item.kind ?? "Alma exam record",
    lines: [
      `Grade: ${item.grade ?? "-"}`,
      `Status: ${item.status ?? "-"}`,
      `Credits: ${item.cp ?? "-"}`,
      `Attempt: ${item.attempt ?? "-"}`,
      `Release date: ${item.release_date ?? "-"}`
    ]
  };
}

export function buildCourseDetail(result: NonNullable<PanelCache["courses"]>["results"][number]): DetailPayload {
  return {
    title: result.title,
    subtitle: result.number ?? result.element_type ?? "Alma module search result",
    lines: [
      `Element type: ${result.element_type ?? "-"}`,
      result.detail_url ? "A public Alma detail page is available for this result." : "No public detail URL exposed."
    ],
    href: result.detail_url ?? undefined,
    hrefLabel: result.detail_url ? "Open source" : undefined
  };
}

export function buildTalkDetail(item: DashboardPayload["talks"]["items"][number]): DetailPayload {
  return {
    title: item.title,
    subtitle: item.speaker_name ?? item.location ?? "Talk",
    lines: [
      `Time: ${formatDate(item.timestamp)}`,
      `Location: ${item.location ?? "-"}`,
      `Speaker: ${item.speaker_name ?? "-"}`,
      item.description ? `Abstract: ${item.description}` : "Abstract: not provided"
    ],
    href: item.source_url,
    hrefLabel: "Open original talk"
  };
}
