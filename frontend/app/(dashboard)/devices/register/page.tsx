"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { devicesApi } from "@/lib/api";
import { toast } from "sonner";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils/cn";

const HARDWARE_TYPES = [
  { value: "looking_glass_portrait", label: "Looking Glass Portrait" },
  { value: "looking_glass_65", label: "Looking Glass 65 inch" },
  { value: "looking_glass_32", label: "Looking Glass 32 inch" },
  { value: "looking_glass_16", label: "Looking Glass 16 inch" },
  { value: "looking_glass_8", label: "Looking Glass 8 inch" },
];

interface FormData {
  name: string;
  hardware_type: string;
  hardware_id: string;
  location_metadata: string;
  tags: string;
}

export default function RegisterDevicePage() {
  const router = useRouter();
  const [formData, setFormData] = useState<FormData>({
    name: "",
    hardware_type: "",
    hardware_id: "",
    location_metadata: "",
    tags: "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const registerMutation = useMutation({
    mutationFn: async (data: Parameters<typeof devicesApi.register>[0]) => {
      return await devicesApi.register(data);
    },
    onSuccess: (device) => {
      toast.success("Device registered successfully!");
      router.push(`/devices/${device.id}`);
    },
    onError: (error: any) => {
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error("Failed to register device");
      }
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Device name is required";
    }
    if (!formData.hardware_type) {
      newErrors.hardware_type = "Hardware type is required";
    }
    if (!formData.hardware_id.trim()) {
      newErrors.hardware_id = "Hardware ID is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Parse location_metadata as JSON if provided
    let locationMetadata: Record<string, unknown> = {};
    if (formData.location_metadata.trim()) {
      try {
        locationMetadata = JSON.parse(formData.location_metadata);
      } catch {
        toast.error("Invalid JSON format for location metadata");
        return;
      }
    }

    // Parse tags as comma-separated list
    const tags = formData.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    registerMutation.mutate({
      name: formData.name,
      hardware_type: formData.hardware_type,
      hardware_id: formData.hardware_id,
      location_metadata: locationMetadata,
      tags,
    });
  };

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/devices">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Register Device</h1>
          <p className="text-muted-foreground">
            Add a new holographic display device to your fleet
          </p>
        </div>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Device Information</CardTitle>
          <CardDescription>
            Enter the details for the device you want to register
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name Field */}
            <div className="space-y-2">
              <Label htmlFor="name">
                Device Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                placeholder="e.g., Lobby Display 1"
                value={formData.name}
                onChange={(e) => handleChange("name", e.target.value)}
                className={cn(errors.name && "border-destructive")}
                disabled={registerMutation.isPending}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </div>

            {/* Hardware Type Field */}
            <div className="space-y-2">
              <Label htmlFor="hardware_type">
                Hardware Type <span className="text-destructive">*</span>
              </Label>
              <Select
                value={formData.hardware_type}
                onValueChange={(value) => handleChange("hardware_type", value)}
                disabled={registerMutation.isPending}
              >
                <SelectTrigger
                  id="hardware_type"
                  className={cn(errors.hardware_type && "border-destructive")}
                >
                  <SelectValue placeholder="Select hardware type" />
                </SelectTrigger>
                <SelectContent>
                  {HARDWARE_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.hardware_type && (
                <p className="text-sm text-destructive">{errors.hardware_type}</p>
              )}
            </div>

            {/* Hardware ID Field */}
            <div className="space-y-2">
              <Label htmlFor="hardware_id">
                Hardware ID / Serial Number <span className="text-destructive">*</span>
              </Label>
              <Input
                id="hardware_id"
                placeholder="e.g., HP-12345-ABC"
                value={formData.hardware_id}
                onChange={(e) => handleChange("hardware_id", e.target.value)}
                className={cn(errors.hardware_id && "border-destructive")}
                disabled={registerMutation.isPending}
              />
              {errors.hardware_id && (
                <p className="text-sm text-destructive">{errors.hardware_id}</p>
              )}
              <p className="text-xs text-muted-foreground">
                The unique identifier for this device (usually found on the device label)
              </p>
            </div>

            {/* Location Metadata Field */}
            <div className="space-y-2">
              <Label htmlFor="location_metadata">Location Metadata (Optional)</Label>
              <Input
                id="location_metadata"
                placeholder='e.g., {"building": "HQ", "floor": 1, "room": "Lobby"}'
                value={formData.location_metadata}
                onChange={(e) => handleChange("location_metadata", e.target.value)}
                disabled={registerMutation.isPending}
              />
              <p className="text-xs text-muted-foreground">
                JSON format with location information (e.g., building, floor, room)
              </p>
            </div>

            {/* Tags Field */}
            <div className="space-y-2">
              <Label htmlFor="tags">Tags (Optional)</Label>
              <Input
                id="tags"
                placeholder="e.g., lobby, main entrance, promotional"
                value={formData.tags}
                onChange={(e) => handleChange("tags", e.target.value)}
                disabled={registerMutation.isPending}
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated tags for organizing and filtering devices
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex items-center gap-4">
              <Button type="submit" disabled={registerMutation.isPending}>
                {registerMutation.isPending ? "Registering..." : "Register Device"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                disabled={registerMutation.isPending}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="max-w-2xl bg-muted/50">
        <CardHeader>
          <CardTitle className="text-base">Registration Instructions</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            <strong className="text-foreground">Hardware ID:</strong> This is typically found
            on a label on the physical device or in the device settings menu.
          </p>
          <p>
            <strong className="text-foreground">Location Metadata:</strong> Use JSON format to
            store structured location data. Example: {"{"}"building": "HQ", "floor": 1{"}"}.
          </p>
          <p>
            <strong className="text-foreground">After Registration:</strong> The device will
            appear in "Pending" status until it connects to the server for the first time.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
