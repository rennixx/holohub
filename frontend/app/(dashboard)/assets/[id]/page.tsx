"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThreeDPreview } from "@/components/assets";
import { assetsApi } from "@/api";
import { formatDistanceToNow } from "date-fns";
import { ArrowLeft, Edit, Trash2, HardDrive, Clock, Package } from "lucide-react";
import Link from "next/link";
import { Asset, ProcessingStatus } from "@/types";
import { cn } from "@/lib/utils/cn";
import { toast } from "sonner";

const statusColors: Record<ProcessingStatus, string> = {
  [ProcessingStatus.PENDING]: "bg-yellow-500",
  [ProcessingStatus.PROCESSING]: "bg-blue-500",
  [ProcessingStatus.COMPLETED]: "bg-green-500",
  [ProcessingStatus.FAILED]: "bg-red-500",
};

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const assetId = params.id as string;

  const { data: asset, isLoading, refetch } = useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => assetsApi.get(assetId),
    enabled: !!assetId,
  });

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this asset?")) return;

    try {
      await assetsApi.delete(assetId);
      toast.success("Asset deleted successfully");
      router.push("/assets");
    } catch (error) {
      toast.error("Failed to delete asset");
    }
  };

  const handleReprocess = async () => {
    try {
      await assetsApi.reprocess(assetId);
      toast.success("Asset reprocessing started");
      refetch();
    } catch (error) {
      toast.error("Failed to reprocess asset");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
          <p className="mt-2 text-sm text-muted-foreground">Loading asset...</p>
        </div>
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-lg font-medium">Asset not found</p>
          <Link href="/assets">
            <Button className="mt-4">Back to Assets</Button>
          </Link>
        </div>
      </div>
    );
  }

  const fileUrl = `${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.file_path}`;
  const fileSize = (asset.file_size / 1024 / 1024).toFixed(2);
  const thumbnailUrl = asset.outputs?.thumbnail?.file_path
    ? `${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.outputs.thumbnail.file_path}`
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/assets">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{asset.title}</h1>
            <p className="text-muted-foreground">
              Added {formatDistanceToNow(new Date(asset.created_at), { addSuffix: true })}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href={`/assets/${asset.id}/edit`}>
            <Button variant="outline">
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </Link>
          {asset.processing_status === ProcessingStatus.FAILED && (
            <Button variant="outline" onClick={handleReprocess}>
              Reprocess
            </Button>
          )}
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* 3D Preview */}
        <Card>
          <CardContent className="p-0">
            <div className="aspect-square">
              {asset.processing_status === ProcessingStatus.COMPLETED && asset.outputs?.optimized_glb ? (
                <ThreeDPreview src={`${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.outputs.optimized_glb.file_path}`} />
              ) : (
                <div className="flex items-center justify-center h-full bg-muted">
                  <div className="text-center">
                    <Badge className={cn("mb-2", statusColors[asset.processing_status])}>
                      {asset.processing_status}
                    </Badge>
                    <p className="text-sm text-muted-foreground">
                      {asset.processing_status === ProcessingStatus.PROCESSING
                        ? "Your 3D model is being processed..."
                        : asset.processing_status === ProcessingStatus.FAILED
                        ? asset.processing_error || "Processing failed"
                        : "Waiting to be processed..."}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Details */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Asset Details</CardTitle>
              <CardDescription>Information about this 3D model</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Category</p>
                  <p className="font-medium capitalize">{asset.category}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <Badge className={cn("text-white", statusColors[asset.processing_status])}>
                    {asset.processing_status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">File Size</p>
                  <p className="font-medium flex items-center gap-1">
                    <HardDrive className="h-4 w-4" />
                    {fileSize} MB
                  </p>
                </div>
                {asset.duration && (
                  <div>
                    <p className="text-sm text-muted-foreground">Duration</p>
                    <p className="font-medium flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {Math.floor(asset.duration / 60)}:{(asset.duration % 60).toString().padStart(2, "0")}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-muted-foreground">MIME Type</p>
                  <p className="font-medium text-sm">{asset.mime_type}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">SHA-256</p>
                  <p className="font-medium text-xs font-mono">{asset.sha256_hash.slice(0, 16)}...</p>
                </div>
              </div>

              {asset.description && (
                <div>
                  <p className="text-sm text-muted-foreground">Description</p>
                  <p className="text-sm">{asset.description}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Geometry Stats */}
          {asset.geometry_stats && (
            <Card>
              <CardHeader>
                <CardTitle>Geometry Stats</CardTitle>
                <CardDescription>Model statistics after processing</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Polygons</p>
                    <p className="font-medium">{asset.geometry_stats.polygon_count.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Vertices</p>
                    <p className="font-medium">{asset.geometry_stats.vertex_count.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Textures</p>
                    <p className="font-medium">{asset.geometry_stats.texture_count}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Materials</p>
                    <p className="font-medium">{asset.geometry_stats.material_count}</p>
                  </div>
                  {asset.geometry_stats.animation_count !== undefined && (
                    <div>
                      <p className="text-sm text-muted-foreground">Animations</p>
                      <p className="font-medium">{asset.geometry_stats.animation_count}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Outputs */}
          {asset.outputs && (
            <Card>
              <CardHeader>
                <CardTitle>Processed Outputs</CardTitle>
                <CardDescription>Generated files from processing</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {asset.outputs.optimized_glb && (
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <Package className="h-5 w-5 text-primary" />
                      <div>
                        <p className="font-medium">Optimized GLB</p>
                        <p className="text-xs text-muted-foreground">
                          {(asset.outputs.optimized_glb.file_size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <Button size="sm" variant="outline" asChild>
                      <a
                        href={`${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.outputs.optimized_glb.file_path}`}
                        download
                      >
                        Download
                      </a>
                    </Button>
                  </div>
                )}

                {asset.outputs.draco_compressed && (
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <Package className="h-5 w-5 text-green-500" />
                      <div>
                        <p className="font-medium">Draco Compressed</p>
                        <p className="text-xs text-muted-foreground">
                          {(asset.outputs.draco_compressed.file_size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <Button size="sm" variant="outline" asChild>
                      <a
                        href={`${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${asset.outputs.draco_compressed.file_path}`}
                        download
                      >
                        Download
                      </a>
                    </Button>
                  </div>
                )}

                {asset.outputs.quilts && asset.outputs.quilts.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Quilt Outputs</p>
                    {asset.outputs.quilts.map((quilt, i) => (
                      <div key={i} className="flex items-center justify-between rounded-lg border p-3">
                        <div>
                          <p className="font-medium text-sm">{quilt.resolution}</p>
                          <p className="text-xs text-muted-foreground">{quilt.format}</p>
                        </div>
                        <Button size="sm" variant="outline" asChild>
                          <a
                            href={`${process.env.NEXT_PUBLIC_S3_ENDPOINT}/${process.env.NEXT_PUBLIC_S3_BUCKET}/${quilt.file_path}`}
                            download
                          >
                            Download
                          </a>
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
