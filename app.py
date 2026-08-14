import io
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pptx import Presentation

from report_writer.analysis_export import build_analysis_title, export_analysis_excel
from report_writer.ces_data import CES_COLUMNS, load_ces_data, ces_row
from report_writer.config import load_config
from report_writer.key_thematic import BRANDS, build_key_thematic_messages, chat_text
from report_writer.overview_ces import (
    build_overview_ces_messages,
    overview_ces_validation_error,
)
from report_writer.overview_pre import (
    build_overview_pre_messages,
    overview_pre_validation_error,
)
from report_writer.pptx_extractor import describe_images, extract_posts
from report_writer.pre_data import load_pre_data, pre_row
from report_writer.top_pri_content import build_top_pri_messages, group_top_pri_posts
from report_writer.usage_cost import add_usage, empty_usage, usage_summary

load_dotenv(override=True)

st.set_page_config(page_title="Report Writer", layout="wide")
st.title("Report Writer")

config = load_config()
pricing_by_model = config.get("pricing_usd_per_million_tokens", {})
model = config.get("model", "gpt-5.6-luna")
base_url = config.get("base_url", "https://api.openai.com/v1")
max_completion_tokens = int(config.get("max_completion_tokens", 4000))

api_key = os.getenv("OPENAI_API_KEY", "").strip()

if not api_key:
    st.warning("OPENAI_API_KEY is empty in .env")


@st.cache_data(show_spinner=False)
def load_slides(file_bytes):
    prs = Presentation(io.BytesIO(file_bytes))

    def title_of(slide):
        try:
            t = slide.shapes.title
            if t is not None and t.text.strip():
                return t.text.strip().replace("\t", " ").replace("\n", " ")
        except Exception:
            pass
        return "(no title)"

    titles = {}
    for i, slide in enumerate(prs.slides, start=1):
        titles[i] = title_of(slide)
    return titles


@st.cache_data(show_spinner=False)
def extract_slide(file_bytes, slide_no):
    prs = Presentation(io.BytesIO(file_bytes))
    slide = prs.slides[slide_no - 1]
    posts = extract_posts(slide)
    for p in posts:
        p.pop("_left", None)
        p.pop("_top", None)
    return posts


@st.cache_data(show_spinner=False)
def load_ces(file_bytes):
    df = load_ces_data(file_bytes)
    return df


@st.cache_data(show_spinner=False)
def load_pre(file_bytes):
    return load_pre_data(file_bytes)


def pillar_of(title, pillars):
    for p in pillars:
        if p in title:
            return p
    return "Other"


def brand_of(title):
    for b in ("SCG", "PTT", "CP"):
        if b in title:
            return b
    return None


def kind_of(title):
    if "TOP PRI" in title:
        return "PRE"
    if "TOP POST" in title:
        return "CES"
    return None


def group_label(kind, pillar):
    return f"{kind} {pillar}"


st.header("1. Upload inputs")

pptx_file = st.file_uploader("PPTX file", type=["pptx"], key="pptx_upload")
excel_file = st.file_uploader("Excel file (CES score)", type=["xlsx", "xls", "xlsm"], key="excel_upload")
pre_excel_file = st.file_uploader(
    "Excel file (PRE score summary)",
    type=["xlsx", "xls", "xlsm"],
    key="pre_excel_upload",
)

selected_slides = []
titles = {}
ces_df = None
pre_df = None
pillars = config.get("pillars", ["ESG Branding", "Business Branding", "Employer Branding"])

if pptx_file is not None:
    titles = load_slides(pptx_file.getvalue())
    st.caption(f"{len(titles)} slides detected")

    default_slides = [n for n, t in titles.items() if "TOP POST" in t or "TOP PRI" in t]
    selected_slides = st.multiselect(
        "Slides to process",
        options=list(titles.keys()),
        default=default_slides,
        format_func=lambda n: f"{n}: {titles[n]}",
    )

if excel_file is not None:
    try:
        ces_df = load_ces(excel_file.getvalue())
        with st.expander("CES score data (columns reordered: score | growth)"):
            st.dataframe(ces_df, use_container_width=True, height=280)
    except Exception as e:
        st.error(f"Could not read Excel: {e}")

if pre_excel_file is not None:
    try:
        pre_df = load_pre(pre_excel_file.getvalue())
        with st.expander("PRE score data (8 required columns)"):
            st.dataframe(pre_df, use_container_width=True, height=280)
    except Exception as e:
        st.error(f"Could not read PRE Excel: {e}")

