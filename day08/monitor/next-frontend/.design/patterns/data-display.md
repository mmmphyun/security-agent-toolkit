# Pattern: Data Display
<!-- Derived from shadcn-ui/ui (MIT License) & wshobson/agents (MIT License) -->

Deterministic components for tabular metrics, telemetry, and structured records without artificial AI ornamentation.

## 1. High-Density Data Table with Full 4-State Coverage

Implements strict state guards satisfying Hobson's 4-State Contract: Loading Skeleton, Empty State, Error Recovery State, and Populated Records.

```tsx
import React from "react";

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  align?: "left" | "right" | "center";
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  isLoading = false,
  error = null,
  onRetry,
  emptyTitle = "No records found",
  emptyDescription = "There are no entries available for this view.",
}: DataTableProps<T>) {
  return (
    <div className="w-full border border-border rounded-card bg-surface overflow-hidden shadow-elevation-1">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm font-sans border-collapse">
          <thead>
            <tr className="border-b border-border bg-background">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`py-3 px-4 text-xs font-semibold text-muted tracking-tight ${
                    col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"
                  }`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border" aria-busy={isLoading}>
            {isLoading ? (
              // 1. Loading State (Accessible Skeleton)
              Array.from({ length: 4 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  {columns.map((col) => (
                    <td key={col.key} className="py-3 px-4">
                      <div className="h-4 w-3/4 bg-border/50 rounded-sm" />
                    </td>
                  ))}
                </tr>
              ))
            ) : error ? (
              // 2. Error State (Actionable Recovery)
              <tr role="alert">
                <td colSpan={columns.length} className="py-10 px-4 text-center">
                  <p className="text-sm font-semibold text-danger">{error}</p>
                  {onRetry && (
                    <button
                      onClick={onRetry}
                      className="mt-3 px-3 py-1.5 text-xs font-medium rounded-btn bg-surface border border-border text-foreground hover:bg-background active:scale-[0.98] transition-all"
                    >
                      Retry Request
                    </button>
                  )}
                </td>
              </tr>
            ) : data.length === 0 ? (
              // 3. Empty State (Actionable Zero-Data)
              <tr>
                <td colSpan={columns.length} className="py-12 px-4 text-center">
                  <p className="text-sm font-medium text-foreground">{emptyTitle}</p>
                  <p className="text-xs text-muted mt-1">{emptyDescription}</p>
                </td>
              </tr>
            ) : (
              // 4. Populated Records
              data.map((row, idx) => (
                <tr
                  key={row.id || idx}
                  className="hover:bg-background/50 transition-colors duration-fast"
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`py-2.5 px-4 text-foreground font-mono text-xs ${
                        col.align === "right" ? "text-right" : col.align === "center" ? "text-center" : "text-left"
                      }`}
                    >
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

## 2. Telemetry Metric Card (Anti-Cliche & Multi-Layer Depth)

Avoids decorative gradient borders, meaningless colored pills, and generic SaaS hero stats. Uses Meng To ambient depth models and clean numeric typography.

```tsx
import React from "react";

export interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: {
    value: string;
    trend: "up" | "down" | "neutral";
  };
}

export function MetricCard({ label, value, unit, delta }: MetricCardProps) {
  return (
    <div className="p-4 border border-border rounded-card bg-surface shadow-elevation-1 hover:shadow-elevation-2 transition-shadow duration-normal flex flex-col justify-between">
      <div className="text-xs font-sans text-muted tracking-tight">{label}</div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-mono font-bold text-foreground tracking-tight">
          {value}
        </span>
        {unit && <span className="text-xs font-mono text-muted">{unit}</span>}
      </div>
      {delta && (
        <div className="mt-3 flex items-center gap-1.5 text-xs font-mono">
          <span
            className={
              delta.trend === "up"
                ? "text-primary"
                : delta.trend === "down"
                ? "text-danger"
                : "text-muted"
            }
          >
            {delta.trend === "up" ? "+" : delta.trend === "down" ? "-" : ""}
            {delta.value}
          </span>
          <span className="text-muted text-[10px]">vs previous cycle</span>
        </div>
      )}
    </div>
  );
}
```
