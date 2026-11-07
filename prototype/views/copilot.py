"""
prototype/views/copilot.py — AI Sustainability Research Assistant & Chatbot
Conversational interface with multi-turn chat history, deep research traces,
clickable evidence drawers, and interactive data charts.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import core.copilot_service as cs
importlib.reload(cs)
from core.api import NavigatorAPI
from core.copilot_service import CopilotService


def render(root: Path) -> None:
    api = NavigatorAPI(root)
    # Ensure fresh instance with all methods bound
    api.copilot = CopilotService(root)

    # ── Custom CSS for Chatbot UI ────────────────────────────────────────────
    st.markdown(
        """
        <style>
        /* Chat container styling */
        .chat-header-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 12px;
            margin-bottom: 16px;
            border-bottom: 1px solid #e2e8f0;
        }
        .chat-title {
            font-size: 1.4rem;
            font-weight: 800;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .live-status-pill {
            background: #ecfdf5;
            color: #065f46;
            border: 1px solid #a7f3d0;
            border-radius: 20px;
            padding: 3px 12px;
            font-size: 0.72rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .status-dot-green {
            width: 7px;
            height: 7px;
            background: #10b981;
            border-radius: 50%;
            display: inline-block;
        }

        /* Working / Research Trace Block */
        .chat-working-block {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 14px 18px;
            margin: 10px 0 16px 0;
            font-size: 0.85rem;
        }
        .working-step {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 10px;
        }
        .green-pulse-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.25);
            flex-shrink: 0;
        }
        .search-chips-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }
        .search-chip {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 16px;
            padding: 3px 10px;
            font-size: 0.76rem;
            color: #475569;
            font-family: monospace;
        }
        .sources-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
        }
        .source-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 0.80rem;
        }
        .source-row:last-child {
            border-bottom: none;
        }
        .source-tag {
            font-size: 0.70rem;
            color: #64748b;
            font-family: monospace;
            background: #f1f5f9;
            padding: 1px 6px;
            border-radius: 4px;
        }

        /* Answer styling inside chat message */
        .chat-answer-summary {
            font-size: 1.02rem;
            line-height: 1.65;
            color: #0f172a;
            margin-bottom: 14px;
        }
        .chat-why-box {
            background: #f8fafc;
            border-left: 3px solid #059669;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin: 12px 0 16px 0;
        }
        .chat-why-title {
            font-size: 0.88rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 8px;
        }
        .chat-why-point {
            position: relative;
            padding-left: 16px;
            margin-bottom: 6px;
            font-size: 0.84rem;
            line-height: 1.55;
            color: #334155;
        }
        .chat-why-point::before {
            content: "•";
            position: absolute;
            left: 4px;
            color: #059669;
            font-weight: bold;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 14px 0;
        }
        .m-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 12px;
            text-align: center;
        }
        .m-box-val {
            font-size: 1.10rem;
            font-weight: 800;
            color: #0f172a;
        }
        .m-box-lbl {
            font-size: 0.68rem;
            font-weight: 600;
            color: #64748b;
            margin-top: 2px;
        }

        /* Evidence item */
        .evidence-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 3px solid #0284c7;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 8px;
            font-size: 0.80rem;
        }

        /* Verification footer */
        .verify-tag {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 0.74rem;
            color: #166534;
            margin-top: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="chat-header-bar">
            <div>
                <div class="chat-title">
                    <span>🌱 AI Sustainability Research Chatbot</span>
                </div>
                <div style="font-size:0.80rem; color:#64748b; margin-top:3px;">
                    Conversational intelligence grounded in Apetit's multi-table databases, ERP activity feeds, and GHG Protocol / SBTi standards.
                </div>
            </div>
            <div>
                <span class="live-status-pill">
                    <span class="status-dot-green"></span>
                    <span>14,213 Parcels · 680 Farms Connected</span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── AI Engine (Gemini) Status & Session Key ─────────────────────────────
    from core.llm_service import LLMService

    session_key = st.session_state.get("gemini_api_key") or None
    engine = LLMService(api_key=session_key)
    with st.expander(
        "🧠 AI Engine: " + ("**Gemini · grounded generation ON**" if engine.is_available else "**Offline deterministic mode** (add a Gemini key to enable free-form AI answers)"),
        expanded=False,
    ):
        st.markdown(
            "Answers are produced in two steps: **(1)** platform data handlers retrieve the relevant tables and evidence; "
            "**(2)** Gemini writes the answer using *only* that evidence and cites it as **[E1]**, **[E2]** … "
            "If Gemini is unavailable, the assistant automatically falls back to the deterministic answer."
        )
        if not LLMService.sdk_installed():
            st.warning("`google-genai` is not installed. Run `.venv/bin/pip install -r requirements.txt`.")
        k1, k2 = st.columns([3, 1])
        with k1:
            entered = st.text_input(
                "Gemini API key (kept in this browser session only, never saved to disk)",
                type="password",
                value=st.session_state.get("gemini_api_key", ""),
                placeholder="Paste key from aistudio.google.com/apikey, or set GEMINI_API_KEY",
            )
        with k2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Save key", use_container_width=True):
                st.session_state["gemini_api_key"] = entered.strip()
                st.rerun()
        st.caption("Key sources checked in order: this field → `GEMINI_API_KEY` / `GOOGLE_API_KEY` env var → `.streamlit/secrets.toml`.")

    def _history() -> List[Dict[str, str]]:
        hist: List[Dict[str, str]] = []
        for m in st.session_state.get("copilot_messages", []):
            if m["role"] == "user":
                hist.append({"role": "user", "content": m["content"]})
            else:
                hist.append({"role": "assistant", "content": m["data"].get("summary", "")})
        return hist

    def _ask(question: str) -> Dict[str, Any]:
        hist = _history()
        if hist and hist[-1]["role"] == "user" and hist[-1]["content"] == question:
            hist = hist[:-1]  # the current question is passed separately
        return api.copilot.research_query(question, history=hist, api_key=session_key)

    # ── Suggested Questions Library ──────────────────────────────────────────
    if hasattr(api.copilot, "get_suggested_queries"):
        suggested = api.copilot.get_suggested_queries()
    else:
        suggested = [
            {"id": "q_prioritise_risk", "label": "Prioritise Agricultural Risks", "query": "Which agricultural risk should we prioritise?", "icon": "🎯"},
            {"id": "q_emissions_increase", "label": "Emissions Increase Cause", "query": "Why did our emissions increase this year?", "icon": "📈"},
            {"id": "q_supplier_risks", "label": "Highest Supplier Climate Risks", "query": "Which agricultural suppliers have the highest climate risks?", "icon": "🚜"},
            {"id": "q_emissions_biodiversity", "label": "Emissions + Biodiversity Levers", "query": "Which actions can reduce emissions while protecting biodiversity?", "icon": "🌿"},
            {"id": "q_scenarios_compare", "label": "2030 vs 2050 Climate Scenarios", "query": "Compare our 2030 and 2050 climate scenarios.", "icon": "🔮"},
            {"id": "q_evidence_recommendation", "label": "Evidence Behind Recommendations", "query": "Show me the evidence behind our decarbonisation recommendations.", "icon": "🛡️"},
        ]

    # ── Session State for Chat History ───────────────────────────────────────
    if "copilot_messages" not in st.session_state:
        # Initial demonstration message (exact user example)
        initial_q = "Which agricultural risk should we prioritise?"
        initial_res = _ask(initial_q)
        st.session_state["copilot_messages"] = [
            {"role": "user", "content": initial_q},
            {"role": "assistant", "data": initial_res},
        ]

    # Quick action row: Reset chat and Suggested Prompt Chips
    chip_row1, chip_row2 = st.columns([4.2, 0.8])
    with chip_row1:
        st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:4px;'>Suggested Questions:</div>", unsafe_allow_html=True)
        q_cols = st.columns(len(suggested))
        for i, s in enumerate(suggested):
            with q_cols[i]:
                if st.button(
                    f"{s['icon']} {s['label']}",
                    key=f"chip_btn_{s['id']}",
                    help=s["query"],
                    use_container_width=True,
                ):
                    # Append new user question and evaluate
                    new_q = s["query"]
                    st.session_state["copilot_messages"].append({"role": "user", "content": new_q})
                    with st.spinner("Analyzing database and compiling evidence..."):
                        ans_data = _ask(new_q)
                    st.session_state["copilot_messages"].append({"role": "assistant", "data": ans_data})
                    st.rerun()

    with chip_row2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["copilot_messages"] = []
            st.rerun()

    st.markdown("---")

    # ── Render Conversational Thread ─────────────────────────────────────────
    for idx, msg in enumerate(st.session_state["copilot_messages"]):
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{msg['content']}**")
        else:
            with st.chat_message("assistant", avatar="🌱"):
                res = msg["data"]
                trace = res.get("trace", {})
                search_pills = trace.get("search_pills", [])
                sources_reviewed = trace.get("sources_reviewed", [])

                # 1. Working / Research Trace
                with st.expander(f"⚙️ Deep Research Trace · {len(sources_reviewed)} sources reviewed ({res.get('time_taken', '0.8s')})", expanded=False):
                    pills_html = "".join([f'<span class="search-chip">{p}</span>' for p in search_pills])
                    sources_html = "".join([
                        f"""
                        <div class="source-row">
                            <span>🌐 {s['title']}</span>
                            <span class="source-tag">{s['domain']}</span>
                        </div>
                        """
                        for s in sources_reviewed
                    ])
                    st.markdown(
                        f"""
                        <div class="chat-working-block">
                            <div class="working-step">
                                <span class="green-pulse-dot"></span>
                                <span>{trace.get('step', 'Executing cross-table analysis...')}</span>
                            </div>
                            <div style="font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:6px;">Searched Internal Tables:</div>
                            <div class="search-chips-container">{pills_html}</div>
                            <div style="font-size:0.75rem; font-weight:700; color:#64748b; margin-bottom:6px;">Consulted Authoritative Sources:</div>
                            <div class="sources-card">{sources_html}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # 2. Executive Summary
                is_gemini = res.get("ai_mode") == "gemini"
                if is_gemini:
                    st.markdown(
                        f"<span style='display:inline-block; background:#eef2ff; color:#4338ca; border:1px solid #c7d2fe; "
                        f"padding:2px 10px; border-radius:12px; font-size:0.72rem; font-weight:700; margin-bottom:6px;'>"
                        f"✨ Gemini · {res.get('llm_model') or 'model'} · grounded in {len(res.get('evidence', []))} cited datasets</span>",
                        unsafe_allow_html=True,
                    )
                    with st.container(border=True):
                        # Escape '$' so model text is never rendered as LaTeX
                        st.markdown(str(res["summary"]).replace("$", "\\$"))
                else:
                    st.markdown(
                        f"""
                        <div class="chat-answer-summary">
                            {res['summary']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # 3. Why? Key Drivers
                why_list = res.get("why", [])
                if why_list and is_gemini:
                    with st.expander("💡 Underlying deterministic findings (pre-computed from data)", expanded=False):
                        for w in why_list:
                            st.markdown(f"- {w}")
                elif why_list:
                    why_html = "".join([f'<div class="chat-why-point">{w}</div>' for w in why_list])
                    st.markdown(
                        f"""
                        <div class="chat-why-box">
                            <div class="chat-why-title">💡 Why? Key Analysis &amp; Drivers</div>
                            {why_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # 4. Key Metrics Grid
                metrics = res.get("metrics", {})
                if metrics:
                    m_cols = st.columns(len(metrics))
                    for mi, (k, v) in enumerate(metrics.items()):
                        with m_cols[mi]:
                            st.markdown(
                                f"""
                                <div class="m-box">
                                    <div class="m-box-val">{v}</div>
                                    <div class="m-box-lbl">{k}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                # 5. Clickable Evidence Drawers
                evidence_items = res.get("evidence", [])
                if evidence_items:
                    with st.expander(f"🛡️ Clickable Evidence ({len(evidence_items)} datasets attached)", expanded=False):
                        for ev_i, ev in enumerate(evidence_items, start=1):
                            st.markdown(
                                f"""
                                <div class="evidence-card">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                        <strong><span style="background:#eef2ff; color:#4338ca; padding:0 6px; border-radius:6px; margin-right:6px;">E{ev_i}</span>🗂️ {ev.get('dataset_name', 'Dataset')} · <code>{ev['file_path']}</code></strong>
                                        <span style="background:#e0f2fe; color:#0369a1; padding:1px 6px; border-radius:10px; font-size:0.70rem; font-weight:700;">
                                            {ev['records_analyzed']} Records
                                        </span>
                                    </div>
                                    <div><b>Formula / Basis:</b> <code>{ev['formula']}</code></div>
                                    <div style="color:#059669; margin:4px 0;"><b>Standard:</b> {ev['standard_ref']}</div>
                                    <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:4px 8px; border-radius:4px; font-size:0.75rem;">
                                        <code>{ev['sample_snippet']}</code>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                # 6. Interactive Visual Chart / Table Option
                chart_type = res.get("chart_type")
                table_data = res.get("table_data", [])

                with st.expander("📊 View Data Table & Visual Chart", expanded=False):
                    if table_data:
                        df_t = pd.DataFrame(table_data)
                        cols = res.get("table_columns")
                        if cols and all(c in df_t.columns for c in cols):
                            df_t = df_t[cols]
                        st.dataframe(df_t, use_container_width=True, hide_index=True)

                    if chart_type == "inventory_trend":
                        inv_df = pd.read_csv(api.copilot.inv_path)
                        fig = go.Figure()
                        fig.add_trace(go.Bar(x=inv_df["year"], y=inv_df["scope1"], name="Scope 1", marker_color="#ef4444"))
                        fig.add_trace(go.Bar(x=inv_df["year"], y=inv_df["scope2_market"], name="Scope 2 (Market)", marker_color="#f59e0b"))
                        fig.add_trace(go.Scatter(x=inv_df["year"], y=inv_df["scope3"], name="Scope 3", yaxis="y2", mode="lines+markers", line=dict(color="#0284c7", width=3)))
                        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), yaxis2=dict(overlaying="y", side="right"), barmode="stack", paper_bgcolor="#ffffff")
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")

                    elif chart_type == "risk_prioritisation_radar":
                        cats = ["Drought Water Stress", "Nutrient Runoff", "Autumn Heavy Rain", "Clay Compaction", "Heatwave Flowering", "Invasive Weeds"]
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(r=[94, 78, 62, 55, 88, 48], theta=cats, fill="toself", name="Region A (Säkylä)", line_color="#ef4444"))
                        fig.add_trace(go.Scatterpolar(r=[60, 45, 70, 75, 52, 40], theta=cats, fill="toself", name="National Baseline", line_color="#0284c7"))
                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=320, margin=dict(l=10, r=10, t=30, b=10))
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")

                    elif chart_type == "levers_co_benefits":
                        levers_df = pd.read_csv(api.copilot.levers_path).dropna(subset=["abatement_tco2e_2030_design"]).head(8)
                        fig = px.bar(levers_df, x="lever_id", y="abatement_tco2e_2030_design", color="indicative_cost_eur_per_tco2e", labels={"abatement_tco2e_2030_design": "Abatement (tCO₂e)"})
                        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")

                    elif chart_type == "tradeoff_radar":
                        from core.tradeoff_service import TradeoffService
                        act = TradeoffService(root).get_action_tradeoff("irrigation_efficiency")
                        cats = list(act["scores"].keys())
                        vals = list(act["scores"].values())
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(r=[50] * (len(cats) + 1), theta=cats + cats[:1], mode="lines", name="Neutral Baseline", line=dict(color="#cbd5e1", dash="dash")))
                        fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself", name=act["title"], line_color="#059669"))
                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=320, margin=dict(l=10, r=10, t=30, b=10))
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{idx}")
                        st.caption("👉 Explore all 6 actions in **⚖️ Trade-off Intelligence** in the sidebar.")

                # 7. Audit Banner
                mode_txt = (
                    f"AI-written by Gemini from cited data · numbers traceable to E1–E{len(evidence_items)}"
                    if is_gemini
                    else "Deterministic answer from platform data" + (f" · AI offline ({res['llm_error']})" if res.get("llm_error") and "No Gemini API key" not in str(res.get("llm_error")) else "")
                )
                st.markdown(
                    f"""
                    <div class="verify-tag">
                        <span>✅ <b>Evidence Grounded:</b> {len(evidence_items)} datasets attached · {mode_txt}</span>
                        <span style="color:#059669; font-weight:700;">Expert Review Pending</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Bottom Chat Input Bar (Native Streamlit chat_input) ──────────────────
    user_chat_query = st.chat_input("Ask about Apetit's emissions, suppliers, climate risks, or nature...")
    if user_chat_query:
        # Append user message
        st.session_state["copilot_messages"].append({"role": "user", "content": user_chat_query.strip()})
        # Evaluate assistant response
        with st.spinner("Analyzing database and cross-referencing evidence..."):
            response_data = _ask(user_chat_query.strip())
        st.session_state["copilot_messages"].append({"role": "assistant", "data": response_data})
        st.rerun()
