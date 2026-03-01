"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { staggerContainer, staggerItem } from "@/lib/animations";

export default function HomePage() {
  return (
    <section className="mx-auto max-w-6xl">
      <div className="grid gap-8 md:grid-cols-[1.05fr_1fr] md:items-center">
        {/* Hero illustration — static slanted badges, floating stars */}
        <div className="hero-illustration">
          <span className="hero-star s1">✦</span>
          <span className="hero-star s2">✦</span>
          <span className="hero-star s3">✦</span>

          <div className="hero-badge badge-a">AI First</div>
          <div className="hero-badge badge-b">Learning</div>
          <div className="hero-badge badge-c">Platform</div>
        </div>

        {/* Hero copy */}
        <motion.div
          className="space-y-5"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <motion.h1
            variants={staggerItem}
            className="text-5xl font-black leading-[1.05] text-slate-900 md:text-6xl"
          >
            LearnStral empowers you to learn anything you&apos;ve ever wanted.
          </motion.h1>

          <motion.p
            variants={staggerItem}
            className="max-w-lg text-base leading-relaxed text-slate-600"
          >
            Upload any PDF, generate clear lessons with narration and captions, and ask questions to understand faster.
          </motion.p>

          <motion.div variants={staggerItem} className="flex flex-wrap items-center gap-3">
            <Link
              href="/documents"
              className="rounded-full bg-brand-500 px-6 py-3 text-sm font-bold text-white shadow-brand-glow transition hover:bg-brand-700 hover:shadow-brand-glow-lg active:scale-95"
            >
              View Lessons
            </Link>
            <Link
              href="/contact"
              className="rounded-full border border-slate-300 bg-white px-6 py-3 text-sm font-bold text-slate-700 transition hover:border-slate-700 active:scale-95"
            >
              Contact
            </Link>
          </motion.div>

          <motion.p variants={staggerItem} className="text-xs text-slate-400">
            Press <kbd>?</kbd> anytime to see keyboard shortcuts
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
}
