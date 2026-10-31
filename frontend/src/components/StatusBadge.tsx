import React from "react";

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const norm = (status || "").toLowerCase();

  let styles = "bg-slate-100 text-slate-700 border-slate-200";

  if (norm === "active" || norm === "confirmed" || norm === "paid") {
    styles = "bg-emerald-50 text-emerald-700 border-emerald-200";
  } else if (norm === "paused" || norm === "sent") {
    styles = "bg-amber-50 text-amber-700 border-amber-200";
  } else if (norm === "closed" || norm === "expired" || norm === "cancelled" || norm === "suspended") {
    styles = "bg-rose-50 text-rose-700 border-rose-200";
  } else if (norm === "draft") {
    styles = "bg-blue-50 text-blue-700 border-blue-200";
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide border ${styles}`}
    >
      {status}
    </span>
  );
};