st.header("2. Extract & describe")

if st.button("Run", type="primary", disabled=(api_key == "" or pptx_file is None or not selected_slides)):
    if not api_key:
        st.error("Set OPENAI_API_KEY in .env")
    else:
        groups = {}
        for n in selected_slides:
            kind = kind_of(titles[n]) or "CES"
            p = pillar_of(titles[n], pillars)
            groups.setdefault((kind, p), []).append(n)

        ordered_keys = [(k, p) for k, p in groups if k == "CES"] + [(k, p) for k, p in groups if k != "CES"]

        results = []
        progress = st.progress(0.0, text="Processing slides...")
        total_usage = empty_usage()
        done = 0
        total_slides = len(selected_slides)

        for kind, pillar in ordered_keys:
            for slide_no in sorted(groups[(kind, pillar)]):
                posts = extract_slide(pptx_file.getvalue(), slide_no)
                desc_map, usage = describe_images(
                    posts, api_key=api_key, model=model, base_url=base_url,
                    max_completion_tokens=max_completion_tokens,
                )

                for j, p in enumerate(posts):
                    p["image_description"] = desc_map.get(j)

                results.append({
                    "kind": kind,
                    "pillar": pillar,
                    "group": group_label(kind, pillar),
                    "brand": brand_of(titles[slide_no]),
                    "slide": slide_no,
                    "title": titles[slide_no],
                    "posts": posts,
                })
                if usage:
                    add_usage(total_usage, usage)

                done += 1
                progress.progress(done / total_slides, text=f"{group_label(kind, pillar)}: slide {slide_no}")

        progress.empty()
        st.session_state["results"] = results
        st.session_state["usage"] = total_usage
        st.session_state["usage_model"] = model
        if ces_df is not None:
            st.session_state["ces_df"] = ces_df
        if pre_df is not None:
            st.session_state["pre_df"] = pre_df

st.header("3. Results")

results = st.session_state.get("results", [])
if not results:
    st.info("Results will appear here after you run.")
else:
    usage = st.session_state.get("usage", {})
    if usage:
        usage_model = st.session_state.get("usage_model", model)
        st.caption(usage_summary(usage, usage_model, pricing_by_model))

    for r in results:
        with st.expander(f"{r['group']} — Slide {r['slide']} — {r['title']}", expanded=False):
            for p in r["posts"]:
                cols = st.columns([1, 3])
                with cols[0]:
                    if p.get("image") is not None:
                        st.image(p["image"], width=180)
                    else:
                        st.caption("no image")
                with cols[1]:
                    st.markdown(f"**Tag:** {p.get('tag') or '—'}")
                    m = p.get("metrics") or {}
                    if p.get("kind") == "pre":
                        st.caption(
                            f"PRI {m.get('pri', '—'):,} | PRE {m.get('pre', '—')} | "
                            f"Engagement {m.get('engagement', '—'):,}"
                        )
                        if p.get("publisher"):
                            st.caption(f"Source: {p['publisher']}")
                    else:
                        st.caption(
                            f"Engagement {m.get('engagement', '—')} | "
                            f"Like {m.get('like', '—')} | "
                            f"Comment {m.get('comment', '—')} | "
                            f"Share {m.get('share', '—')}"
                        )
                    st.caption(p["caption"][:200])
                    if p.get("image_description"):
                        st.write(p["image_description"])
                    else:
                        st.caption("_no image description_")

st.header("4. Analysis")


def section_instruction(section_name):
    for s in config.get("sections", []):
        if s.get("name") == section_name:
            return s.get("prompt", "")
    return ""


instruction = st.text_area(
    "Key Thematic instruction prompt (editable)",
    value=section_instruction("CES Key Thematic (Enterprise)"),
    key="kt_instruction",
    height=300,
)

top_pri_instruction = st.text_area(
    "Top PRI Content instruction prompt (editable)",
    value=section_instruction("Top PRI Content"),
    key="top_pri_instruction",
    height=300,
)

overview_ces_instruction = st.text_area(
    "Overview CES instruction prompt (editable)",
    value=section_instruction("CES Overview (Enterprise)"),
    key="overview_ces_instruction",
    height=300,
)

overview_pre_instruction = st.text_area(
    "PRE Overview instruction prompt (editable)",
    value=section_instruction("PRE Overview"),
    key="overview_pre_instruction",
    height=300,
)

