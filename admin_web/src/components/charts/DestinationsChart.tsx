"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TopDestination } from "@/lib/types";

const ACCENT = "#d95926";
const GRID = "#2c2c2a";
const MUTED = "#898781";

export function DestinationsChart({ data }: { data: TopDestination[] }) {
  if (data.length === 0) {
    return <p className="py-12 text-center text-sm text-ink-muted">Aucun appel enregistre.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis
          dataKey="destination"
          stroke={MUTED}
          tick={{ fill: MUTED, fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: GRID }}
        />
        <YAxis stroke={MUTED} tick={{ fill: MUTED, fontSize: 12 }} tickLine={false} axisLine={false} width={40} />
        <Tooltip
          cursor={{ fill: "rgba(255,255,255,0.04)" }}
          contentStyle={{
            background: "#1a1a19",
            border: "1px solid #2c2c2a",
            borderRadius: 8,
            color: "#ffffff",
            fontSize: 13,
          }}
          labelStyle={{ color: "#c3c2b7" }}
        />
        <Bar dataKey="nombre_appels" name="Appels" fill={ACCENT} radius={[4, 4, 0, 0]} maxBarSize={36} />
      </BarChart>
    </ResponsiveContainer>
  );
}
