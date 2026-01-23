"use client";

import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PlaylistCard } from "@/components/playlists";
import { playlistsApi } from "@/api";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";

export default function PlaylistsPage() {
  const router = useRouter();

  const { data, isLoading } = useQuery({
    queryKey: ["playlists"],
    queryFn: async () => {
      return await playlistsApi.list();
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Playlists</h1>
          <p className="text-muted-foreground">
            Create and manage content playlists
          </p>
        </div>
        <Button onClick={() => router.push("/playlists/new")}>
          <Plus className="mr-2 h-4 w-4" />
          New Playlist
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-6 w-3/4 rounded bg-muted mb-2" />
                <div className="h-4 w-1/2 rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((playlist) => (
            <PlaylistCard key={playlist.id} playlist={playlist} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-medium mb-2">No playlists yet</p>
            <p className="text-sm text-muted-foreground mb-4">
              Create your first playlist to start displaying content
            </p>
            <Button onClick={() => router.push("/playlists/new")}>
              <Plus className="mr-2 h-4 w-4" />
              Create Playlist
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