all_results = st.session_state.get("results", [])
ces_results = [result for result in all_results if result.get("kind") == "CES"]
pre_results = [r for r in st.session_state.get("results", []) if r.get("kind") == "PRE"]
has_pre_data = pre_df is not None or st.session_state.get("pre_df") is not None
has_ces_data = ces_df is not None or st.session_state.get("ces_df") is not None

ces_posts_by_combo = {}
for result in ces_results:
    pillar = result.get("pillar")
    brand = result.get("brand")
    if pillar not in pillars or brand not in BRANDS:
        continue
    ces_posts_by_combo.setdefault((pillar, brand), []).extend(result.get("posts") or [])

pre_posts_by_combo = group_top_pri_posts(pre_results, pillars)
key_thematic_combos = [
    (pillar, brand)
    for pillar in pillars
    for brand in BRANDS
    if (pillar, brand) in ces_posts_by_combo
]
top_pri_combos = [
    (pillar, brand)
    for pillar in pillars
    for brand in BRANDS
    if (pillar, brand) in pre_posts_by_combo
]

analysis_ready = (
    api_key != ""
    and has_ces_data
    and has_pre_data
    and bool(key_thematic_combos)
    and bool(top_pri_combos)
)

if st.button(
    "Generate All Analysis",
    type="primary",
    disabled=not analysis_ready,
):
    if not api_key:
        st.error("Set OPENAI_API_KEY in .env")
    else:
        ces_df_now = ces_df if ces_df is not None else st.session_state.get("ces_df")
        pre_df_now = pre_df if pre_df is not None else st.session_state.get("pre_df")
        total_usage = empty_usage()
        analyses = []
        top_pri_analyses = []
        overview_ces_analyses = []
        overview_pre_analyses = []
        total_combos = len(key_thematic_combos) + len(top_pri_combos) + (2 * len(pillars))
        done = 0
        progress = st.progress(0.0, text="Generating Key Thematic...")

        for pillar, brand in key_thematic_combos:
            ces_rows = {
                comparison_brand: ces_row(ces_df_now, pillar, comparison_brand)
                for comparison_brand in BRANDS
            }
            messages = build_key_thematic_messages(
                pillar,
                brand,
                ces_rows,
                ces_posts_by_combo[(pillar, brand)],
                instruction=instruction,
            )
            try:
                output, usage = chat_text(
                    messages,
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    max_completion_tokens=max_completion_tokens,
                )
                error = None
            except Exception as e:
                output, usage, error = None, None, str(e)

            analyses.append({
                "section": "CES Key Thematic",
                "pillar": pillar,
                "brand": brand,
                "title": build_analysis_title("CES", pillar, brand, "Key Thematic"),
                "output": output,
                "error": error,
                "messages": messages,
            })
            if usage:
                add_usage(total_usage, usage)
            done += 1
            progress.progress(
                done / total_combos,
                text=f"Key Thematic: {pillar} / {brand}",
            )

        for pillar, brand in top_pri_combos:
            pre_rows = {
                comparison_brand: pre_row(pre_df_now, pillar, comparison_brand)
                for comparison_brand in BRANDS
            }
            messages = build_top_pri_messages(
                pillar,
                brand,
                pre_rows,
                pre_posts_by_combo[(pillar, brand)],
                instruction=top_pri_instruction,
            )
            try:
                output, usage = chat_text(
                    messages,
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    max_completion_tokens=max_completion_tokens,
                )
                error = None
            except Exception as e:
                output, usage, error = None, None, str(e)

            top_pri_analyses.append({
                "section": "Top PRI Content",
                "pillar": pillar,
                "brand": brand,
                "title": build_analysis_title("PRE", pillar, brand, "Top PRI Content"),
                "output": output,
                "error": error,
                "messages": messages,
            })
            if usage:
                add_usage(total_usage, usage)
            done += 1
            progress.progress(
                done / total_combos,
                text=f"Top PRI Content: {pillar} / {brand}",
            )

        key_thematic_outputs = {
            (analysis["pillar"], analysis["brand"]): analysis.get("output")
            for analysis in analyses
            if not analysis.get("error") and analysis.get("output")
        }
        for pillar in pillars:
            ces_rows = {
                brand: ces_row(ces_df_now, pillar, brand)
                for brand in BRANDS
            }
            pillar_key_thematics = {
                brand: key_thematic_outputs.get((pillar, brand))
                for brand in BRANDS
            }
            error = overview_ces_validation_error(ces_rows, pillar_key_thematics)
            messages = []
            output = None
            usage = None

            if error is None:
                messages = build_overview_ces_messages(
                    pillar,
                    ces_rows,
                    pillar_key_thematics,
                    instruction=overview_ces_instruction,
                )
                try:
                    output, usage = chat_text(
                        messages,
                        api_key=api_key,
                        model=model,
                        base_url=base_url,
                        max_completion_tokens=max_completion_tokens,
                    )
                except Exception as e:
                    error = str(e)

            overview_ces_analyses.append({
                "section": "CES Overview",
                "pillar": pillar,
                "brand": None,
                "title": build_analysis_title("CES", pillar, None, "Overview"),
                "output": output,
                "error": error,
                "messages": messages,
            })
            if usage:
                add_usage(total_usage, usage)
            done += 1
            progress.progress(
                done / total_combos,
                text=f"Overview CES: {pillar}",
            )

        top_pri_outputs = {
            (analysis["pillar"], analysis["brand"]): analysis.get("output")
            for analysis in top_pri_analyses
            if not analysis.get("error") and analysis.get("output")
        }
        for pillar in pillars:
            pre_rows = {
                brand: pre_row(pre_df_now, pillar, brand)
                for brand in BRANDS
            }
            pillar_top_pri_outputs = {
                brand: top_pri_outputs.get((pillar, brand))
                for brand in BRANDS
            }
            error = overview_pre_validation_error(pre_rows, pillar_top_pri_outputs)
            messages = []
            output = None
            usage = None

            if error is None:
                messages = build_overview_pre_messages(
                    pillar,
                    pre_rows,
                    pillar_top_pri_outputs,
                    instruction=overview_pre_instruction,
                )
                try:
                    output, usage = chat_text(
                        messages,
                        api_key=api_key,
                        model=model,
                        base_url=base_url,
                        max_completion_tokens=max_completion_tokens,
                    )
                except Exception as e:
                    error = str(e)

            overview_pre_analyses.append({
                "section": "PRE Overview",
                "pillar": pillar,
                "brand": None,
                "title": build_analysis_title("PRE", pillar, None, "Overview"),
                "output": output,
                "error": error,
                "messages": messages,
            })
            if usage:
                add_usage(total_usage, usage)
            done += 1
            progress.progress(
                done / total_combos,
                text=f"PRE Overview: {pillar}",
            )

        progress.empty()
        st.session_state["analyses"] = analyses
        st.session_state["top_pri_analyses"] = top_pri_analyses
        st.session_state["overview_ces_analyses"] = overview_ces_analyses
        st.session_state["overview_pre_analyses"] = overview_pre_analyses
        st.session_state["analysis_usage"] = total_usage
        st.session_state["analysis_usage_model"] = model

