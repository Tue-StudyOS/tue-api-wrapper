import type { ReactNode } from "react";
import { PortalNav } from "./portal-nav";
import { ThemeToggle } from "./theme-toggle";
import { MobileNav } from "./mobile-nav";
import { Separator } from "@/components/ui/separator";

function SidebarContents() {
  return (
    <>
      <div className="px-3 pb-4 flex items-center gap-2.5">
        <div className="w-1 h-8 rounded-full bg-[--tue-red] shrink-0" />
        <div>
          <p className="text-[0.65rem] font-semibold tracking-[0.1em] uppercase text-muted-foreground">
            Universität Tübingen
          </p>
          <h1 className="text-[0.95rem] font-semibold tracking-tight text-foreground mt-0.5">
            Study Hub
          </h1>
        </div>
      </div>
      <Separator className="mb-2" />
      <PortalNav />
      <div className="mt-auto pt-2">
        <Separator className="mb-2" />
        <ThemeToggle />
      </div>
    </>
  );
}

export async function AppShell({
  title,
  children,
}: {
  title: string;
  kicker?: string;
  children: ReactNode;
}) {
  return (
    <div className="grid lg:grid-cols-[248px_minmax(0,1fr)] min-h-screen">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex sticky top-0 h-screen flex-col gap-1 py-4 px-3 border-r border-sidebar-border bg-sidebar overflow-y-auto">
        <SidebarContents />
      </aside>

      <main className="flex flex-col min-h-screen overflow-y-auto">
        {/* Mobile sticky header */}
        <div className="lg:hidden sticky top-0 z-20 flex items-center gap-3 px-4 py-3 bg-sidebar border-b border-sidebar-border">
          <MobileNav>
            <SidebarContents />
          </MobileNav>
          <span className="text-sm font-semibold text-foreground truncate">{title}</span>
        </div>

        {/* Main content */}
        <div className="flex flex-col gap-5 p-5 lg:p-7">
          <div className="hidden lg:flex items-baseline justify-between gap-4">
            <h2 className="text-xl font-semibold tracking-tight text-foreground">{title}</h2>
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}
