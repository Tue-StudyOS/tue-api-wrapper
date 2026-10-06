import "./mensa-render.css";
import { escapeHtml } from "./widget-format.js";

import type { CampusCanteen, CampusFoodPlanView, CampusMenu } from "../../src/types.js";

type CallTool = <T = unknown>(name: string, args?: Record<string, unknown>) => Promise<T | null>;
type RenderResult = (result: CampusFoodPlanView | { view: "error"; message: string }) => void;

const knownCanteens = [
  { id: "611", label: "Mensa Wilhelmstrasse" },
  { id: "621", label: "Mensa Morgenstelle" },
  { id: "623", label: "Mensa Prinz Karl" },
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object");
}

export function isMensaFoodPlanView(value: unknown): value is CampusFoodPlanView {
  return Boolean(
    isRecord(value) &&
      value.view === "mensa" &&
      typeof value.date === "string" &&
      Array.isArray(value.canteens),
  );
}

function formatPlanDate(value: string): string {
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("de-DE", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function menuPhoto(menu: CampusMenu): string | null {
  return menu.photo?.medium ?? menu.photo?.thumbnail ?? menu.photo?.large ?? menu.photo?.full ?? null;
}

function menuTitle(menu: CampusMenu): string {
  return menu.menu_line ?? menu.items[0] ?? "Menu";
}

function menuDescription(menu: CampusMenu): string {
  const remainingItems = menu.items.filter((item) => item !== menu.items[0]);
  return remainingItems.join(" · ") || menu.meats.join(" · ") || "No further description returned.";
}

function priceLine(menu: CampusMenu): string {
  return [
    menu.student_price ? `Student ${menu.student_price} EUR` : null,
    menu.guest_price ? `Guest ${menu.guest_price} EUR` : null,
  ].filter(Boolean).join(" · ");
}

function tagValues(menu: CampusMenu): string[] {
  return Array.from(new Set([...menu.icons, ...menu.filters_include, ...menu.meats]))
    .map((value) => value.trim())
    .filter(Boolean)
    .slice(0, 6);
}

function renderTags(menu: CampusMenu): string {
  const tags = tagValues(menu);
  if (!tags.length) {
    return "";
  }
  return `
    <div class="mensa-tags">
      ${tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}
    </div>
  `;
}

function renderMenu(menu: CampusMenu): string {
  const photo = menuPhoto(menu);
  const price = priceLine(menu);
  return `
    <article class="mensa-menu${photo ? " has-photo" : ""}">
      ${photo ? `<img class="mensa-photo" src="${escapeHtml(photo)}" alt="" loading="lazy" />` : ""}
      <div class="mensa-menu-body">
        <div>
          <strong>${escapeHtml(menuTitle(menu))}</strong>
          <p>${escapeHtml(menuDescription(menu))}</p>
        </div>
        ${renderTags(menu)}
        ${price ? `<p class="mensa-price">${escapeHtml(price)}</p>` : ""}
      </div>
    </article>
  `;
}

function renderLinks(canteen: CampusCanteen): string {
  const links = [
    canteen.page_url ? { label: "Menu page", href: canteen.page_url } : null,
    canteen.map_url ? { label: "Map", href: canteen.map_url } : null,
  ].filter(Boolean) as Array<{ label: string; href: string }>;

  if (!links.length) {
    return "";
  }

  return `
    <div class="mensa-links">
      ${links
        .map(
          (link) => `
            <button class="widget-button ghost small" data-action="open-external" data-href="${escapeHtml(link.href)}">
              ${escapeHtml(link.label)}
            </button>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderCanteen(canteen: CampusCanteen): string {
  const menus = canteen.menus.map(renderMenu).join("");
  return `
    <section class="widget-card widget-card-wide mensa-canteen">
      <div class="widget-card-header">
        <div>
          <p class="widget-kicker">${escapeHtml(canteen.canteen_id)}</p>
          <h2>${escapeHtml(canteen.canteen)}</h2>
          ${canteen.address ? `<p>${escapeHtml(canteen.address)}</p>` : ""}
        </div>
        ${renderLinks(canteen)}
      </div>
      <div class="mensa-menu-list">
        ${menus || `<div class="widget-row compact"><strong>No matching menus returned.</strong></div>`}
      </div>
    </section>
  `;
}

function renderCanteenOptions(plan: CampusFoodPlanView): string {
  const current = new Map<string, string>(knownCanteens.map((canteen) => [canteen.id, canteen.label]));
  for (const canteen of plan.canteens) {
    current.set(canteen.canteen_id, canteen.canteen);
  }
  const selected = plan.requested_canteen_ids[0] ?? "";
  return [
    `<option value="">All canteens</option>`,
    ...Array.from(current.entries()).map(
      ([id, label]) => `<option value="${escapeHtml(id)}"${selected === id ? " selected" : ""}>${escapeHtml(label)}</option>`,
    ),
  ].join("");
}

function renderIconOptions(plan: CampusFoodPlanView): string {
  const selected = plan.requested_icons[0] ?? "";
  const values = new Set(["", "vegan", "vegetarisch", selected]);
  return Array.from(values).map((value) => {
    const label = value || "All meals";
    return `<option value="${escapeHtml(value)}"${selected === value ? " selected" : ""}>${escapeHtml(label)}</option>`;
  }).join("");
}

function renderControls(plan: CampusFoodPlanView): string {
  return `
    <form class="mensa-controls" data-mensa-filter>
      <label>
        <span>Date</span>
        <input class="widget-input" type="date" name="date" value="${escapeHtml(plan.date)}" />
      </label>
      <label>
        <span>Canteen</span>
        <select class="widget-input" name="canteenId">${renderCanteenOptions(plan)}</select>
      </label>
      <label>
        <span>Filter</span>
        <select class="widget-input" name="icon">${renderIconOptions(plan)}</select>
      </label>
      <button class="widget-button small" type="submit">Refresh</button>
    </form>
  `;
}

function renderEmptyState(plan: CampusFoodPlanView): string {
  return `
    <section class="widget-card widget-card-wide">
      <p class="widget-kicker">No menus</p>
      <h2>No published menus matched ${escapeHtml(formatPlanDate(plan.date))}</h2>
      <p>Try another date, canteen, or meal filter.</p>
    </section>
  `;
}

export function renderMensaFoodPlan(plan: CampusFoodPlanView): string {
  const canteens = plan.canteens.map(renderCanteen).join("");
  return `
    <div class="widget-stack widget-modal-stack mensa-shell">
      <header class="widget-hero">
        <div>
          <p class="widget-kicker">Mensa</p>
          <h1>${escapeHtml(formatPlanDate(plan.date))}</h1>
          <p>${escapeHtml(`${plan.matched_menu_count} matching menus across ${plan.canteens.length} Tübingen canteens`)}</p>
        </div>
      </header>
      ${renderControls(plan)}
      ${canteens || renderEmptyState(plan)}
    </div>
  `;
}

export function bindMensaFoodPlanActions(root: HTMLElement, callTool: CallTool, renderResult: RenderResult) {
  const form = root.querySelector<HTMLFormElement>("form[data-mensa-filter]");
  if (!form) {
    return;
  }

  form.onsubmit = (event) => {
    event.preventDefault();
    void submitMensaFilters(form, callTool, renderResult);
  };
}

async function submitMensaFilters(form: HTMLFormElement, callTool: CallTool, renderResult: RenderResult) {
  const data = new FormData(form);
  const args: Record<string, unknown> = {};
  const date = String(data.get("date") ?? "").trim();
  const canteenId = String(data.get("canteenId") ?? "").trim();
  const icon = String(data.get("icon") ?? "").trim();

  if (date) {
    args.date = date;
  }
  if (canteenId) {
    args.canteenIds = [canteenId];
  }
  if (icon) {
    args.icons = [icon];
  }

  const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
  if (submit?.disabled) return;
  if (submit) { submit.disabled = true; submit.textContent = "Loading…"; }
  let errorBox = form.querySelector<HTMLElement>('[role="alert"]');
  errorBox?.remove();
  try {
    const result = await callTool<unknown>("get_mensa_food_plan", args);
    if (isMensaFoodPlanView(result)) {
      renderResult(result);
      return;
    }
    const error = isRecord(result) && typeof result.error === "string" ? result.error : "The mensa tool returned an unsupported result.";
    throw new Error(error);
  } catch (error) {
    errorBox = document.createElement("p");
    errorBox.setAttribute("role", "alert");
    errorBox.textContent = error instanceof Error ? error.message : "Mensa refresh failed.";
    form.append(errorBox);
  } finally {
    if (submit) { submit.disabled = false; submit.textContent = "Refresh"; }
  }
}