st.subheader("Analysis results")

analyses = st.session_state.get("analyses", [])
top_pri_analyses = st.session_state.get("top_pri_analyses", [])
overview_ces_analyses = st.session_state.get("overview_ces_analyses", [])
overview_pre_analyses = st.session_state.get("overview_pre_analyses", [])
combined_analyses = analyses + top_pri_analyses + overview_ces_analyses + overview_pre_analyses

if not combined_analyses:
    st.info("Analysis results will appear here after generation.")
else:
    analysis_usage = st.session_state.get("analysis_usage", {})
    if analysis_usage:
        analysis_usage_model = st.session_state.get("analysis_usage_model", model)
        st.caption(usage_summary(analysis_usage, analysis_usage_model, pricing_by_model))

    exportable_analyses = [
        analysis
        for analysis in combined_analyses
        if analysis.get("output") and not analysis.get("error")
    ]
    if exportable_analyses:
        st.download_button(
            "Export analysis to Excel",
            data=export_analysis_excel(exportable_analyses),
            file_name="scg_analysis_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    for section_name, section_results in (
        ("Key Thematic", analyses),
        ("Top PRI Content", top_pri_analyses),
        ("Overview CES", overview_ces_analyses),
        ("PRE Overview", overview_pre_analyses),
    ):
        st.markdown(f"**{section_name}**")
        if not section_results:
            st.caption("No results")
            continue
        for analysis in section_results:
            result_label = analysis["pillar"]
            if analysis.get("brand"):
                result_label += f" / {analysis['brand']}"
            with st.expander(result_label, expanded=False):
                if analysis["error"]:
                    st.error(f"Error: {analysis['error']}")
                else:
                    tab_out, tab_data = st.tabs(["Output", "Data sent"])
                    with tab_out:
                        st.code(analysis["output"], language=None, wrap_lines=True)
                    with tab_data:
                        st.code(analysis["messages"][1]["content"], language="text")
