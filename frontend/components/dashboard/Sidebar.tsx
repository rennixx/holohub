"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils/cn";
import { useUIStore } from "@/lib/store";
import {
  LayoutDashboard,
  Box,
  Monitor,
  ListMusic,
  Settings,
  Users,
  CreditCard,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthStore } from "@/lib/store";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
  items?: Array<{ title: string; href: string; icon: React.ComponentType<{ className?: string }> }>;
}

const navItems: NavItem[] = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Assets",
    href: "/assets",
    icon: Box,
  },
  {
    title: "Devices",
    href: "/devices",
    icon: Monitor,
  },
  {
    title: "Playlists",
    href: "/playlists",
    icon: ListMusic,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
    items: [
      { title: "Team", href: "/settings/team", icon: Users },
      { title: "Billing", href: "/settings/billing", icon: CreditCard },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, setSidebarCollapsed } = useUIStore();
  const { user } = useAuthStore();

  const getUserInitials = () => {
    if (!user?.full_name) return "U";
    return user.full_name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div
      className={cn(
        "flex flex-col border-r transition-all duration-300 relative overflow-hidden",
        // Holographic gradient background
        "bg-gradient-to-b from-slate-950 via-slate-950 to-violet-950/30",
        // Glass effect
        "backdrop-blur-xl",
        // Border with glow
        "border-r border-violet-500/20",
        sidebarCollapsed ? "w-20" : "w-72"
      )}
    >
      {/* Animated background particles */}
      <div className="absolute inset-0 opacity-20 pointer-events-none">
        <div className="absolute top-20 left-10 w-32 h-32 bg-violet-500/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-40 right-10 w-40 h-40 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      {/* Logo/Brand */}
      <div className="relative z-10 flex h-16 items-center border-b border-violet-500/20 px-4">
        {!sidebarCollapsed && (
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="relative">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-cyan-500 shadow-lg shadow-violet-500/30 group-hover:shadow-violet-500/50 transition-shadow duration-300">
                <span className="text-xl font-bold text-white">H</span>
              </div>
              {/* Glow ring */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 opacity-0 group-hover:opacity-30 blur-xl transition-opacity duration-300" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold text-white">HoloHub</span>
              <span className="text-xs text-violet-400">Spatial CMS</span>
            </div>
          </Link>
        )}
        {sidebarCollapsed && (
          <Link href="/dashboard" className="mx-auto relative group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-cyan-500 shadow-lg">
              <span className="text-xl font-bold text-white">H</span>
            </div>
            <div className="absolute inset-0 rounded-xl bg-violet-500/30 blur-xl group-hover:opacity-50 transition-opacity" />
          </Link>
        )}
      </div>

      {/* User Profile */}
      <div className="relative z-10 border-b border-violet-500/20 p-4">
        <div className={cn(
          "flex items-center gap-3 p-2 rounded-xl transition-all duration-300",
          "hover:bg-violet-500/10 hover:border-violet-500/30",
          sidebarCollapsed && "justify-center"
        )}>
          <div className="relative">
            <Avatar className="h-10 w-10 ring-2 ring-violet-500/30">
              <AvatarImage src="" alt={user?.full_name} />
              <AvatarFallback className="bg-gradient-to-br from-violet-600 to-cyan-500 text-white text-xs font-semibold">
                {getUserInitials()}
              </AvatarFallback>
            </Avatar>
            {/* Online indicator */}
            <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 bg-green-500 rounded-full border-2 border-slate-950" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">{user?.full_name}</p>
              <p className="text-xs text-violet-400/70 truncate">{user?.email}</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <ScrollArea className="relative z-10 flex-1 px-3 py-4">
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 relative overflow-hidden",
                  isActive
                    ? "bg-gradient-to-r from-violet-600/20 to-cyan-500/20 text-white border border-violet-500/30 shadow-lg shadow-violet-500/10"
                    : "text-violet-300/70 hover:text-violet-200 hover:bg-violet-500/10",
                  sidebarCollapsed && "justify-center px-3"
                )}
              >
                {/* Active indicator glow */}
                {isActive && (
                  <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-cyan-500/10 blur-xl" />
                )}

                {/* Icon with glow on active */}
                <div className={cn(
                  "relative shrink-0",
                  isActive && "drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]"
                )}>
                  <Icon className={cn(
                    "h-5 w-5 transition-colors",
                    isActive ? "text-violet-400" : "text-violet-400/70 group-hover:text-violet-300"
                  )} />
                </div>

                {!sidebarCollapsed && (
                  <>
                    <span className="relative truncate">{item.title}</span>
                    {item.badge && (
                      <span className="ml-auto flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-cyan-500 text-xs text-white shadow-lg shadow-violet-500/30">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        {!sidebarCollapsed && (
          <div className="mt-6 pt-6 border-t border-violet-500/20">
            <Link
              href="/settings"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-violet-300/70 hover:text-violet-200 hover:bg-violet-500/10 transition-all duration-200"
            >
              <Settings className="h-5 w-5" />
              <span className="text-sm font-medium">Settings</span>
            </Link>
          </div>
        )}
      </ScrollArea>

      {/* Collapse Toggle */}
      <div className="relative z-10 border-t border-violet-500/20 p-3">
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "w-full text-violet-300/70 hover:text-violet-200 hover:bg-violet-500/10 transition-all duration-200",
            sidebarCollapsed && "px-2"
          )}
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span className="ml-2 text-sm">Collapse</span>
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
