"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { AssetGrid, AssetFilters, type AssetFiltersState } from "@/components/assets";
import { assetsApi, type AssetListParams } from "@/lib/api";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";

export default function AssetsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<AssetFiltersState>({});
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["assets", filters, page],
    queryFn: async () => {
      const params: AssetListParams = {
        page,
        page_size: 20,
        search: filters.search,
        category: filters.category,
        processing_status: filters.status,
        sort_by: filters.sort_by as any,
        sort_order: filters.sort_order,
      };
      return await assetsApi.list(params);
    },
  });

  const handleFilterChange = (newFilters: AssetFiltersState) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page when filters change
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">
            <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
              Asset Library
            </span>
          </h1>
          <p className="text-violet-300/70 mt-1">
            Manage your 3D models and holographic content
          </p>
        </div>
        <Button
          variant="holo-primary"
          className="shadow-lg shadow-violet-500/30"
          onClick={() => router.push("/assets/upload")}
        >
          <Plus className="mr-2 h-4 w-4" />
          Upload Asset
        </Button>
      </div>

      <AssetFilters
        filters={filters}
        onChange={handleFilterChange}
        resultCount={data?.meta.total}
      />

      <AssetGrid assets={data?.items || []} isLoading={isLoading} />
    </div>
  );
}
