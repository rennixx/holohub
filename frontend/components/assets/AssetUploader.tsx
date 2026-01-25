"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, File } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { assetsApi } from "@/lib/api";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

interface UploadFile {
  file: File;
  id: string;
  progress: number;
  status: "pending" | "uploading" | "processing" | "completed" | "error";
  error?: string;
}

export function AssetUploader() {
  const router = useRouter();
  const [uploads, setUploads] = useState<UploadFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const glbFiles = acceptedFiles.filter((f) => f.name.endsWith(".glb") || f.name.endsWith(".gltf"));

    if (glbFiles.length === 0) {
      toast.error("Only .glb and .gltf files are supported");
      return;
    }

    if (glbFiles.length !== acceptedFiles.length) {
      toast.warning(`Filtered out ${acceptedFiles.length - glbFiles.length} non-GLB/GLTF files`);
    }

    const newUploads: UploadFile[] = glbFiles.map((file) => ({
      file,
      id: Math.random().toString(36).substring(7),
      progress: 0,
      status: "pending",
    }));

    setUploads((prev) => [...prev, ...newUploads]);
    setIsUploading(true);

    // Process uploads
    for (const upload of newUploads) {
      await processUpload(upload);
    }

    setIsUploading(false);
  }, []);

  const processUpload = async (upload: UploadFile) => {
    try {
      // Update status to uploading
      setUploads((prev) =>
        prev.map((u) => (u.id === upload.id ? { ...u, status: "uploading" as const } : u))
      );

      // Upload directly through backend (no CORS issues)
      await assetsApi.uploadDirect(
        upload.file,
        upload.file.name.replace(/\.[^/.]+$/, ""), // title without extension
        undefined, // description
        (progress) => {
          setUploads((prev) => prev.map((u) => (u.id === upload.id ? { ...u, progress } : u)));
        }
      );

      // Update status to completed
      setUploads((prev) =>
        prev.map((u) => (u.id === upload.id ? { ...u, status: "completed" as const, progress: 100 } : u))
      );

      toast.success(`${upload.file.name} uploaded successfully!`);

      // Remove completed uploads after a delay
      setTimeout(() => {
        setUploads((prev) => prev.filter((u) => u.id !== upload.id));
      }, 3000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Upload failed";
      setUploads((prev) =>
        prev.map((u) => (u.id === upload.id ? { ...u, status: "error" as const, error: errorMessage } : u))
      );
      toast.error(`${upload.file.name} failed to upload`);
    }
  };

  const removeUpload = (id: string) => {
    setUploads((prev) => prev.filter((u) => u.id !== id));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "model/gltf-binary": [".glb"],
      "model/gltf+json": [".gltf"],
    },
    disabled: isUploading,
  });

  return (
    <div className="space-y-4">
      <Card
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer",
          isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
        )}
      >
        <input {...getInputProps()} />
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <Upload className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium">
            {isDragActive ? "Drop your files here" : "Drag & drop GLB/GLTF files here"}
          </p>
          <p className="text-sm text-muted-foreground mt-1">or click to browse</p>
          <Button variant="outline" className="mt-4" disabled={isUploading}>
            Select Files
          </Button>
        </CardContent>
      </Card>

      {uploads.length > 0 && (
        <Card>
          <CardContent className="pt-6 space-y-4">
            {uploads.map((upload) => (
              <div key={upload.id} className="flex items-center gap-4">
                <File className="h-8 w-8 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{upload.file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(upload.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  {upload.status === "uploading" && (
                    <Progress value={upload.progress} className="mt-2" />
                  )}
                  {upload.status === "error" && (
                    <p className="text-sm text-destructive mt-1">{upload.error}</p>
                  )}
                  {upload.status === "processing" && (
                    <p className="text-sm text-muted-foreground mt-1">Processing...</p>
                  )}
                  {upload.status === "completed" && (
                    <p className="text-sm text-green-600 mt-1">Completed!</p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeUpload(upload.id)}
                  disabled={upload.status === "processing"}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {uploads.some((u) => u.status === "completed") && (
        <Button onClick={() => router.push("/assets")} className="w-full">
          View Assets
        </Button>
      )}
    </div>
  );
}

import { cn } from "@/lib/utils/cn";
