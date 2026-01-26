"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Box, Monitor, ListMusic, HardDrive, Upload, TrendingUp, TrendingDown, Play } from "lucide-react";
import { organizationsApi } from "@/lib/api";
import { useOrganizationStore } from "@/lib/store";
import { cn } from "@/lib/utils/cn";

export default function DashboardPage() {
  const { setStats } = useOrganizationStore();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["organization-stats"],
    queryFn: async () => {
      const data = await organizationsApi.getStats();
      setStats(data);
      return data;
    },
  });

  const statCards = [
    {
      title: "Total Assets",
      value: stats?.total_assets || 0,
      icon: Box,
      description: "Media files in your library",
      color: "violet",
    },
    {
      title: "Active Devices",
      value: stats?.total_devices || 0,
      icon: Monitor,
      description: "Devices currently online",
      color: "cyan",
    },
    {
      title: "Playlists",
      value: stats?.total_playlists || 0,
      icon: ListMusic,
      description: "Active playlists",
      color: "purple",
    },
    {
      title: "Storage Used",
      value: `${((stats?.storage_usage_percent || 0) * 100).toFixed(1)}%`,
      icon: HardDrive,
      description: `${((stats?.storage_used_bytes || 0) / 1024 / 1024 / 1024).toFixed(2)} GB used`,
      color: "pink",
      progress: (stats?.storage_usage_percent || 0) * 100,
    },
  ];

  const colorClasses = {
    violet: {
      bg: "bg-violet-500/20",
      border: "border-violet-500/40",
      shadow: "shadow-violet-500/20",
      text: "text-violet-400",
      iconBg: "from-violet-500/20 to-violet-500/10",
    },
    cyan: {
      bg: "bg-cyan-500/20",
      border: "border-cyan-500/40",
      shadow: "shadow-cyan-500/20",
      text: "text-cyan-400",
      iconBg: "from-cyan-500/20 to-cyan-500/10",
    },
    purple: {
      bg: "bg-purple-500/20",
      border: "border-purple-500/40",
      shadow: "shadow-purple-500/20",
      text: "text-purple-400",
      iconBg: "from-purple-500/20 to-purple-500/10",
    },
    pink: {
      bg: "bg-pink-500/20",
      border: "border-pink-500/40",
      shadow: "shadow-pink-500/20",
      text: "text-pink-400",
      iconBg: "from-pink-500/20 to-pink-500/10",
    },
  };

  return (
    <div className="space-y-8">
      {/* Hero Header with Gradient */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-violet-950/80 via-slate-950/80 to-cyan-950/80 border border-violet-500/30 p-8">
        {/* Animated background grid */}
        <div className="absolute inset-0 opacity-10">
          <div className="h-full w-full" style={{
            backgroundImage: `
              linear-gradient(rgba(139, 92, 246, 0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(139, 92, 246, 0.3) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px'
          }} />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/50 to-transparent" />

        <div className="relative z-10">
          <h1 className="text-4xl font-bold text-white mb-2">
            Welcome to HoloHub
          </h1>
          <p className="text-lg text-violet-300/70">
            Your holographic display fleet is ready
          </p>

          {/* Quick stats inline */}
          <div className="flex gap-8 mt-6">
            <div>
              <p className="text-3xl font-bold text-white">{stats?.total_devices || 0}</p>
              <p className="text-sm text-violet-400">Active Displays</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{stats?.total_assets || 0}</p>
              <p className="text-sm text-violet-400">Total Assets</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid with Enhanced Cards */}
      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="glass-holo rounded-xl h-32 skeleton-shimmer" />
          ))}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 stagger-in">
          {statCards.map((stat) => {
            const Icon = stat.icon;
            const colors = colorClasses[stat.color as keyof typeof colorClasses];

            return (
              <Card
                key={stat.title}
                className={cn(
                  "glass-holo rounded-xl p-6",
                  "hover:scale-[1.02] hover:shadow-xl hover:shadow-violet-500/20",
                  "transition-all duration-300",
                  "group"
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-violet-300 font-medium">{stat.title}</p>
                    <p className="text-3xl font-bold text-white mt-2">{stat.value}</p>
                    <p className="text-xs text-violet-400/70 mt-1">{stat.description}</p>
                  </div>

                  {/* Icon with glow */}
                  <div className={cn(
                    "p-3 rounded-lg border transition-all duration-300",
                    "group-hover:scale-110 group-hover:shadow-lg",
                    colors.bg, colors.border, colors.shadow
                  )}>
                    <Icon className={cn("h-6 w-6", colors.text)} />
                  </div>
                </div>

                {/* Progress indicator if applicable */}
                {stat.progress !== undefined && (
                  <div className="mt-4 h-1.5 bg-violet-950/50 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full transition-all duration-500"
                      style={{ width: `${stat.progress}%` }}
                    />
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Quick Actions & Getting Started */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Quick Actions - Glass cards */}
        <Card className="glass-holo rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              href="/assets/upload"
              className="flex items-center gap-3 p-3 rounded-lg border border-violet-500/20 hover:bg-violet-500/10 hover:border-violet-400/40 transition-all duration-200 group"
            >
              <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-violet-500/30 group-hover:scale-110 transition-transform">
                <Upload className="h-5 w-5 text-violet-400" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white group-hover:text-violet-300 transition-colors">Upload Asset</p>
                <p className="text-sm text-violet-400/70">Add new 3D content</p>
              </div>
            </Link>
            <Link
              href="/devices"
              className="flex items-center gap-3 p-3 rounded-lg border border-cyan-500/20 hover:bg-cyan-500/10 hover:border-cyan-400/40 transition-all duration-200 group"
            >
              <div className="p-2 rounded-lg bg-gradient-to-br from-cyan-500/20 to-violet-500/20 border border-cyan-500/30 group-hover:scale-110 transition-transform">
                <Monitor className="h-5 w-5 text-cyan-400" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white group-hover:text-cyan-300 transition-colors">Manage Devices</p>
                <p className="text-sm text-violet-400/70">View your display fleet</p>
              </div>
            </Link>
            <Link
              href="/playlists/new"
              className="flex items-center gap-3 p-3 rounded-lg border border-purple-500/20 hover:bg-purple-500/10 hover:border-purple-400/40 transition-all duration-200 group"
            >
              <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 group-hover:scale-110 transition-transform">
                <Play className="h-5 w-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white group-hover:text-purple-300 transition-colors">Create Playlist</p>
                <p className="text-sm text-violet-400/70">Schedule content</p>
              </div>
            </Link>
          </div>
        </Card>

        {/* Getting Started */}
        <Card className="glass-holo rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">Getting Started</h2>
          <CardContent className="p-0 space-y-4 text-sm">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-violet-500/30">
                1
              </div>
              <div>
                <p className="font-medium text-white">Upload Assets</p>
                <p className="text-violet-300/70">Add your 3D models (GLB/GLTF files) to the asset library.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-violet-500/30">
                2
              </div>
              <div>
                <p className="font-medium text-white">Create Playlists</p>
                <p className="text-violet-300/70">Organize your assets into playlists with scheduling options.</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-violet-500/30">
                3
              </div>
              <div>
                <p className="font-medium text-white">Assign to Devices</p>
                <p className="text-violet-300/70">Link playlists to your holographic displays.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
