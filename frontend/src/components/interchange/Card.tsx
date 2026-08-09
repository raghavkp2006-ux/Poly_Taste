import type { Domain } from "../../tokens"

interface CardProps {
  children: React.ReactNode
  domain?: Domain
  className?: string
  style?: React.CSSProperties
  onClick?: () => void
}

export function Card({
  children,
  domain,
  className = "",
  style,
  onClick,
}: CardProps) {
  return (
    <div
      className={`bg-[#FFFFFF] dark:bg-[#18181B] transition-colors duration-150 ease-out border border-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out rounded-xl overflow-hidden transition-all duration-[100ms] ease-out ${
        onClick ? "cursor-pointer hover:shadow-[0_1px_3px_rgba(0,0,0,0.06),0_1px_2px_rgba(0,0,0,0.04)] dark:shadow-none hover:scale-[1.01]" : ""
      } ${className}`}
      style={style}
      onClick={onClick}
    >
      {children}
    </div>
  )
}
