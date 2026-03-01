import type { Variants, Transition } from "framer-motion";

// Shared transitions
export const spring: Transition = { type: "spring", stiffness: 400, damping: 28 };
export const springGentle: Transition = { type: "spring", stiffness: 260, damping: 20 };
export const easeOut: Transition = { duration: 0.3, ease: "easeOut" };

// Page / section animations
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: easeOut },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1, transition: springGentle },
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.15 } },
};

export const slideFromRight: Variants = {
  hidden: { opacity: 0, x: 24 },
  visible: { opacity: 1, x: 0, transition: easeOut },
  exit: { opacity: 0, x: 24, transition: { duration: 0.2 } },
};

export const slideFromLeft: Variants = {
  hidden: { opacity: 0, x: -24 },
  visible: { opacity: 1, x: 0, transition: easeOut },
  exit: { opacity: 0, x: -24, transition: { duration: 0.2 } },
};

export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06, delayChildren: 0.05 },
  },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: easeOut },
};

export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

// Card hover props to spread onto motion components
export const cardHover = {
  whileHover: { y: -2, boxShadow: "0 8px 24px rgba(18,20,26,0.10)" },
  whileTap: { scale: 0.99, y: 0 },
};

export const toastAnimation: Variants = {
  hidden: { opacity: 0, x: 40, scale: 0.96 },
  visible: { opacity: 1, x: 0, scale: 1, transition: springGentle },
  exit: { opacity: 0, x: 40, scale: 0.95, transition: { duration: 0.2 } },
};
