"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RevenuParPeriode } from "@/lib/types";
import { formatMontant } from "@/lib/format";

const ACCENT = "#d95926";
const GRID = "#2c2c2a";
const MUTED = "#898781";

export function RevenueChart({ data }: { data: RevenuParPeriode[] }) {
  const points = data.map((d) => ({ periode: d.periode, revenu: Number(d.revenu) }));

  if (points.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">Aucune donnee de revenu sur cette periode.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={ACCENT} stopOpacity={0.35} />
            <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="periode"
          stroke={MUTED}
          tick={{ fill: MUTED, fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: GRID }}
        />
        <YAxis stroke={MUTED} tick={{ fill: MUTED, fontSize: 12 }} tickLine={false} axisLine={false} width={70} />
        <Tooltip
          formatter={(value) => formatMontant(Number(value))}
          contentStyle={{
            background: "#1a1a19",
            border: "1px solid #2c2c2a",
            borderRadius: 8,
            color: "#ffffff",
            fontSize: 13,
          }}
          labelStyle={{ color: "#c3c2b7" }}
        />
        <Area
          type="monotone"
          dataKey="revenu"
          stroke={ACCENT}
          strokeWidth={2}
          fill="url(#revenueFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
