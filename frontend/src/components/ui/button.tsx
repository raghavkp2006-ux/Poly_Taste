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
        default: [
          "bg-[#18181B] text-[#FAFAFA] dark:bg-[#FAFAFA] dark:text-[#18181B]",
          "hover:bg-[#27272A] dark:hover:bg-[#E4E4E7]",
          "shadow-sm",
          "active:scale-[0.97]",
        ].join(" "),

        secondary: [
          "bg-[#F4F4F5] text-[#18181B] dark:bg-[#27272A] dark:text-[#FAFAFA]",
          "hover:bg-[#E4E4E7] dark:hover:bg-[#3F3F46]",
          "shadow-sm",
          "active:scale-[0.97]",
        ].join(" "),

        destructive: [
          "bg-red-600 text-white hover:bg-red-700 shadow-sm",
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

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        style={style}
        ref={ref}
        {...props}
      />
    )
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
