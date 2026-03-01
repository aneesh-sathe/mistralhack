import { ButtonHTMLAttributes } from "react";
import { clsx } from "clsx";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold",
        "bg-brand-500 text-white shadow-[0_10px_18px_rgba(53,83,222,0.28)]",
        "transition duration-200 hover:-translate-y-0.5 hover:bg-brand-700",
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none",
        className
      )}
      {...props}
    />
  );
}
