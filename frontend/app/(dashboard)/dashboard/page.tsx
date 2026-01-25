"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Box, Monitor, ListMusic, HardDrive } from "lucide-react";
import { organizationsApi } from "@/lib/api";
import { useOrganizationStore } from "@/lib/store";

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
    },
    {
      title: "Active Devices",
      value: stats?.total_devices || 0,
      icon: Monitor,
      description: "Devices currently online",
    },
    {
      title: "Playlists",
      value: stats?.total_playlists || 0,
      icon: ListMusic,
      description: "Active playlists",
    },
    {
      title: "Storage Used",
      value: `${((stats?.storage_usage_percent || 0) * 100).toFixed(1)}%`,
      icon: HardDrive,
      description: `${(stats?.storage_used_bytes || 0 / 1024 / 1024 / 1024).toFixed(2)} GB used`,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your organization</p>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="space-y-2">
                <div className="h-4 w-24 rounded bg-muted" />
                <div className="h-8 w-16 rounded bg-muted" />
              </CardHeader>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">{stat.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link
              href="/assets/upload"
              className="flex items-center gap-2 rounded-lg border p-3 hover:bg-accent transition-colors"
            >
              <Box className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Upload Asset</p>
                <p className="text-sm text-muted-foreground">Add a new 3D model to your library</p>
              </div>
            </Link>
            <Link
              href="/devices"
              className="flex items-center gap-2 rounded-lg border p-3 hover:bg-accent transition-colors"
            >
              <Monitor className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Manage Devices</p>
                <p className="text-sm text-muted-foreground">View and control your display fleet</p>
              </div>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
            <CardDescription>Learn how to use HoloHub</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <strong>1. Upload Assets:</strong> Add your 3D models (GLB/GLTF files) to the asset library.
            </p>
            <p>
              <strong>2. Create Playlists:</strong> Organize your assets into playlists with scheduling.
            </p>
            <p>
              <strong>3. Assign to Devices:</strong> Link playlists to your holographic displays.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
