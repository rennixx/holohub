"use client";

import { Asset } from "@/types";
import { AssetCard } from "./AssetCard";

interface AssetGridProps {
  assets: Asset[];
  isLoading?: boolean;
  onDelete?: (id: string) => void;
}

export function AssetGrid({ assets, isLoading, onDelete }: AssetGridProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="aspect-square animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  if (assets.length === 0) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center">
        <p className="text-lg font-medium">No assets found</p>
        <p className="text-sm text-muted-foreground mt-1">
          Get started by uploading your first 3D model
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {assets.map((asset) => (
        <AssetCard key={asset.id} asset={asset} onDelete={onDelete} />
      ))}
    </div>
  );
}
