import { ButtonHTMLAttributes } from "react";
import { clsx } from "clsx";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-semibold",
        "bg-brand-500 text-white shadow-[0_8px_18px_rgba(95,67,255,0.26)]",
        "transition duration-200 hover:bg-brand-700",
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none",
        className
      )}
      {...props}
    />
  );
}
