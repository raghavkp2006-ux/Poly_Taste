import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // Base — matches keyboard focus, transition, disabled
  [
    "inline-flex items-center justify-center whitespace-nowrap",
    "text-sm font-sans font-medium tracking-wide",
    "rounded-lg",
    "transition-all duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-40",
  ].join(" "),
  {
    variants: {
      variant: {
        // Indigo primary — solid glow
        default: [
          "bg-[#7C6CF0] text-white",
          "hover:bg-[#6B5AE8] hover:shadow-[0_0_24px_rgba(124,108,240,0.4)]",
          "active:scale-[0.97]",
        ].join(" "),

        // Glass secondary — frosted panel
        secondary: [
          "bg-white/5 border border-white/10 text-foreground",
          "backdrop-blur-sm",
          "hover:bg-white/10 hover:border-white/20",
          "active:scale-[0.97]",
        ].join(" "),

        // Destructive
        destructive: [
          "bg-destructive text-destructive-foreground",
          "hover:bg-destructive/85",
          "active:scale-[0.97]",
        ].join(" "),

        // Outline — hairline border, glass hover
        outline: [
          "border border-border bg-transparent text-foreground",
          "hover:bg-white/5 hover:border-white/20",
          "active:scale-[0.97]",
        ].join(" "),

        // Ghost — no border, subtle hover
        ghost: [
          "bg-transparent text-muted-foreground",
          "hover:bg-white/5 hover:text-foreground",
          "active:scale-[0.97]",
        ].join(" "),

        // Text link
        link: [
          "text-primary underline-offset-4",
          "hover:underline",
        ].join(" "),
      },
      size: {
        default: "h-10 px-5 py-2",
        sm:      "h-8 rounded-md px-3 text-xs",
        lg:      "h-12 rounded-xl px-8 text-base",
        icon:    "h-9 w-9 rounded-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size:    "default",
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
