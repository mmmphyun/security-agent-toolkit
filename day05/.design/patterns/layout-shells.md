# Pattern: Layout Shells

Production-grade structural shells enforcing visual rhythm, responsive breakpoints, and purposeful whitespace.

## Surface Hierarchy Convention
- **Level 0 (Canvas/Base)**: `bg-background` - 최하단 페이지 캔버스 및 뷰포트 배경.
- **Level 1 (Surface/Plate)**: `bg-surface` + `border border-border/60` - 독립 컴포넌트, 사이드바, 헤더, 기본 카드 패널.
- **Level 2 (Elevated/Overlay)**: `bg-surface` + `shadow-elevation-3` - 중첩 팝오버, 다이얼로그, 플로팅 툴바.
- **규칙**: 단일 컴포넌트 개발 시 부모 캔버스는 Level 0(`bg-background`)으로 가정하며, 컴포넌트 자체 컨테이너는 Level 1(`bg-surface`)로 격리하여 명도 대비를 확보한다.

## 1. High-Density Dashboard Shell (B2B Cockpit)

A dense, non-collapsing multi-pane layout maximizing data density without visual clutter.

```tsx
import React from "react";

export interface DashboardShellProps {
  sidebar: React.ReactNode;
  header: React.ReactNode;
  children: React.ReactNode;
}

export function DashboardShell({ sidebar, header, children }: DashboardShellProps) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground antialiased font-sans">
      {/* Fixed Sticky Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-border bg-surface flex flex-col justify-between">
        <div className="flex flex-col h-full overflow-y-auto p-4 space-y-4">
          {sidebar}
        </div>
      </aside>

      {/* Main Execution View */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-14 border-b border-border bg-surface px-6 flex items-center justify-between flex-shrink-0">
          {header}
        </header>

        {/* Scrollable Work Area */}
        <main className="flex-1 overflow-y-auto p-6 bg-background space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

## 2. Asymmetric Editorial Grid (Landing / Showcase)

Avoids the standard 3-card centered generic hero. Breaks symmetry with an intentional focal anchor.

```tsx
import React from "react";

export interface EditorialHeroProps {
  tagline: string;
  title: string;
  description: string;
  action: React.ReactNode;
  showcaseVisual: React.ReactNode;
}

export function EditorialHero({
  tagline,
  title,
  description,
  action,
  showcaseVisual
}: EditorialHeroProps) {
  return (
    <section className="relative w-full max-w-7xl mx-auto px-6 py-16 md:py-24">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Editorial Text: 7 Columns */}
        <div className="lg:col-span-7 flex flex-col space-y-6">
          <span className="text-xs font-mono font-medium text-muted tracking-tight">
            {tagline}
          </span>
          <h1 className="text-4xl md:text-5xl font-display font-bold text-foreground leading-tight tracking-tight">
            {title}
          </h1>
          <p className="text-base md:text-lg text-muted max-w-xl leading-relaxed">
            {description}
          </p>
          <div className="pt-2 flex items-center gap-4">
            {action}
          </div>
        </div>

        {/* Right Anchor Showcase: 5 Columns with offset surface */}
        <div className="lg:col-span-5 relative">
          <div className="rounded-card border border-border bg-surface p-6 shadow-elevation-3 overflow-hidden">
            {showcaseVisual}
          </div>
        </div>
      </div>
    </section>
  );
}
```
