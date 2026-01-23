"use client";

import Link from "next/link";
import { MoreHorizontal, Clock, Repeat, Shuffle } from "lucide-react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Playlist } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils/cn";

interface PlaylistCardProps {
  playlist: Playlist;
  onDelete?: (id: string) => void;
}

export function PlaylistCard({ playlist, onDelete }: PlaylistCardProps) {
  const itemCount = playlist.items?.length || 0;
  const totalDuration = playlist.items?.reduce((sum, item) => sum + item.duration, 0) || 0;

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <Link href={`/playlists/${playlist.id}`}>
        <CardContent className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h3 className="font-medium truncate hover:underline">{playlist.name}</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {itemCount} item{itemCount !== 1 ? "s" : ""} • {formatDuration(totalDuration)}
              </p>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.preventDefault()}>
                <Button variant="ghost" size="icon" className="shrink-0">
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">Actions</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild>
                  <Link href={`/playlists/${playlist.id}`}>View Details</Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href={`/playlists/${playlist.id}/edit`}>Edit</Link>
                </DropdownMenuItem>
                {onDelete && (
                  <DropdownMenuItem
                    className="text-destructive"
                    onClick={() => onDelete(playlist.id)}
                  >
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2 mt-4">
            {playlist.loop_mode && (
              <Badge variant="outline" className="gap-1">
                <Repeat className="h-3 w-3" />
                Loop
              </Badge>
            )}
            {playlist.shuffle_mode && (
              <Badge variant="outline" className="gap-1">
                <Shuffle className="h-3 w-3" />
                Shuffle
              </Badge>
            )}
            {playlist.is_active ? (
              <Badge className="bg-green-500">Active</Badge>
            ) : (
              <Badge variant="outline">Inactive</Badge>
            )}
          </div>
        </CardContent>
      </Link>

      <CardFooter className="px-6 pb-6 pt-0 text-xs text-muted-foreground">
        Updated {formatDistanceToNow(new Date(playlist.updated_at), { addSuffix: true })}
      </CardFooter>
    </Card>
  );
}
