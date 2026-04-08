"""
Cellpose Multi-Condition Analysis App
--------------------------------------
Streamlit + papermill web interface for keyence_10x_cellpose_notebook_multi_conditions.ipynb.

Usage:
    conda activate cellpose
    streamlit run app_keyence_10x.py
"""

import os
import glob
import re
import sys

import streamlit as st
import papermill as pm

# ─────────────────────────────────────────────────────────────────────────────
#  SETTINGS  —  set this to your top-level data directory
# ─────────────────────────────────────────────────────────────────────────────
# Auto-detect a sensible starting data root across machines:
#   Windows: C:/Users/Backup  →  C:/Users  →  home dir
#   Mac:     ~/Desktop  →  home dir
def _detect_data_root():
    home = os.path.expanduser("~")
    # Look for any OneDrive folder under the user's home (handles variant domain names)
    onedrive_candidates = []
    try:
        for name in os.listdir(home):
            if name.lower().startswith("onedrive") and os.path.isdir(os.path.join(home, name)):
                onedrive_candidates.append(os.path.join(home, name))
    except PermissionError:
        pass

    candidates = onedrive_candidates + [
        "C:/Backup/Keyence",
        "C:/Backup",
        "C:/Users/Backup",
        os.path.join(home, "Desktop"),
        home,
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return home

DATA_ROOT = _detect_data_root()
NOTEBOOK_PATH = os.path.join(os.path.dirname(__file__), "keyence_10x_cellpose_notebook_multi_conditions.ipynb")
EXECUTED_NB_NAME = "keyence_10x_cellpose_notebook_multi_executed.ipynb"

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def immediate_subfolders(path):
    try:
        return sorted([d for d in os.listdir(path)
                       if os.path.isdir(os.path.join(path, d))
                       and not d.startswith('.')])
    except PermissionError:
        return []


def label_to_key(label, idx):
    """Convert a label to a safe key, guaranteed unique by including the index."""
    key = re.sub(r'[^\w]', '_', label.strip()).lower()
    key = re.sub(r'_+', '_', key).strip('_')   # collapse runs of underscores
    if not key or key[0].isdigit():
        key = 'cond_' + key if key else 'condition'
    return f"cond{idx}_{key}"


def folder_browser(label, key_prefix, root):
    """Text-input folder picker. Returns path string if valid, else None."""
    state_key = f"{key_prefix}_text"
    if state_key not in st.session_state:
        st.session_state[state_key] = root

    path = st.text_input(label, value=st.session_state[state_key], key=state_key)

    # Normalize: strip whitespace, remove surrounding quotes, and convert backslashes
    # so pasted Windows paths (e.g. from File Explorer) are accepted without modification.
    if path:
        path = path.strip()
        # Remove surrounding quotes (both single and double)
        if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
            path = path[1:-1]
        path = path.replace("\\", "/")

    if path and os.path.isdir(path):
        return path
    elif path:
        st.warning("Path not found — check the folder path.")
    return None


def find_overlay_pngs(roots):
    pngs = []
    for root in roots:
        if root and os.path.isdir(root):
            pngs += glob.glob(os.path.join(root, "**", "*_overlay.png"), recursive=True)
    return sorted(set(pngs))


def find_figures(save_dir):
    figs = {}
    for i in [1, 2, 3]:
        matches = glob.glob(os.path.join(save_dir, f"fig{i}_*.png")) or \
                  glob.glob(os.path.join(save_dir, f"fig{i}_*.pdf"))
        if matches:
            figs[f"Figure {i}"] = matches[0]
    return figs


# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Cellpose Multi-Condition Analysis", layout="wide")

# Inject CSS to tighten up sidebar vertical spacing
st.markdown("""
<style>
/* ── Sidebar spacing ── */
section[data-testid="stSidebar"] .block-container { padding-top: 0.5rem; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; }
section[data-testid="stSidebar"] .stMarkdown p { margin-bottom: -0.4rem; }
section[data-testid="stSidebar"] .stTextInput  { margin-bottom: -0.8rem; }
section[data-testid="stSidebar"] .stSelectbox  { margin-bottom: -0.8rem; }
section[data-testid="stSidebar"] .stButton      { margin-bottom: -0.8rem; }
section[data-testid="stSidebar"] .stButton > button { padding: 0.15rem 0.5rem; font-size: 0.75rem; min-height: 0; }
section[data-testid="stSidebar"] .stCaption     { margin-top: -0.4rem; margin-bottom: -0.4rem; }
section[data-testid="stSidebar"] .stNumberInput { margin-bottom: -0.8rem; }
section[data-testid="stSidebar"] .stSuccess     { margin-top: -0.3rem; margin-bottom: -0.3rem; padding: 0.2rem 0.5rem; }
section[data-testid="stSidebar"] .stInfo        { margin-top: -0.3rem; margin-bottom: -0.3rem; padding: 0.2rem 0.5rem; }
section[data-testid="stSidebar"] hr { margin-top: 0.25rem; margin-bottom: 0.25rem; }

/* ── Sidebar font sizes ── */
section[data-testid="stSidebar"] { font-size: 0.78rem; }
section[data-testid="stSidebar"] label  { font-size: 0.75rem !important; }
section[data-testid="stSidebar"] p      { font-size: 0.78rem !important; }
section[data-testid="stSidebar"] small  { font-size: 0.72rem !important; }
section[data-testid="stSidebar"] input  { font-size: 0.75rem !important; padding: 0.2rem 0.4rem; }
section[data-testid="stSidebar"] select { font-size: 0.75rem !important; }

/* ── Dropdown menu font (the floating option list) ── */
div[data-baseweb="select"] span            { font-size: 0.78rem !important; }
div[data-baseweb="select"] div             { font-size: 0.78rem !important; }
div[data-baseweb="popover"] li             { font-size: 0.78rem !important; }
div[data-baseweb="popover"] ul             { font-size: 0.78rem !important; }
div[data-baseweb="menu"] li                { font-size: 0.78rem !important; }
div[role="listbox"] li                     { font-size: 0.78rem !important; }
div[role="option"]                         { font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("Cellpose Fluorescence Analysis — Multi-Condition")

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR — condition setup
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Setup")

    if not os.path.isdir(DATA_ROOT):
        st.error(f"DATA_ROOT not found:\n`{DATA_ROOT}`\n\nEdit `app_multi.py` to point to your data folder.")
        st.stop()

    # ── Number of conditions ──────────────────────────────────────────────────
    n_cond = st.number_input("Number of conditions", min_value=2, max_value=10,
                             value=st.session_state.get("n_cond", 2), step=1, key="n_cond")

    # ── Channel selection ─────────────────────────────────────────────────────
    CH_OPTIONS = ["CH1", "CH2", "CH3", "CH4"]
    ref_ch = st.selectbox("Reference channel (segmentation)",
                          CH_OPTIONS, index=CH_OPTIONS.index("CH2"), key="ref_ch")
    sig_ch = st.selectbox("Signal channel (fluorescence)",
                          CH_OPTIONS, index=CH_OPTIONS.index("CH4"), key="sig_ch")
    if ref_ch == sig_ch:
        st.warning("Reference and signal channels are the same.")

    REF_SUFFIX = f"_{ref_ch}.tif"
    SIG_SUFFIX = f"_{sig_ch}.tif"

    st.divider()

    # ── Per-condition: label + folder picker ─────────────────────────────────
    # Labels are stored in a single protected dict so that st.rerun() calls
    # inside folder_browser (which restart the script mid-loop) never wipe
    # values that haven't been re-rendered yet in the new run.
    if "_labels" not in st.session_state:
        st.session_state["_labels"] = {}

    conditions_config = []
    all_confirmed = True

    for i in range(int(n_cond)):
        default_label = ["Control", "Drug"][i] if i < 2 else f"Condition {i+1}"

        # Initialise label for this slot if not yet set
        if i not in st.session_state["_labels"]:
            st.session_state["_labels"][i] = default_label

        # Text input — value driven from protected dict; update dict on every render
        new_label = st.text_input(
            f"Condition {i+1} name",
            value=st.session_state["_labels"][i],
        )
        st.session_state["_labels"][i] = new_label   # persist immediately
        label = new_label

        confirmed_path = folder_browser(f"Folder for '{label}'", f"cond_{i}", DATA_ROOT)

        if confirmed_path:
            conditions_config.append({
                "label"     : label,
                "key"       : label_to_key(label, i),
                "root_path" : confirmed_path,
            })
        else:
            all_confirmed = False

        if i < int(n_cond) - 1:
            st.divider()

    # ── SAVE_DIR ──────────────────────────────────────────────────────────────
    SAVE_DIR = None
    if all_confirmed and len(conditions_config) == int(n_cond):
        all_paths = [os.path.abspath(c["root_path"]) for c in conditions_config]
        if len(set(all_paths)) < len(all_paths):
            st.warning("Two or more conditions point to the same folder.")
            all_confirmed = False
        else:
            SAVE_DIR = os.path.join(os.path.commonpath(all_paths), "RESULTS")
            st.markdown("**Results will be saved to:**")
            st.caption(SAVE_DIR)
    else:
        st.info("Confirm all condition folders above to enable Run.")

    st.divider()
    run_button = st.button("▶  Run Analysis", type="primary", use_container_width=True,
                           disabled=not (all_confirmed and SAVE_DIR))

# ─────────────────────────────────────────────────────────────────────────────
#  RUN NOTEBOOK
# ─────────────────────────────────────────────────────────────────────────────

if run_button:
    os.makedirs(SAVE_DIR, exist_ok=True)
    executed_nb_path = os.path.join(SAVE_DIR, EXECUTED_NB_NAME)

    st.info("Running analysis... This may take several minutes.")
    progress_bar = st.progress(10, text="Executing notebook (papermill)...")

    try:
        import jupyter_client
        kernel_name = "cellpose"
        available = jupyter_client.kernelspec.find_kernel_specs()
        if kernel_name not in available:
            kernel_name = next(
                (k for k in available
                 if sys.executable in jupyter_client.kernelspec.get_kernel_spec(k).argv),
                list(available.keys())[0]
            )

        pm.execute_notebook(
            NOTEBOOK_PATH,
            executed_nb_path,
            parameters={
                "CONDITIONS_CONFIG": conditions_config,
                "REF_SUFFIX": REF_SUFFIX,
                "SIG_SUFFIX": SIG_SUFFIX,
            },
            kernel_name=kernel_name,
            log_output=True,
        )

        progress_bar.progress(100, text="Done!")
        st.success("Analysis complete!")
        st.session_state["last_save_dir"]    = SAVE_DIR
        st.session_state["last_cond_roots"]  = [c["root_path"] for c in conditions_config]
        st.session_state["last_cond_labels"] = [c["label"]     for c in conditions_config]

    except Exception as e:
        progress_bar.empty()
        st.error("Notebook execution failed.")
        st.exception(e)
        st.stop()

# ─────────────────────────────────────────────────────────────────────────────
#  RESULTS DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

display_save_dir = st.session_state.get(
    "last_save_dir",
    SAVE_DIR if (SAVE_DIR and os.path.isdir(SAVE_DIR)) else None
)
display_cond_roots = st.session_state.get(
    "last_cond_roots",
    [c["root_path"] for c in conditions_config] if all_confirmed else []
)

if display_save_dir and os.path.isdir(display_save_dir):

    st.divider()

    # ── Figures ───────────────────────────────────────────────────────────────
    figs = find_figures(display_save_dir)
    if figs:
        st.header("Summary Figures")
        from PIL import Image as _Image
        import io as _io

        # Target height in pixels — every figure is resized to exactly this height,
        # preserving aspect ratio. Streamlit receives a pre-sized image so column
        # width can never shrink it further.
        TARGET_HEIGHT = 500

        # Pre-resize all PNGs to TARGET_HEIGHT tall, keep aspect ratio
        fig_images = {}
        for name, fpath in figs.items():
            if fpath.endswith(".png"):
                with _Image.open(fpath) as im:
                    w, h = im.size
                    new_w = max(1, int(TARGET_HEIGHT * w / h))
                    resized = im.resize((new_w, TARGET_HEIGHT), _Image.LANCZOS)
                    buf = _io.BytesIO()
                    resized.save(buf, format="PNG")
                    fig_images[name] = buf.getvalue()

        fig_cols = st.columns(len(figs))
        for col, (name, fpath) in zip(fig_cols, figs.items()):
            with col:
                st.subheader(name)
                if name in fig_images:
                    st.image(fig_images[name])   # already exactly TARGET_HEIGHT tall
                else:
                    with open(fpath, "rb") as f:
                        st.download_button(f"Download {name} (PDF)", f,
                                           os.path.basename(fpath), "application/pdf")

    # ── Field-of-view average chart ───────────────────────────────────────────
    _excel_path = os.path.join(display_save_dir, "cellpose_results.xlsx")
    if os.path.exists(_excel_path):
        import pandas as _pd
        import matplotlib.pyplot as _plt
        import matplotlib.cm as _cm
        import numpy as _np

        df_fov = _pd.read_excel(_excel_path, sheet_name="per_image")
        st.header("Field-of-View Averages")

        conditions = df_fov["condition"].unique()
        colors = _cm.tab10.colors
        fov_names = df_fov["image_file"].unique()
        short_names = [os.path.splitext(os.path.basename(f))[0] for f in fov_names]
        x = _np.arange(len(fov_names))
        width = 0.8 / max(len(conditions), 1)

        fig, ax = _plt.subplots(figsize=(max(8, len(fov_names) * 0.5 * len(conditions)), 4))
        for ci, cond in enumerate(conditions):
            sub = df_fov[df_fov["condition"] == cond].set_index("image_file")
            vals = [sub.loc[f, "mean_cellF_ratio"] if f in sub.index else float("nan")
                    for f in fov_names]
            ax.bar(x + ci * width, vals, width, label=cond,
                   color=colors[ci % len(colors)], alpha=0.85)

        ax.set_xticks(x + width * (len(conditions) - 1) / 2)
        ax.set_xticklabels(short_names, rotation=45, ha="right", fontsize=7)
        ax.set_ylabel("Mean signal/reference ratio")
        ax.set_title("Mean cellF ratio per field of view")
        ax.legend()
        _plt.tight_layout()
        st.pyplot(fig)
        _plt.close(fig)

    # ── Cell mask overlays — grouped by condition ─────────────────────────────
    st.header("Cell Mask Overlays")
    COLS = 4
    any_overlays = False

    # Build label→root mapping from whichever conditions are known this session
    if display_cond_roots and "last_cond_labels" in st.session_state:
        cond_pairs = list(zip(st.session_state["last_cond_labels"], display_cond_roots))
    else:
        # Fall back: use current sidebar config if available
        cond_pairs = [(c["label"], c["root_path"]) for c in conditions_config] \
                     if all_confirmed else []

    for cond_label, cond_root in cond_pairs:
        pngs = sorted(glob.glob(os.path.join(cond_root, "**", "*_overlay.png"), recursive=True))
        if not pngs:
            continue
        any_overlays = True
        st.subheader(f"{cond_label}  ({len(pngs)} images)")
        for row_start in range(0, len(pngs), COLS):
            row_imgs = pngs[row_start : row_start + COLS]
            cols = st.columns(COLS)
            for col, img_path in zip(cols, row_imgs):
                with col:
                    caption = os.path.basename(img_path).replace("_overlay.png", "")
                    st.image(img_path, caption=caption, use_container_width=True)

    if not any_overlays:
        st.info("No cell mask overlay images found yet. Run the analysis first.")

    # ── Excel download ────────────────────────────────────────────────────────
    excel_path = os.path.join(display_save_dir, "cellpose_results.xlsx")
    if os.path.exists(excel_path):
        st.divider()
        with open(excel_path, "rb") as f:
            st.download_button("Download Results Excel", f,
                               "cellpose_results.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
