import io
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pptx import Presentation

from report_writer.ces_data import CES_COLUMNS, load_ces_data, ces_row
from report_writer.config import load_config
from report_writer.key_thematic import BRANDS, build_key_thematic_messages, chat_text
from report_writer.pptx_extractor import describe_images, extract_posts

load_dotenv(override=True)

st.set_page_config(page_title="Report Writer", layout="wide")
st.title("Report Writer")

config = load_config()

api_key = os.getenv("OPENAI_API_KEY", "").strip()

with st.sidebar:
    st.header("Settings")
    if api_key:
        st.success("OpenAI API key loaded from .env")
    else:
        st.warning("OPENAI_API_KEY is empty in .env")

    model = st.text_input("Model", value=config.get("model", "gpt-4o"))
    base_url = st.text_input("Base URL", value=config.get("base_url", "https://api.openai.com/v1"))
    temperature = st.slider("Temperature", 0.0, 1.0, float(config.get("temperature", 0.2)), 0.1)
    max_tokens = st.number_input("Max tokens", 100, 16000, int(config.get("max_tokens", 4000)), 100)


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

selected_slides = []
titles = {}
ces_df = None
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
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        done = 0
        total_slides = len(selected_slides)

        for kind, pillar in ordered_keys:
            for slide_no in sorted(groups[(kind, pillar)]):
                posts = extract_slide(pptx_file.getvalue(), slide_no)
                desc_map, usage = describe_images(
                    posts, api_key=api_key, model=model, base_url=base_url,
                    temperature=temperature, max_tokens=max_tokens,
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
                    for k in ("prompt_tokens", "completion_tokens"):
                        if isinstance(usage.get(k), int):
                            total_usage[k] += usage[k]

                done += 1
                progress.progress(done / total_slides, text=f"{group_label(kind, pillar)}: slide {slide_no}")

        progress.empty()
        st.session_state["results"] = results
        st.session_state["usage"] = total_usage
        if ces_df is not None:
            st.session_state["ces_df"] = ces_df

st.header("3. Results")

results = st.session_state.get("results", [])
if not results:
    st.info("Results will appear here after you run.")
else:
    usage = st.session_state.get("usage", {})
    if usage:
        st.caption(
            f"Tokens: {usage.get('prompt_tokens', 0)} prompt + "
            f"{usage.get('completion_tokens', 0)} completion"
        )

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

st.header("4. Key Thematic analysis")


def default_instruction():
    for s in config.get("sections", []):
        if s.get("name") == "CES Key Thematic (Enterprise)":
            return s.get("prompt", "")
    return ""


instruction = st.text_area(
    "Instruction prompt (editable)",
    value=default_instruction(),
    key="kt_instruction",
    height=300,
)

ces_results = [r for r in st.session_state.get("results", []) if r.get("kind") == "CES"]
has_ces_data = ces_df is not None or st.session_state.get("ces_df") is not None

if st.button("Generate Key Thematic", type="primary",
             disabled=(api_key == "" or not ces_results or not has_ces_data)):
    if not api_key:
        st.error("Set OPENAI_API_KEY in .env")
    else:
        ces_df_now = ces_df if ces_df is not None else st.session_state.get("ces_df")

        posts_by_combo = {}
        for r in ces_results:
            posts_by_combo[(r["pillar"], r["brand"])] = r["posts"]

        pillars_with_data = [p for p in pillars if any((p, b) in posts_by_combo for b in BRANDS)]

        total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        analyses = []
        progress = st.progress(0.0, text="Generating Key Thematic...")
        combos = [(p, b) for p in pillars_with_data for b in BRANDS if (p, b) in posts_by_combo]
        done = 0

        for pillar, brand in combos:
            ces_rows = {
                b: ces_row(ces_df_now, pillar, b)
                for b in BRANDS
            }
            posts = posts_by_combo[(pillar, brand)]

            messages = build_key_thematic_messages(pillar, brand, ces_rows, posts, instruction=instruction)
            try:
                output, usage = chat_text(
                    messages, api_key=api_key, model=model, base_url=base_url,
                    temperature=temperature, max_tokens=max_tokens,
                )
                error = None
            except Exception as e:
                output, usage, error = None, None, str(e)

            analyses.append({
                "pillar": pillar,
                "brand": brand,
                "output": output,
                "error": error,
                "messages": messages,
            })
            if usage:
                for k in ("prompt_tokens", "completion_tokens"):
                    if isinstance(usage.get(k), int):
                        total_usage[k] += usage[k]

            done += 1
            progress.progress(done / len(combos), text=f"{pillar} / {brand}")

        progress.empty()
        st.session_state["analyses"] = analyses
        st.session_state["kt_usage"] = total_usage

st.header("5. Key Thematic results")

analyses = st.session_state.get("analyses", [])
if not analyses:
    st.info("Key Thematic results will appear here after generation.")
else:
    kt_usage = st.session_state.get("kt_usage", {})
    if kt_usage:
        st.caption(
            f"Tokens: {kt_usage.get('prompt_tokens', 0)} prompt + "
            f"{kt_usage.get('completion_tokens', 0)} completion"
        )

    for a in analyses:
        with st.expander(f"{a['pillar']} / {a['brand']}", expanded=False):
            if a["error"]:
                st.error(f"Error: {a['error']}")
            else:
                tab_out, tab_data = st.tabs(["Output", "Data sent"])
                with tab_out:
                    st.markdown(a["output"])
                with tab_data:
                    st.code(a["messages"][1]["content"], language="text")
