"use client";

import Link from "next/link";
import { MoreHorizontal, Clock, Box } from "lucide-react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Asset, ProcessingStatus, AssetCategory } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils/cn";

interface AssetCardProps {
  asset: Asset;
  onDelete?: (id: string) => void;
}

const statusColors: Record<ProcessingStatus, string> = {
  [ProcessingStatus.PENDING]: "bg-yellow-500",
  [ProcessingStatus.PROCESSING]: "bg-blue-500",
  [ProcessingStatus.COMPLETED]: "bg-green-500",
  [ProcessingStatus.FAILED]: "bg-red-500",
};

const categoryColors: Record<AssetCategory, string> = {
  [AssetCategory.SCENE]: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  [AssetCategory.PRODUCT]: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  [AssetCategory.CHARACTER]: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  [AssetCategory.PROP]: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
};

export function AssetCard({ asset, onDelete }: AssetCardProps) {
  const thumbnailUrl = asset.outputs?.thumbnail?.file_path
    ? `${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.outputs.thumbnail.file_path}`
    : null;

  const fileSize = (asset.file_size / 1024 / 1024).toFixed(2);

  return (
    <Card className="group overflow-hidden hover:shadow-md transition-shadow">
      <Link href={`/assets/${asset.id}`}>
        <div className="aspect-square relative overflow-hidden bg-muted">
          {thumbnailUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={thumbnailUrl}
              alt={asset.title}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <Box className="h-16 w-16 text-muted-foreground/50" />
            </div>
          )}

          {/* Status Badge */}
          <div className="absolute top-2 right-2">
            <Badge className={cn("text-white", statusColors[asset.processing_status])}>
              {asset.processing_status}
            </Badge>
          </div>

          {/* Duration Badge */}
          {asset.duration && (
            <div className="absolute bottom-2 right-2 flex items-center gap-1 rounded bg-black/70 px-2 py-1 text-xs text-white">
              <Clock className="h-3 w-3" />
              {formatDuration(asset.duration)}
            </div>
          )}
        </div>
      </Link>

      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <Link href={`/assets/${asset.id}`}>
              <h3 className="font-medium truncate hover:underline">{asset.title}</h3>
            </Link>
            <p className="text-sm text-muted-foreground truncate">{asset.description || "No description"}</p>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="shrink-0">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Actions</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link href={`/assets/${asset.id}`}>View Details</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href={`/assets/${asset.id}/edit`}>Edit</Link>
              </DropdownMenuItem>
              {onDelete && (
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={() => onDelete(asset.id)}
                >
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex items-center gap-2 mt-2">
          <Badge variant="outline" className={categoryColors[asset.category]}>
            {asset.category}
          </Badge>
          <span className="text-xs text-muted-foreground ml-auto">{fileSize} MB</span>
        </div>
      </CardContent>

      <CardFooter className="px-4 pb-4 pt-0 text-xs text-muted-foreground">
        Added {formatDistanceToNow(new Date(asset.created_at), { addSuffix: true })}
      </CardFooter>
    </Card>
  );
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
