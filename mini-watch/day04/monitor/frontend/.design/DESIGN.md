# System Design Principles

## Taste Configuration (1-10 Scale)
<!-- Architecture derived from leonxlnx/taste-skill (MIT License, Copyright (c) 2025 Leon Linz) -->
<!-- Tune these knobs to govern visual output without ambiguous prose -->
- `DESIGN_VARIANCE`: 3   # 1 (Strict/Symmetric) ~ 10 (Asymmetric/Experimental)
- `VISUAL_DENSITY`: 9    # 1 (Airy/Minimalist) ~ 10 (Information-Dense Cockpit)
- `MOTION_INTENSITY`: 2  # 1 (Static/Subtle) ~ 10 (Cinematic Spring Physics)

## 1. Single Source of Truth
- All visual values (colors, spacing, typography, radii) MUST be derived from `reference/tokens/`.
- Do NOT inject arbitrary hex codes or ad-hoc pixel values into component source code.

## 2. Aesthetic Constraints
- Read `reference/notes/do-not-copy.md` before initiating any frontend work.
- Strict avoidance of generic AI aesthetics (overly rounded cards, ambient neon glows, unsemantic step markers).
- Focus boldness in a single signature feature per page.
