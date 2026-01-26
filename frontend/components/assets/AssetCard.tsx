"use client";

import Link from "next/link";
import { MoreHorizontal, Clock, Box, Play, Download } from "lucide-react";
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
import { ThreeDPreviewMini } from "./ThreeDPreview";

// Map backend status to frontend ProcessingStatus
const mapStatusToProcessing = (status: string): ProcessingStatus => {
  switch (status) {
    case "ready":
    case "completed":
      return ProcessingStatus.COMPLETED;
    case "processing":
    case "uploading":
      return ProcessingStatus.PROCESSING;
    case "error":
    case "failed":
      return ProcessingStatus.FAILED;
    case "pending":
    default:
      return ProcessingStatus.PENDING;
  }
};

interface AssetCardProps {
  asset: Asset;
  onDelete?: (id: string) => void;
}

const statusColors: Record<ProcessingStatus, string> = {
  [ProcessingStatus.PENDING]: "border-amber-500/40 bg-amber-500/20 text-amber-400 shadow-lg shadow-amber-500/20",
  [ProcessingStatus.PROCESSING]: "border-cyan-500/40 bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/20 animate-pulse",
  [ProcessingStatus.COMPLETED]: "border-green-500/40 bg-green-500/20 text-green-400 shadow-lg shadow-green-500/20",
  [ProcessingStatus.FAILED]: "border-red-500/40 bg-red-500/20 text-red-400 shadow-lg shadow-red-500/20",
};

const categoryColors: Record<AssetCategory, string> = {
  [AssetCategory.SCENE]: "border-violet-500/30 text-violet-300 hover:bg-violet-500/10",
  [AssetCategory.PRODUCT]: "border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10",
  [AssetCategory.CHARACTER]: "border-green-500/30 text-green-300 hover:bg-green-500/10",
  [AssetCategory.PROP]: "border-orange-500/30 text-orange-300 hover:bg-orange-500/10",
};

export function AssetCard({ asset, onDelete }: AssetCardProps) {
  const thumbnailUrl = asset.outputs?.thumbnail?.file_path
    ? `${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.outputs.thumbnail.file_path}`
    : null;

  const fileSize = (asset.file_size / 1024 / 1024).toFixed(2);

  // Map backend status to frontend ProcessingStatus
  const displayStatus = mapStatusToProcessing(asset.processing_status);

  // Determine file URL for 3D preview
  const fileUrl = `${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.file_path}`;
  const hasProcessedOutput = asset.outputs?.optimized_glb;
  const previewUrl = hasProcessedOutput
    ? `${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.outputs.optimized_glb.file_path}`
    : fileUrl;

  // Check if this is a GLB/GLTF file that can be previewed
  const isGlbFormat = asset.mime_type?.includes("glb") || asset.mime_type?.includes("gltf");
  const canShow3D = displayStatus === ProcessingStatus.COMPLETED && isGlbFormat;

  return (
    <Card className="
      group overflow-hidden
      glass-holo rounded-xl
      hover:scale-[1.02] hover:shadow-2xl hover:shadow-violet-500/20
      hover:border-violet-400/50
      active:scale-[0.98]
      transition-all duration-300
      cursor-pointer
      relative
    ">
      <Link href={`/assets/${asset.id}`}>
        {/* Preview Area */}
        <div className="aspect-square relative overflow-hidden bg-gradient-to-br from-slate-950 to-slate-900">
          {thumbnailUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={thumbnailUrl}
              alt={asset.title}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
            />
          ) : canShow3D ? (
            <ThreeDPreviewMini src={previewUrl} />
          ) : (
            <div className="flex h-full items-center justify-center">
              <Box className="h-16 w-16 text-violet-500/30" />
            </div>
          )}

          {/* Gradient overlay on hover */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

          {/* Status Badge with Glow */}
          <div className="absolute top-3 right-3">
            <Badge className={cn(
              "text-white font-semibold shadow-lg border",
              statusColors[displayStatus],
              displayStatus === ProcessingStatus.PROCESSING && "animate-pulse"
            )}>
              {displayStatus}
            </Badge>
          </div>

          {/* Duration Badge */}
          {asset.duration && (
            <div className="absolute bottom-3 right-3 flex items-center gap-1 rounded-full bg-black/70 backdrop-blur-sm px-3 py-1 text-xs text-white border border-white/10">
              <Clock className="h-3 w-3" />
              {formatDuration(asset.duration)}
            </div>
          )}

          {/* Quick Actions Overlay */}
          <div className="absolute bottom-3 left-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <Button size="icon" variant="holo-primary" className="h-8 w-8 shadow-lg">
              <Play className="h-4 w-4" />
            </Button>
            <Button size="icon" variant="holo-secondary" className="h-8 w-8">
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Link>

      {/* Card Content */}
      <CardContent className="p-4 space-y-3">
        {/* Title & Actions */}
        <div className="flex items-start justify-between gap-2">
          <Link href={`/assets/${asset.id}`} className="flex-1 min-w-0">
            <h3 className="font-medium text-white truncate group-hover:text-violet-300 transition-colors">
              {asset.title}
            </h3>
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="holo-ghost" size="icon" className="shrink-0 h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="glass-holo border-violet-500/30"
            >
              <DropdownMenuItem asChild>
                <Link href={`/assets/${asset.id}`}>View Details</Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href={`/assets/${asset.id}/edit`}>Edit</Link>
              </DropdownMenuItem>
              {onDelete && (
                <DropdownMenuItem
                  className="text-red-400 focus:text-red-300"
                  onClick={() => onDelete(asset.id)}
                >
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Description */}
        <p className="text-sm text-violet-300/70 truncate">
          {asset.description || "No description"}
        </p>

        {/* Metadata Row */}
        <div className="flex items-center gap-2 pt-2 border-t border-violet-500/20">
          <Badge
            variant="outline"
            className={cn("border-violet-500/30", categoryColors[asset.category])}
          >
            {asset.category}
          </Badge>
          <span className="text-xs text-violet-400/70 ml-auto">{fileSize} MB</span>
        </div>
      </CardContent>

      {/* Footer */}
      <CardFooter className="px-4 pb-4 pt-0">
        <p className="text-xs text-violet-400/50">
          Added {formatDistanceToNow(new Date(asset.created_at), { addSuffix: true })}
        </p>
      </CardFooter>

      {/* Hover Glow Effect */}
      <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-violet-500/10 via-cyan-500/10 to-violet-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none blur-xl" />
    </Card>
  );
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
