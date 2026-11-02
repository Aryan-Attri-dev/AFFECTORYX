"use client";

import React from "react";

export function Footer() {
  return (
    <footer className="border-t border-[#1a2333] bg-[#070b12] py-3 px-6 text-xs text-gray-500 font-mono flex flex-col sm:flex-row items-center justify-between gap-2 shrink-0 z-10">
      <div className="flex items-center gap-2.5">
        <span className="font-bold tracking-wider text-gray-300">AFFECTORYX</span>
        <span className="text-gray-700">•</span>
        <span className="text-gray-400">Engineering Intelligence Platform</span>
      </div>
      <div className="flex items-center gap-1.5 text-gray-400 text-[11px]">
        <span>Developed by</span>
        <span className="font-semibold text-gray-200">Aryan Attri</span>
      </div>
    </footer>
  );
}
