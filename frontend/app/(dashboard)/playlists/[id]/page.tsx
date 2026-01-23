"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { playlistsApi } from "@/api";
import { formatDistanceToNow } from "date-fns";
import { ArrowLeft, Edit, Repeat, Shuffle, Clock } from "lucide-react";
import Link from "next/link";
import { Playlist } from "@/types";

export default function PlaylistDetailPage() {
  const params = useParams();
  const router = useRouter();
  const playlistId = params.id as string;

  const { data: playlist, isLoading } = useQuery({
    queryKey: ["playlist", playlistId],
    queryFn: () => playlistsApi.get(playlistId),
    enabled: !!playlistId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
          <p className="mt-2 text-sm text-muted-foreground">Loading playlist...</p>
        </div>
      </div>
    );
  }

  if (!playlist) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-lg font-medium">Playlist not found</p>
          <Link href="/playlists">
            <Button className="mt-4">Back to Playlists</Button>
          </Link>
        </div>
      </div>
    );
  }

  const itemCount = playlist.items?.length || 0;
  const totalDuration = playlist.items?.reduce((sum, item) => sum + item.duration, 0) || 0;

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/playlists">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">{playlist.name}</h1>
              {playlist.is_active ? (
                <Badge className="bg-green-500">Active</Badge>
              ) : (
                <Badge variant="outline">Inactive</Badge>
              )}
            </div>
            <p className="text-muted-foreground">
              Updated {formatDistanceToNow(new Date(playlist.updated_at), { addSuffix: true })}
            </p>
          </div>
        </div>
        <Link href={`/playlists/${playlist.id}/edit`}>
          <Button>
            <Edit className="mr-2 h-4 w-4" />
            Edit Playlist
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Playlist Info */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Playlist Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Loop Mode</span>
                <Badge variant="outline" className={playlist.loop_mode ? "" : "opacity-50"}>
                  <Repeat className="h-3 w-3 mr-1" />
                  {playlist.loop_mode ? "On" : "Off"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Shuffle Mode</span>
                <Badge variant="outline" className={playlist.shuffle_mode ? "" : "opacity-50"}>
                  <Shuffle className="h-3 w-3 mr-1" />
                  {playlist.shuffle_mode ? "On" : "Off"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Transition</span>
                <span className="text-sm font-medium capitalize">{playlist.transition_type}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Transition Duration</span>
                <span className="text-sm font-medium">{playlist.transition_duration_ms}ms</span>
              </div>
              <div className="pt-2 border-t text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Total Items</span>
                  <span className="font-medium">{itemCount}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Total Duration
                  </span>
                  <span className="font-medium">{formatDuration(totalDuration)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {playlist.schedule_config && (
            <Card>
              <CardHeader>
                <CardTitle>Schedule</CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p className="text-muted-foreground">
                  Start: {new Date(playlist.schedule_config.start_date).toLocaleDateString()}
                </p>
                {playlist.schedule_config.end_date && (
                  <p className="text-muted-foreground">
                    End: {new Date(playlist.schedule_config.end_date).toLocaleDateString()}
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Playlist Items */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Playlist Items</CardTitle>
              <CardDescription>
                {itemCount} item{itemCount !== 1 ? "s" : ""} in this playlist
              </CardDescription>
            </CardHeader>
            <CardContent>
              {itemCount === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p>No items in this playlist</p>
                  <Link href={`/playlists/${playlist.id}/edit`}>
                    <Button variant="outline" className="mt-4">
                      Add Items
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {playlist.items?.map((item, index) => (
                    <div
                      key={item.id}
                      className="flex items-center gap-3 p-3 rounded-lg border bg-card"
                    >
                      <span className="text-xs text-muted-foreground w-6 text-center">
                        #{index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{item.asset?.title || "Unknown Asset"}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{item.duration}s</span>
                          {item.asset?.category && (
                            <>
                              <span>•</span>
                              <span className="capitalize">{item.asset.category}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        {item.asset && (
                          <span>{(item.asset.file_size / 1024 / 1024).toFixed(1)} MB</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
