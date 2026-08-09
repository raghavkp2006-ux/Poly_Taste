import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { colors, inkAlpha, paperAlpha } from "../../tokens"

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
        // Removed hardcoded hex Tailwind classes from variants, handled in inline styles.
        default: [
          "hover:opacity-90 shadow-sm",
          "active:scale-[0.97]",
        ].join(" "),

        secondary: [
          "backdrop-blur-sm",
          "hover:opacity-80 shadow-sm",
          "active:scale-[0.97]",
        ].join(" "),

        destructive: [
          "hover:opacity-90 shadow-sm",
          "active:scale-[0.97]",
        ].join(" "),

        outline: [
          "border border-[#E4E4E7] dark:border-[#27272A]",
          "text-[#18181B] dark:text-[#FAFAFA]",
          "bg-transparent hover:bg-[#F4F4F5] dark:hover:bg-[#27272A]",
          "active:scale-[0.97]",
        ].join(" "),

        ghost: [
          "text-[#18181B] dark:text-[#FAFAFA]",
          "bg-transparent hover:bg-[#F4F4F5] dark:hover:bg-[#27272A]",
          "active:scale-[0.97]",
        ].join(" "),

        link: [
          "underline-offset-4",
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
  ({ className, variant, size, asChild = false, style, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"

    // Inline style overrides for variants that used hardcoded hexes in Tailwind
    let variantStyles: React.CSSProperties = {}
    if (variant === "default" || !variant) {
      variantStyles = {
        backgroundColor: colors.ink,
        color: colors.paper,
        border: `1px solid ${inkAlpha(0.1)}`,
      }
    } else if (variant === "secondary") {
      variantStyles = {
        backgroundColor: paperAlpha(0.6),
        color: colors.ink,
        border: `1px solid ${paperAlpha(0.8)}`,
      }
    } else if (variant === "destructive") {
      variantStyles = {
        backgroundColor: colors.error,
        color: colors.paper,
      }
    } else if (variant === "outline") {
      variantStyles = {}
    } else if (variant === "ghost") {
      variantStyles = {}
    }

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        style={{ ...variantStyles, ...style }}
        ref={ref}
        {...props}
      />
    )
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
