import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils/cn";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground border-violet-500/30",
        success: "border-green-500/40 bg-green-500/20 text-green-400 shadow-lg shadow-green-500/20 hover:bg-green-500/30",
        warning: "border-amber-500/40 bg-amber-500/20 text-amber-400 shadow-lg shadow-amber-500/20 hover:bg-amber-500/30",
        info: "border-cyan-500/40 bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/20 hover:bg-cyan-500/30",
        // Holographic variants
        "holo-gradient": "relative overflow-hidden bg-gradient-to-r from-violet-600 to-cyan-500 text-white font-semibold shadow-lg shadow-violet-500/30 border-transparent",
        "holo-outline": "text-violet-300 border-violet-500/30 hover:bg-violet-500/10 hover:border-violet-400/50",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
