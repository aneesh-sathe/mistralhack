"use client";

import { motion } from "framer-motion";

interface SuccessAnimationProps {
  size?: number;
  className?: string;
}

export default function SuccessAnimation({ size = 64, className }: SuccessAnimationProps) {
  return (
    <motion.div
      className={className}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 18 }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        aria-label="Success"
      >
        <motion.circle
          cx="32"
          cy="32"
          r="30"
          fill="#56ea99"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
        {/* Ripple ring */}
        <motion.circle
          cx="32"
          cy="32"
          r="30"
          stroke="#56ea99"
          strokeWidth="2"
          fill="none"
          initial={{ scale: 1, opacity: 0.8 }}
          animate={{ scale: 1.6, opacity: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
        />
        <motion.path
          d="M18 32L27 41L46 22"
          stroke="white"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.4, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
    </motion.div>
  );
}
