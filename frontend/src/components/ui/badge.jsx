import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default:  "bg-primary/15 text-primary border border-primary/20",
        approved: "bg-emerald/10 text-emerald border border-emerald/20",
        passing:  "bg-emerald/10 text-emerald border border-emerald/20",
        pending:  "bg-gold/10 text-gold border border-gold/20",
        failing:  "bg-destructive/10 text-destructive border border-destructive/20",
        failed:   "bg-destructive/10 text-destructive border border-destructive/20",
        outline:  "border border-border text-muted-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
)

export function Badge({ className, variant, ...props }) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
