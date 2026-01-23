"use client";

import { AssetUploader } from "@/components/assets";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function AssetUploadPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/assets">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Upload Asset</h1>
          <p className="text-muted-foreground">
            Upload a new 3D model to your library
          </p>
        </div>
      </div>

      <AssetUploader />
    </div>
  );
}
