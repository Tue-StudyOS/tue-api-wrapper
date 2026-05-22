"use client";

import type React from "react";
import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  CalendarDays,
  BookOpen,
  Clapperboard,
  Mic,
  BriefcaseBusiness,
  Map,
  FolderOpen,
  FileText,
  MessageSquare,
  ClipboardList,
  GraduationCap,
  Mail,
  LibraryBig,
  Bug,
} from "lucide-react";
import { cn } from "@/lib/utils";

const baseGroups: Array<{
  label?: string;
  items: ReadonlyArray<{ href: `/${string}`; label: string; icon: React.ComponentType<{ className?: string }> }>;
}> = [
  {
    items: [{ href: "/", label: "Overview", icon: LayoutDashboard }],
  },
  {
    label: "Study",
    items: [
      { href: "/agenda", label: "Agenda", icon: Calendar },
      { href: "/courses", label: "Courses", icon: BookOpen },
      { href: "/talks", label: "Talks", icon: Mic },
      { href: "/events", label: "Events", icon: CalendarDays },
      { href: "/archive", label: "Archive", icon: Clapperboard },
      { href: "/career", label: "Career", icon: BriefcaseBusiness },
      { href: "/campus", label: "Campus", icon: Map },
      { href: "/moodle", label: "Moodle", icon: LibraryBig },
    ],
  },
  {
    label: "Workspace",
    items: [
      { href: "/spaces", label: "Spaces", icon: FolderOpen },
      { href: "/tasks", label: "Tasks", icon: ClipboardList },
      { href: "/mail", label: "Inbox", icon: Mail },
    ],
  },
  {
    label: "Records",
    items: [
      { href: "/progress", label: "Progress", icon: GraduationCap },
      { href: "/documents", label: "Documents", icon: FileText },
    ],
  },
  {
    label: "Tools",
    items: [
      { href: "/assistant", label: "Assistant", icon: MessageSquare },
    ],
  },
] as const;

export function PortalNav({ feedbackEnabled }: { feedbackEnabled: boolean }) {
  const pathname = usePathname();
  const groups = feedbackEnabled
    ? baseGroups.map((group) => group.label === "Tools"
      ? { ...group, items: [...group.items, { href: "/feedback", label: "Feedback", icon: Bug }] }
      : group)
    : baseGroups;

  return (
    <nav className="flex flex-col gap-3" aria-label="Primary">
      {groups.map((group, i) => (
        <div key={i} className="flex flex-col gap-0.5">
          {group.label ? (
            <p className="px-3 pt-1 pb-0.5 text-[0.6rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground/60">
              {group.label}
            </p>
          ) : null}
          {group.items.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === item.href
                : pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href as Route}
                className={cn(
                  "flex items-center gap-2.5 py-1.5 rounded-md text-sm transition-colors duration-100 border-l-2 pl-[10px] pr-3",
                  isActive
                    ? "border-[--tue-red] bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "border-transparent text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"
                )}
              >
                <Icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}
