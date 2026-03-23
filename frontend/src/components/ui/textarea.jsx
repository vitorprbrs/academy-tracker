import * as React from "react"
import { cn } from "@/lib/utils"

const Textarea = React.forwardRef(({ className, ...props }, ref) => (
  <textarea ref={ref}
    className={cn("flex min-h-[80px] w-full rounded-md border border-input bg-input px-3 py-2 text-sm text-foreground shadow-sm placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50 resize-y font-sans", className)}
    {...props} />
))
Textarea.displayName = "Textarea"

export { Textarea }
