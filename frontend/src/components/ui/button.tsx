import { ButtonHTMLAttributes } from "react";
import { clsx } from "clsx";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium",
        "bg-brand-500 text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60",
        "transition-colors",
        className
      )}
      {...props}
    />
  );
}
