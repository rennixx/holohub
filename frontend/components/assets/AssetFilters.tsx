"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, X, Grid3x3, List } from "lucide-react";
import { AssetCategory, ProcessingStatus } from "@/types";
import { useUIStore } from "@/store";
import { useCallback } from "react";

export interface AssetFiltersState {
  search?: string;
  category?: string;
  status?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

interface AssetFiltersProps {
  filters: AssetFiltersState;
  onChange: (filters: AssetFiltersState) => void;
  resultCount?: number;
}

export function AssetFilters({ filters, onChange, resultCount }: AssetFiltersProps) {
  const { assetsViewMode, setAssetsViewMode } = useUIStore();

  const updateFilter = useCallback(
    (key: keyof AssetFiltersState, value: string | undefined) => {
      onChange({ ...filters, [key]: value });
    },
    [filters, onChange]
  );

  const clearFilters = () => {
    onChange({});
  };

  const hasFilters = Object.values(filters).some((v) => v !== undefined);

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:gap-2">
        {/* Search */}
        <div className="relative sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search assets..."
            value={filters.search || ""}
            onChange={(e) => updateFilter("search", e.target.value || undefined)}
            className="pl-9"
          />
        </div>

        {/* Category Filter */}
        <Select value={filters.category} onValueChange={(v) => updateFilter("category", v || undefined)}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {Object.values(AssetCategory).map((category) => (
              <SelectItem key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Status Filter */}
        <Select value={filters.status} onValueChange={(v) => updateFilter("status", v || undefined)}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            {Object.values(ProcessingStatus).map((status) => (
              <SelectItem key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Sort By */}
        <Select
          value={filters.sort_by}
          onValueChange={(v) => updateFilter("sort_by", v || undefined)}
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="created_at">Date Created</SelectItem>
            <SelectItem value="title">Name</SelectItem>
            <SelectItem value="file_size">File Size</SelectItem>
            <SelectItem value="duration">Duration</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center gap-2">
        {/* Result count */}
        {resultCount !== undefined && (
          <span className="text-sm text-muted-foreground hidden sm:inline-block">
            {resultCount} result{resultCount !== 1 ? "s" : ""}
          </span>
        )}

        {/* View mode toggle */}
        <div className="flex rounded-md border">
          <Button
            variant="ghost"
            size="icon"
            className="rounded-r-none"
            onClick={() => setAssetsViewMode("grid")}
            data-active={assetsViewMode === "grid"}
          >
            <Grid3x3 className="h-4 w-4" />
            <span className="sr-only">Grid view</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-l-none"
            onClick={() => setAssetsViewMode("list")}
            data-active={assetsViewMode === "list"}
          >
            <List className="h-4 w-4" />
            <span className="sr-only">List view</span>
          </Button>
        </div>

        {/* Clear filters */}
        {hasFilters && (
          <Button variant="ghost" size="icon" onClick={clearFilters}>
            <X className="h-4 w-4" />
            <span className="sr-only">Clear filters</span>
          </Button>
        )}
      </div>
    </div>
  );
}
