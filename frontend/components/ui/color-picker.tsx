/**
 * Color Picker Component
 *
 * A color input with preset colors and custom color selection.
 */
import * as React from "react";
import { cn } from "@/lib/utils/cn";

interface ColorPickerProps {
  value: string;
  onChange: (value: string) => void;
  presetColors?: string[];
  disabled?: boolean;
  className?: string;
}

export function ColorPicker({
  value,
  onChange,
  presetColors = [
    "#8b5cf6", // violet
    "#06b6d4", // cyan
    "#10b981", // green
    "#f59e0b", // amber
    "#ef4444", // red
    "#ec4899", // pink
    "#6366f1", // indigo
    "#14b8a6", // teal
  ],
  disabled = false,
  className,
}: ColorPickerProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      {/* Current Color Display */}
      <div
        className="h-10 w-10 rounded-lg ring-2 ring-white/20 transition-all"
        style={{ backgroundColor: value }}
      />

      {/* Color Input */}
      <input
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="h-10 w-16 cursor-pointer rounded border-0 bg-transparent p-0"
      />

      {/* Preset Colors */}
      <div className="flex gap-2 flex-wrap">
        {presetColors.map((color) => (
          <button
            key={color}
            type="button"
            onClick={() => onChange(color)}
            disabled={disabled}
            className={cn(
              "h-8 w-8 rounded-md ring-2 transition-all",
              "ring-white/20 hover:ring-white/40 hover:scale-110",
              value === color && "ring-violet-500 ring-offset-2 ring-offset-background",
              disabled && "opacity-50 cursor-not-allowed"
            )}
            style={{ backgroundColor: color }}
            title={color}
          />
        ))}
      </div>

      {/* Hex Value Display */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-950/50 border border-violet-500/30">
        <span className="text-sm text-violet-400 font-mono">{value.toUpperCase()}</span>
      </div>
    </div>
  );
}

export { ColorPicker as ColorPicker };
