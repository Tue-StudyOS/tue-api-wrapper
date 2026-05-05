import { useState } from "react";

import type { DesktopRuntimeState } from "../../shared/desktop-types";
import type { DashboardData } from "../lib/dashboard-types";
import { useCampusSnapshot } from "../lib/use-campus-snapshot";
import { useCareerSearch } from "../lib/use-career-search";
import { useCourseDiscovery } from "../lib/use-course-discovery";
import { useMailSurface } from "../lib/use-mail-surface";
import { useMoodleSnapshot } from "../lib/use-moodle-snapshot";
import { AssistantPage } from "./dashboard/AssistantPage";
import { CalendarPage } from "./dashboard/CalendarPage";
import { CampusPage } from "./dashboard/CampusPage";
import { CareerPage } from "./dashboard/CareerPage";
import { CourseDetailPage } from "./dashboard/CourseDetailPage";
import { CourseDiscoveryPage } from "./dashboard/CourseDiscoveryPage";
import { DashboardNav } from "./dashboard/DashboardNav";
import { LearningPage } from "./dashboard/LearningPage";
import { MailPage } from "./dashboard/MailPage";
import { StudyPage } from "./dashboard/StudyPage";
import { TodayPage } from "./dashboard/TodayPage";
import { ToolsPage } from "./dashboard/ToolsPage";
import type { CourseDetailTarget, DashboardPageId } from "./dashboard/types";

export function DashboardScreen({
  state,
  data,
  loading,
  error,
  onRefresh,
  onRestart,
  onClearCredentials
}: {
  state: DesktopRuntimeState;
  data: DashboardData | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onRestart: () => Promise<void>;
  onClearCredentials: () => Promise<void>;
}) {
  const [activePage, setActivePage] = useState<DashboardPageId>("today");
  const [courseDetailTarget, setCourseDetailTarget] = useState<CourseDetailTarget | null>(null);
  const campus = useCampusSnapshot(state.backendUrl ?? null, activePage === "campus");
  const career = useCareerSearch(state.backendUrl ?? null, activePage === "career");
  const discovery = useCourseDiscovery(state.backendUrl ?? null, activePage === "discovery");
  const mail = useMailSurface(state.backendUrl ?? null, activePage === "mail");
  const moodle = useMoodleSnapshot(state.backendUrl ?? null, activePage === "learning");
  const changePage = (page: DashboardPageId) => {
    setCourseDetailTarget(null);
    setActivePage(page);
  };

  return (
    <div className="dashboard-shell">
      <DashboardNav
        activePage={activePage}
        data={data}
        loading={loading}
        onChange={changePage}
        onRefresh={onRefresh}
        refreshDisabled={!state.backendUrl}
      />

      {error ? <div className="panel error-panel">{error}</div> : null}

      <main className="page-surface">
        {courseDetailTarget ? (
          <CourseDetailPage
            baseUrl={state.backendUrl ?? null}
            onBack={() => setCourseDetailTarget(null)}
            target={courseDetailTarget}
          />
        ) : null}
        {!courseDetailTarget && activePage === "today" ? <TodayPage data={data} state={state} /> : null}
        {!courseDetailTarget && activePage === "calendar" ? (
          <CalendarPage data={data} onOpenCourseDetail={setCourseDetailTarget} state={state} />
        ) : null}
        {!courseDetailTarget && activePage === "learning" ? <LearningPage data={data} moodle={moodle} state={state} /> : null}
        {!courseDetailTarget && activePage === "study" ? <StudyPage data={data} state={state} /> : null}
        {!courseDetailTarget && activePage === "mail" ? (
          <MailPage
            data={data}
            inbox={mail.inbox}
            mailbox={mail.mailbox}
            mailError={mail.error}
            mailLoading={mail.loading}
            mailboxes={mail.mailboxes}
            onRefreshMail={mail.refresh}
            query={mail.query}
            setMailbox={mail.setMailbox}
            setQuery={mail.setQuery}
            setUnreadOnly={mail.setUnreadOnly}
            state={state}
            unreadOnly={mail.unreadOnly}
          />
        ) : null}
        {!courseDetailTarget && activePage === "campus" ? (
          <CampusPage
            campus={campus.data}
            campusError={campus.error}
            campusLoading={campus.loading}
            data={data}
            onRefreshCampus={campus.refresh}
            state={state}
          />
        ) : null}
        {!courseDetailTarget && activePage === "discovery" ? (
          <CourseDiscoveryPage
            data={data}
            discovery={discovery}
            discoveryError={discovery.error}
            discoveryLoading={discovery.loading}
            discoverySyncing={discovery.syncing}
            onSearchDiscovery={discovery.search}
            onOpenCourseDetail={setCourseDetailTarget}
            onSyncDiscovery={discovery.sync}
            setDiscoveryDegrees={discovery.setDegrees}
            setDiscoveryIncludePrivate={discovery.setIncludePrivate}
            setDiscoveryModuleCodes={discovery.setModuleCodes}
            setDiscoveryQuery={discovery.setQuery}
            setDiscoverySources={discovery.setSources}
            state={state}
          />
        ) : null}
        {!courseDetailTarget && activePage === "career" ? <CareerPage career={career} data={data} state={state} /> : null}
        {!courseDetailTarget && activePage === "assistant" ? <AssistantPage data={data} state={state} /> : null}
        {!courseDetailTarget && activePage === "tools" ? (
          <ToolsPage
            data={data}
            loading={loading}
            onClearCredentials={onClearCredentials}
            onRefresh={onRefresh}
            onRestart={onRestart}
            state={state}
          />
        ) : null}
      </main>
    </div>
  );
}
