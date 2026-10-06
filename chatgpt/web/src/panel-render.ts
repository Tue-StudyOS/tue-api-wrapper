import { state } from "./widget-state.js";
import { getSchedulePanelData, getTasksPanelData, getGradesPanelData, getSpacesPanelData } from "./dashboard-data.js";
import { escapeHtml, formatDate, formatRelativeStart, formatCredits } from "./widget-format.js";
import { renderAgendaRow, renderFallbackRow, renderDetailButton, buildTaskDetail, buildMembershipDetail, buildExamDetail, buildCourseDetail } from "./widget-rows.js";

export function renderSchedulePanel(): string {
  const data = getSchedulePanelData();
  const nextItem = data.items[0];
  const rows = data.items
    .slice(0, 10)
    .map((item, index) => renderAgendaRow(item, index === 0 ? "teal" : "rose"))
    .join("") || renderFallbackRow("No upcoming Alma events found.");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Schedule</p>
          <h2>${escapeHtml(data.termLabel)}</h2>
        </div>
        <div class="widget-card-actions">
          ${data.exportUrl ? `<a class="widget-button ghost small" href="${escapeHtml(data.exportUrl)}" target="_blank" rel="noreferrer">Export</a>` : ""}
          <button class="widget-button small" data-action="refresh-panel" data-panel="schedule">Refresh</button>
        </div>
      </div>
      <div class="widget-summary">
        <div>
          <span>Next up</span>
          <strong>${escapeHtml(nextItem ? formatRelativeStart(nextItem.start) ?? formatDate(nextItem.start) : "Nothing queued")}</strong>
        </div>
        <div>
          <span>Saved semester</span>
          <strong>${formatCredits(data.currentSemesterCredits)}</strong>
        </div>
        <div>
          <span>Visible items</span>
          <strong>${data.items.length}</strong>
        </div>
      </div>
      <div class="widget-list">${rows}</div>
    </article>
  `;
}

export function renderTasksPanel(): string {
  const data = getTasksPanelData();
  const rows = data.tasks
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.item_type ?? "Task")}</p>
          </div>
          <div class="widget-row-actions">
            <span>${escapeHtml(item.end ?? item.start ?? "-")}</span>
            ${renderDetailButton(buildTaskDetail(item))}
          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No open ILIAS tasks found.");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Tasks</p>
          <h2>ILIAS due items</h2>
        </div>
        <button class="widget-button small" data-action="refresh-panel" data-panel="tasks">Refresh</button>
      </div>
      <div class="widget-list">${rows}</div>
    </article>
  `;
}

export function renderGradesPanel(): string {
  const data = getGradesPanelData();
  const rows = data.exams
    .slice(0, 16)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml([item.number, item.cp ? `${item.cp} CP` : null, item.attempt ? `Attempt ${item.attempt}` : null].filter(Boolean).join(" · ") || item.status || "No structured metadata")}</p>
          </div>
          <div class="widget-row-actions">
            <span>${escapeHtml(item.grade ?? item.status ?? "-")}</span>
            ${renderDetailButton(buildExamDetail(item))}
          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No Alma exam rows found.");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Grades</p>
          <h2>Study progress</h2>
        </div>
        <button class="widget-button small" data-action="refresh-panel" data-panel="grades">Refresh</button>
      </div>
      <div class="widget-summary">
        <div>
          <span>Saved semester</span>
          <strong>${formatCredits(data.study.currentSemesterCredits)}</strong>
        </div>
        <div>
          <span>Tracked credits</span>
          <strong>${data.study.trackedCredits}</strong>
        </div>
        <div>
          <span>Passed exams</span>
          <strong>${data.study.passedExamCount}</strong>
        </div>
        <div>
          <span>Term</span>
          <strong>${escapeHtml(data.study.selectedTerm ?? "Unknown")}</strong>
        </div>
      </div>
      <div class="widget-list">${rows}</div>
      ${data.study.message ? `<p class="widget-panel-note">${escapeHtml(data.study.message)}</p>` : ""}
    </article>
  `;
}

export function renderSpacesPanel(): string {
  const data = getSpacesPanelData();
  const rows = data.memberships
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.description ?? item.properties[0] ?? item.kind ?? "Learning space")}</p>
          </div>
          <div class="widget-row-actions">
            <span>${escapeHtml(item.kind ?? "Open")}</span>
            ${renderDetailButton(buildMembershipDetail(item))}
          </div>
        </div>
      `
    )
    .join("") || renderFallbackRow("No current ILIAS memberships found.");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Spaces</p>
          <h2>Current learning spaces</h2>
        </div>
        <button class="widget-button small" data-action="refresh-panel" data-panel="spaces">Refresh</button>
      </div>
      <div class="widget-list">${rows}</div>
    </article>
  `;
}

export function renderCoursesPanel(): string {
  const data = state.panelCache.courses;
  const rows = data?.results
    .slice(0, 8)
    .map(
      (item) => `
        <div class="widget-row compact">
          <div>
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml([item.number, item.element_type].filter(Boolean).join(" · ") || "Alma result")}</p>
          </div>
          <div class="widget-row-actions">
            ${renderDetailButton(buildCourseDetail(item))}
          </div>
        </div>
      `
    )
    .join("");

  return `
    <article class="widget-card widget-card-wide">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">Courses</p>
          <h2>Search public module descriptions</h2>
        </div>
        <button class="widget-button ghost small" data-follow-up="Suggest courses for next semester based on my study progress and current degree.">
          Ask model
        </button>
      </div>
      <form class="widget-search" data-action="search-courses">
        <input
          class="widget-input"
          type="text"
          name="courseQuery"
          aria-label="Search public Alma modules"
          placeholder="Search module descriptions"
          value="${escapeHtml(state.courseQuery)}"
        />
        <button class="widget-button small" type="submit">Search</button>
      </form>
      ${
        data
          ? `
            <p class="widget-panel-note">
              ${escapeHtml(`Showing ${data.returnedResults} result${data.returnedResults === 1 ? "" : "s"}${data.totalResults !== null ? ` of ${data.totalResults}` : ""} for "${data.query}".`)}
            </p>
          `
          : `
            <p class="widget-panel-note">
              Search public Alma module descriptions. A module description does not confirm semester availability.
            </p>
          `
      }
      <div class="widget-list">
        ${rows || renderFallbackRow(data ? "No Alma course results matched this query." : "No course search has been run yet.")}
      </div>
    </article>
  `;
}
