import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CalendarDays } from "lucide-react";

import type { AlmaTimetableCourseAssignmentsPage, AlmaTimetableView } from "../lib/discovery-types";
import { formatTimetableDateLabel } from "../lib/alma-timetable-ui";
import { buildPortalApiUrl } from "../lib/portal-api";
import { AlmaTimetableActions } from "./alma-timetable-actions";
import { AlmaTimetableGrid } from "./alma-timetable-grid";

function formatCredits(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(/\.0$/, "");
}

export function AlmaTimetablePanel({
  view,
  filters,
  creditSummary
}: {
  view: AlmaTimetableView;
  filters: {
    term: string;
    week: string;
    fromDate: string;
    toDate: string;
    singleDay: string;
  };
  creditSummary?: AlmaTimetableCourseAssignmentsPage | null;
}) {
  const scheduledOccurrences = view.occurrences.filter((item) => item.status !== "cancelled");
  const pdfParams = new URLSearchParams();
  if (view.selected_term_value) {
    pdfParams.set("term", view.selected_term_value);
  }
  if (filters.week) {
    pdfParams.set("week", filters.week);
  }
  if (filters.singleDay) {
    pdfParams.set("single_day", filters.singleDay);
  }
  const canRenderPdf = view.can_print_pdf && !filters.fromDate && !filters.toDate;
  const pdfUrl = canRenderPdf ? buildPortalApiUrl(`/api/alma/timetable/pdf?${pdfParams.toString()}`) : null;

  return (
    <div className="flex flex-col gap-3">
      <Card>
        <CardHeader>
          <div>
            <CardDescription>Alma timetable controls</CardDescription>
            <CardTitle>Filter schedule by term, week, or date</CardTitle>
          </div>
          <CardAction className="col-start-1 row-start-3 w-full justify-self-stretch sm:col-start-2 sm:row-span-2 sm:row-start-1 sm:w-auto sm:justify-self-end">
            <AlmaTimetableActions
              almaUrl={view.page_url}
              initialFeedUrl={view.calendar_feed_url}
              termValue={view.selected_term_value ?? ""}
              canRefreshFeed={view.can_refresh_export_url}
              supportsPdf={view.can_print_pdf}
              pdfUrl={pdfUrl}
            />
          </CardAction>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <form method="get" action="/agenda" className="grid gap-3 rounded-[1.75rem] border border-border bg-background/80 p-4 md:grid-cols-5">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="agenda_term" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Term</label>
              <select id="agenda_term" name="term" defaultValue={filters.term || view.selected_term_value || ""} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
                {view.terms.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="agenda_week" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Week</label>
              <select id="agenda_week" name="week" defaultValue={filters.week || view.selected_week_value || ""} className="h-9 rounded-md border border-input bg-background px-3 text-sm">
                <option value="">Current view</option>
                {view.weeks.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="agenda_day" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Single day</label>
              <input id="agenda_day" name="single_day" type="date" defaultValue={filters.singleDay} className="h-9 rounded-md border border-input bg-background px-3 text-sm" />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="agenda_from" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">From</label>
              <input id="agenda_from" name="from_date" type="date" defaultValue={filters.fromDate} className="h-9 rounded-md border border-input bg-background px-3 text-sm" disabled={!view.supports_custom_range} />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="agenda_to" className="text-xs font-medium uppercase tracking-wide text-muted-foreground">To</label>
              <input id="agenda_to" name="to_date" type="date" defaultValue={filters.toDate} className="h-9 min-w-0 flex-1 rounded-md border border-input bg-background px-3 text-sm" disabled={!view.supports_custom_range} />
            </div>
            <div className="md:col-span-5 flex flex-wrap items-center justify-end gap-2">
              <a
                href="/agenda"
                className="inline-flex h-9 shrink-0 items-center justify-center whitespace-nowrap rounded-lg border border-border bg-background px-3 text-sm font-medium transition-all hover:bg-muted hover:text-foreground"
              >
                Reset
              </a>
              <Button type="submit">Apply</Button>
            </div>
          </form>

          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            {view.selected_term_label ? <Badge variant="secondary">{view.selected_term_label}</Badge> : null}
            {view.selected_week_label ? <Badge variant="outline">{view.selected_week_label}</Badge> : null}
            {view.visible_range_start ? <span>{formatTimetableDateLabel(view.visible_range_start)} to {formatTimetableDateLabel(view.visible_range_end ?? view.visible_range_start)}</span> : null}
            <span>· {scheduledOccurrences.length} items</span>
            {creditSummary ? <span>· Saved semester {formatCredits(creditSummary.total_credits)} CP</span> : null}
          </div>
          {creditSummary?.unresolved_credit_count ? (
            <p className="text-xs text-muted-foreground">
              CP metadata is still missing for {creditSummary.unresolved_credit_count} visible modules.
            </p>
          ) : null}
          {!creditSummary?.unresolved_credit_count && creditSummary ? (
            <p className="text-xs text-muted-foreground">
              Saved semester totals are reflected from the current Alma course assignments.
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="size-4 text-primary" />
            Schedule view
          </CardTitle>
          <CardDescription>Weekly blocks arranged by day and time with course-based accent colors and overlap handling.</CardDescription>
        </CardHeader>
        <CardContent>
          <AlmaTimetableGrid
            days={view.days}
            occurrences={scheduledOccurrences}
            selectedTermValue={view.selected_term_value}
          />
        </CardContent>
      </Card>
    </div>
  );
}
