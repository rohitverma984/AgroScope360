# AGENTS.md — Apetit Climate & Nature Navigator Project Rules

These rules apply to ALL agents and AI tools working in this workspace.

## Core Guardrails

1. **Keep supplied data unchanged.** Never edit, overwrite, or delete any file inside
   `APETIT_CLIMATE_NATURE_NAVIGATOR_2026/`. All original data, tools, docs, and task
   templates are read-only reference material.

2. **Label results as synthetic estimates.** Every output, chart, and narrative must carry
   a visible notice that the data is a synthetic twin and does not represent Apetit's
   actual emissions, farm results, or financial figures.

3. **Every key number must show its source and assumptions.** No metric may appear in the
   app without a traceable link to the source record(s) (e.g. ERP doc/line, meter reading,
   PCF JSON, parcel ID) and the emission factor or formula applied.

4. **Calculations are code-based.** All GHG inventory, nutrient load, yield, and
   abatement calculations must be implemented as deterministic Python code, reusing
   `tools/ccn_tools/` where appropriate. AI may only be used to explain results, not to
   generate numerical outputs.

5. **Expert approval is required.** Pathway recommendations and AI-generated
   interpretations must pass through an explicit expert-review step (status: Pending /
   Approved / Flagged) before being treated as final.

6. **Distinguish physical reductions from accounting changes.** Structural boundary events
   (acquisitions, divestments) and measurement improvements (e.g. soil sampling) must be
   clearly separated from actual emissions reductions in all pathway views.

## Prototype Location

All new prototype code lives exclusively in `prototype/`. Do not create app files
anywhere else in the workspace.

