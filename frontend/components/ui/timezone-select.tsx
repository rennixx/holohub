/**
 * Timezone Selector Component
 *
 * A searchable select dropdown for timezone selection with common timezones highlighted.
 */
"use client";

import * as React from "react";
import { cn } from "@/lib/utils/cn";

// Common timezones grouped by region
const TIMEZONE_GROUPS = [
  {
    label: "North America",
    timezones: [
      { value: "America/New_York", label: "Eastern Time (ET)" },
      { value: "America/Chicago", label: "Central Time (CT)" },
      { value: "America/Denver", label: "Mountain Time (MT)" },
      { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
      { value: "America/Phoenix", label: "Arizona (MST)" },
      { value: "America/Anchorage", label: "Alaska (AKST)" },
      { value: "Pacific/Honolulu", label: "Hawaii (HST)" },
    ],
  },
  {
    label: "Europe",
    timezones: [
      { value: "Europe/London", label: "London (GMT/BST)" },
      { value: "Europe/Paris", label: "Paris (CET/CEST)" },
      { value: "Europe/Berlin", label: "Berlin (CET/CEST)" },
      { value: "Europe/Madrid", label: "Madrid (CET/CEST)" },
      { value: "Europe/Rome", label: "Rome (CET/CEST)" },
      { value: "Europe/Amsterdam", label: "Amsterdam (CET/CEST)" },
      { value: "Europe/Moscow", label: "Moscow (MSK)" },
    ],
  },
  {
    label: "Asia",
    timezones: [
      { value: "Asia/Tokyo", label: "Tokyo (JST)" },
      { value: "Asia/Shanghai", label: "Shanghai (CST)" },
      { value: "Asia/Hong_Kong", label: "Hong Kong (HKT)" },
      { value: "Asia/Singapore", label: "Singapore (SGT)" },
      { value: "Asia/Seoul", label: "Seoul (KST)" },
      { value: "Asia/Dubai", label: "Dubai (GST)" },
      { value: "Asia/Kolkata", label: "India (IST)" },
    ],
  },
  {
    label: "Australia & Pacific",
    timezones: [
      { value: "Australia/Sydney", label: "Sydney (AEST/AEDT)" },
      { value: "Australia/Melbourne", label: "Melbourne (AEST/AEDT)" },
      { value: "Pacific/Auckland", label: "Auckland (NZST/NZDT)" },
    ],
  },
  {
    label: "Other",
    timezones: [
      { value: "UTC", label: "UTC (Universal Coordinated Time)" },
    ],
  },
];

interface TimezoneSelectProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  className?: string}
}

export function TimezoneSelect({ value, onChange, disabled = false, className }: TimezoneSelectProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const selectRef = React.useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Find current timezone label
  const findTimezoneLabel = (tz: string) => {
    for (const group of TIMEZONE_GROUPS) {
      const found = group.timezones.find((t) => t.value === tz);
      if (found) return found.label;
    }
    return tz;
  };

  // Filter timezones based on search
  const filteredGroups = TIMEZONE_GROUPS.map((group) => ({
    ...group,
    timezones: group.timezones.filter(
      (tz) =>
        tz.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tz.value.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter((group) => group.timezones.length > 0);

  const selectedLabel = findTimezoneLabel(value);

  return (
    <div ref={selectRef} className={cn("relative", className)}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "w-full flex items-center justify-between px-3 py-2 text-left",
          "bg-slate-950/50 border border-violet-500/30 rounded-md",
          "text-white placeholder:text-violet-400/50",
          "focus:outline-none focus:ring-2 focus:ring-violet-500/50",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "transition-all"
        )}
      >
        <span className="truncate">{selectedLabel}</span>
        <svg
          className={cn(
            "h-4 w-4 text-violet-400 transition-transform",
            isOpen && "rotate-180"
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 max-h-80 overflow-auto rounded-md bg-slate-950 border border-violet-500/30 shadow-lg">
          {/* Search Input */}
          <div className="sticky top-0 z-10 bg-slate-950 p-2 border-b border-violet-500/20">
            <input
              type="text"
              placeholder="Search timezone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-slate-900/50 border border-violet-500/30 rounded-md text-white placeholder:text-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              autoFocus
            />
          </div>

          {/* Options */}
          <div className="p-2">
            {filteredGroups.map((group) => (
              <div key={group.label} className="mb-2 last:mb-0">
                <div className="px-2 py-1 text-xs font-semibold text-violet-400 uppercase tracking-wide">
                  {group.label}
                </div>
                {group.timezones.map((tz) => (
                  <button
                    key={tz.value}
                    type="button"
                    onClick={() => {
                      onChange(tz.value);
                      setIsOpen(false);
                      setSearchQuery("");
                    }}
                    className={cn(
                      "w-full flex items-center px-2 py-1.5 text-left rounded-sm",
                      "text-sm text-violet-300 hover:bg-violet-600/20",
                      "transition-colors",
                      value === tz.value && "bg-violet-600/30 text-white font-medium"
                    )}
                  >
                    {tz.label}
                  </button>
                ))}
              </div>
            ))}

            {filteredGroups.length === 0 && (
              <div className="px-2 py-4 text-sm text-center text-violet-400/50">
                No timezones found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export { TimezoneSelect as TimezoneSelect };
