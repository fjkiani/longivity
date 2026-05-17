import * as React from "react"

export interface TextProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
}

export function Lead({ children, className, ...props }: TextProps) {
  return (
    <p className={`text-xl md:text-2xl text-gray-600 font-medium leading-relaxed ${className || ""}`} {...props}>
      {children}
    </p>
  )
}

export function Highlight({
  children,
  color = "emerald",
  className,
}: {
  children: React.ReactNode;
  color?: "emerald" | "rose" | "violet" | "sky" | "indigo";
  className?: string;
}) {
  const colorClasses = {
    emerald: "decoration-emerald-500 text-gray-900",
    rose: "decoration-rose-500 text-gray-900",
    violet: "decoration-violet-500 text-gray-900",
    sky: "decoration-sky-500 text-gray-900",
    indigo: "decoration-indigo-500 text-gray-900",
  };
  return (
    <span className={`underline decoration-2 underline-offset-4 font-bold ${colorClasses[color]} ${className || ""}`}>
      {children}
    </span>
  )
}
