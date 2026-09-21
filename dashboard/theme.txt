import streamlit as st

# ---------------------------------------------------------------------------
# GreenGrid "Aurora" theme
#   * Inner pages : LIGHT background, glass cards, DARK nav bar + DARK footer
#   * Home page   : DARK background with an animated aurora-wave parallax layer
# Same brand accents in both modes (Urban Green / Thermal Coral / Sky Blue).
# ---------------------------------------------------------------------------
LIGHT = {
    "mist": "#FAF7F2",                    # page background
    "panel": "#E9EEEA",
    "card": "#FFFFFF",
    "slate": "#1E2B2E",                   # primary text
    "slate_60": "rgba(30,43,46,.72)",     # secondary text  (>= 5.9:1 on mist)
    "slate_45": "rgba(30,43,46,.55)",
    "coral": "#D9603B",
    "coral_dark": "#7A2E17",
    "coral_tint": "#F3D9CB",
    "coral_text": "#B8431F",              # coral that passes AA as text on light
    "green": "#2E7D6B",
    "green_dark": "#1F5A4C",
    "green_light": "#2E7D6B",
    "green_tint": "#E3F0EA",
    "green_text": "#1F5A4C",
    "green_glass": "linear-gradient(135deg, rgba(46,125,107,.16), rgba(46,125,107,.05))",
    "green_glass_border": "rgba(46,125,107,.30)",
    "blue": "#4A90C4",
    "border": "rgba(30,43,46,.12)",
    "glass_bg": "linear-gradient(135deg, rgba(255,255,255,.80), rgba(255,255,255,.48))",
    "glass_border": "rgba(30,43,46,.10)",
    "glass_shadow": "0 8px 30px rgba(30,43,46,.08), inset 0 1px 0 rgba(255,255,255,.9)",
    "bar_bg": "rgba(30,43,46,.08)",
    "input_bg": "rgba(255,255,255,.75)",
    "popover": "#FFFFFF",
}

DARK = {
    "mist": "#0A1214",
    "panel": "#172327",
    "card": "#1E2B2E",
    "slate": "#F3F6F5",
    "slate_60": "rgba(243,246,245,.86)",
    "slate_45": "rgba(243,246,245,.62)",
    "coral": "#D9603B",
    "coral_dark": "#F08A67",
    "coral_tint": "rgba(217,96,59,.22)",
    "coral_text": "#F08A67",
    "green": "#2E7D6B",
    "green_dark": "#1F5A4C",
    "green_light": "#4DB397",
    "green_tint": "rgba(46,125,107,.2)",
    "green_text": "#4DB397",
    "green_glass": "linear-gradient(135deg, rgba(46,125,107,.32), rgba(46,125,107,.10)), rgba(10,18,20,.45)",
    "green_glass_border": "rgba(77,179,151,.38)",
    "blue": "#4A90C4",
    "border": "rgba(255,255,255,.14)",
    "glass_bg": "linear-gradient(135deg, rgba(255,255,255,.10), rgba(255,255,255,.03)), rgba(10,18,20,.5)",
    "glass_border": "rgba(255,255,255,.16)",
    "glass_shadow": "0 8px 32px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.14)",
    "bar_bg": "rgba(243,246,245,.1)",
    "input_bg": "rgba(255,255,255,.07)",
    "popover": "#172327",
}

# Pages import C for accent colours only (identical in both modes).
C = LIGHT

NAV_BG = "linear-gradient(180deg,#132024,#0D1719)"
FOOT_BG = "linear-gradient(180deg,#0D1719,#0A1214)"
ON_DARK = "#F3F6F5"

PAGES = {
    "hotspot":  {"label": "hotspot maps",       "file": "pages/1_Hotspot_Map.py"},
    "driver":   {"label": "driver analysis",    "file": "pages/2_Driver_Analysis.py"},
    "scenario": {"label": "scenario simulator", "file": "pages/3_Scenario_Simulator.py"},
    "optimizer":{"label": "optimizer",          "file": "pages/4_Optimizer.py"},
}


def apply_theme(mode="light", backdrop=None):
    """Call once near the top of every page.

    mode     : "light" (inner pages) or "dark" (Home).
    backdrop : optional base64 JPEG. When given (Home), it becomes an animated,
               two-layer aurora parallax behind the whole page.
    Returns the active palette dict.
    """
    dark = mode == "dark"
    c = DARK if dark else LIGHT
    glass = (
        f"background:{c['glass_bg']}; "
        "backdrop-filter:blur(16px) saturate(140%); -webkit-backdrop-filter:blur(16px) saturate(140%); "
        f"border:1px solid {c['glass_border']}; box-shadow:{c['glass_shadow']};"
    )

    # ---- layout: no sidebar, no Streamlit header, edge-to-edge bars ----
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    header[data-testid="stHeader"] { display: none; }
    html { overflow-x: hidden; }
    [data-testid="stMain"] { overflow-x: hidden; }
    [data-testid="stMainBlockContainer"], .main .block-container {
        max-width: 1440px !important;
        padding: 0 40px 0 40px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---- page background ----
    if backdrop:
        bg_css = f"""
    html, body, .stApp, [data-testid="stApp"] {{ background:{c['mist']} !important; color:{c['slate']}; }}
    .stApp {{ isolation:isolate; --aurora:url(data:image/jpeg;base64,{backdrop}); }}
    [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{ background:transparent !important; }}
    /* dark scrim keeps light text readable (WCAG AA, 4.5:1+) without hiding the waves */
    [data-testid="stAppViewContainer"] {{ background:rgba(5,9,11,.48) !important; }}
    .stApp::before, .stApp::after {{ content:""; position:fixed; z-index:-1; pointer-events:none; will-change:transform;
        filter:saturate(1.05) brightness(.95); }}
    .stApp::before {{ inset:-8%; background:var(--aurora) center/cover no-repeat; animation:aurora-a 70s ease-in-out infinite alternate; }}
    .stApp::after  {{ inset:-12%; background:var(--aurora) 30% 70%/cover no-repeat; opacity:.55; mix-blend-mode:screen; animation:aurora-b 110s ease-in-out infinite alternate; }}
    @keyframes aurora-a {{ from {{ transform:translate3d(-2%,-3%,0) scale(1.04); }} to {{ transform:translate3d(2%,3%,0) scale(1.14); }} }}
    @keyframes aurora-b {{ from {{ transform:translate3d(3%,2%,0) scale(-1.2,1.2); }} to {{ transform:translate3d(-3%,-2%,0) scale(-1.35,1.35); }} }}
    @media (prefers-reduced-motion: reduce) {{ .stApp::before, .stApp::after {{ animation:none; }} }}
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] span {{ text-shadow:0 2px 16px rgba(0,0,0,.85), 0 0 3px rgba(0,0,0,1); }}
        """
    elif dark:
        bg_css = f"""
    html, body, .stApp, [data-testid="stApp"] {{ background:{c['mist']} !important; color:{c['slate']}; }}
    .stApp {{ isolation:isolate; }}
    [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{ background:transparent !important; }}
    .stApp::before {{ content:""; position:fixed; inset:0; z-index:-1; pointer-events:none;
        background:
            radial-gradient(600px 420px at 10% 6%,  rgba(46,125,107,.30), transparent 70%),
            radial-gradient(720px 520px at 90% 18%, rgba(217,96,59,.24),  transparent 70%),
            radial-gradient(640px 520px at 50% 105%, rgba(74,144,196,.20), transparent 70%); }}
        """
    else:
        bg_css = f"""
    html, body, .stApp, [data-testid="stApp"] {{ background:{c['mist']} !important; color:{c['slate']}; }}
    .stApp {{ isolation:isolate; }}
    [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{ background:transparent !important; }}
    /* faint colour glows + city grid so the glass cards have something to blur */
    .stApp::before {{ content:""; position:fixed; inset:0; z-index:-1; pointer-events:none;
        background:
            radial-gradient(600px 420px at 8% 4%,   rgba(46,125,107,.13), transparent 70%),
            radial-gradient(720px 520px at 92% 14%, rgba(217,96,59,.11),  transparent 70%),
            radial-gradient(640px 520px at 50% 104%, rgba(74,144,196,.12), transparent 70%),
            linear-gradient(rgba(30,43,46,.035) 1px, transparent 1px) 0 0/40px 40px,
            linear-gradient(90deg, rgba(30,43,46,.035) 1px, transparent 1px) 0 0/40px 40px; }}
        """

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=Inter:wght@400;500;600&family=Manrope:wght@500;600&family=IBM+Plex+Sans:wght@500&display=swap');

    html, body, [class*="css"] {{ font-family:'Inter',sans-serif; color-scheme:{'dark' if dark else 'light'}; }}
    {bg_css}
    h1, h2, h3, h4 {{ font-family:'Space Grotesk',sans-serif; font-weight:600; }}
    p, span, label, div {{ color:{c['slate']}; }}
    h1, h2, h3, h4, h5, h6, li, small,
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"] {{ color:{c['slate']}; }}
    a:focus-visible, button:focus-visible, input:focus-visible, [role="button"]:focus-visible {{ outline:2px solid {c['green_text']}; outline-offset:2px; }}

    /* ---- Brand mark ---- */
    .brand {{ display:flex; align-items:center; gap:9px; font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:17px; padding-top:2px; }}
    .mark {{ display:grid; grid-template-columns:1fr 1fr; width:18px; height:18px; border-radius:4px; overflow:hidden; }}
    .mark span {{ background:#2E7D6B; }}
    .mark span:nth-child(3) {{ background:#D9603B; }}

    /* ---- DARK top nav bar (edge-to-edge background, content aligned to the
       SAME max-width/padding box as the page content below it) ---- */
    .st-key-top_nav {{
        position:relative; max-width:1440px; margin:0 auto 32px auto;
        padding:14px 40px; box-sizing:border-box; z-index:10;
    }}
    .st-key-top_nav::before {{
        content:""; position:absolute; top:0; bottom:0; left:50%; width:100vw; margin-left:-50vw;
        background:{NAV_BG}; border-bottom:1px solid rgba(255,255,255,.08); z-index:-1;
    }}
    .st-key-top_nav [data-testid="stHorizontalBlock"] {{ align-items:center; }}
    .st-key-top_nav [data-testid="column"] {{ display:flex; align-items:center; }}
    .st-key-top_nav [data-testid="stVerticalBlock"] {{ gap:0; }}
    .st-key-top_nav .brand {{ padding-top:0; line-height:1; }}
    .st-key-top_nav, .st-key-top_nav div, .st-key-top_nav p, .st-key-top_nav span {{ color:{ON_DARK}; text-shadow:none; }}
    .st-key-top_nav [data-testid="stPageLink"] {{ margin:0; }}
    .st-key-top_nav [data-testid="stPageLink"] p {{ font-family:'Inter',sans-serif; font-size:14px; color:rgba(243,246,245,.74); font-weight:400; line-height:1; }}
    .st-key-top_nav [data-testid="stPageLink"] a {{ border-radius:8px; padding:6px 10px; display:inline-flex; align-items:center; line-height:1; }}
    .st-key-top_nav [data-testid="stPageLink"] a:hover {{ background:rgba(255,255,255,.08); }}
    .st-key-top_nav [data-testid="stPageLink"] a:hover p {{ color:#fff; }}
    .st-key-top_nav a:focus-visible {{ outline-color:#4DB397; }}
    .tab-active {{ font-size:14px; font-weight:600; color:{ON_DARK}; border-bottom:2px solid #4DB397; padding-bottom:4px; width:fit-content; line-height:1.4; }}

    /* ---- DARK footer (same alignment technique as the nav bar) ---- */
    .gg-footer {{
        position:relative; max-width:1440px; margin:56px auto 0 auto;
        padding:22px 40px; box-sizing:border-box;
        display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;
    }}
    .gg-footer::before {{
        content:""; position:absolute; top:0; bottom:0; left:50%; width:100vw; margin-left:-50vw;
        background:{FOOT_BG}; border-top:1px solid rgba(255,255,255,.08); z-index:-1;
    }}
    .gg-footer, .gg-footer div, .gg-footer span {{ color:{ON_DARK}; text-shadow:none; }}
    .gg-footer .tag {{ font-size:13px; color:rgba(243,246,245,.74); }}

    /* ---- Hero / text ---- */
    .badge {{ display:inline-block; background:{c['coral_tint']}; color:{c['coral_dark']}; font-size:13px; padding:5px 12px; border-radius:20px; margin-bottom:16px; border:1px solid rgba(217,96,59,.35); }}
    .eyebrow {{ font-size:12.5px; letter-spacing:.5px; text-transform:uppercase; color:{c['green_text']}; font-weight:600; margin-bottom:8px; }}
    .sec-title {{ font-size:26px; margin-bottom:10px; max-width:900px; }}
    .sec-sub {{ font-size:14.5px; color:{c['slate_60']}; max-width:820px; line-height:1.6; margin-bottom:8px; }}
    .page-title {{ font-family:'Space Grotesk',sans-serif; font-size:2rem; font-weight:600; color:{c['slate']}; margin:0 0 14px 0; }}

    /* ---- Glass cards / chips / stats / rows / bars / buttons ---- */
    .chip {{ display:inline-block; {glass} font-size:12px; padding:6px 12px; border-radius:20px; margin-right:8px; color:{c['slate']}; }}
    .card {{ {glass} border-radius:12px; padding:14px 16px; }}
    .card-white {{ {glass} border-radius:14px; padding:20px 22px; }}
    .card-glass-green {{ {glass} background:{c['green_glass']}; border-color:{c['green_glass_border']}; border-radius:12px; padding:16px 14px; }}
    .stat {{ font-family:'IBM Plex Sans',sans-serif; font-weight:500; font-size:16px; color:{c['slate']}; }}
    .stat-lg {{ font-family:'Space Grotesk',sans-serif; font-size:26px; font-weight:600; color:{c['coral_text']}; }}
    .card-label {{ font-size:13px; color:{c['slate_60']}; margin:0 0 4px 0; }}
    .row {{ display:flex; justify-content:space-between; font-size:13px; {glass} border-radius:8px; padding:9px 13px; margin-bottom:6px; align-items:center; }}
    .bar-bg {{ height:8px; border-radius:4px; background:{c['bar_bg']}; }}
    .bar {{ height:100%; border-radius:4px; }}
    .btn-tag {{ display:inline-block; font-size:12.5px; font-weight:500; padding:9px 16px; border-radius:6px; }}
    .btn-primary-tag {{ background:#2E7D6B; color:#fff; }}
    .btn-outline-tag {{ border:1px solid {c['border']}; color:{c['slate']}; }}
    .btn-alert-tag {{ background:#C24E29; color:#fff; }}
    .heatgrad {{ height:190px; border-radius:10px; background:linear-gradient(135deg,{c['blue']} 0%,{c['green']} 45%,{c['coral']} 100%); position:relative; }}

    /* ---- Page pieces ---- */
    .st-key-controls_panel {{ {glass} border-radius:14px; padding:14px 18px 20px 18px; }}
    .st-key-controls_panel h3 {{ font-size:1.1rem; margin:4px 0 14px 0; }}
    .section-label {{ font-size:.9rem; font-weight:600; color:{c['slate']}; margin:14px 0 6px 0; }}
    .legend-box {{ {glass} border-radius:10px; padding:10px 12px; font-size:.85rem; color:{c['slate']}; }}
    .legend-gradient {{ width:100%; height:12px; border-radius:3px; margin:6px 0 4px 0; background:linear-gradient(to right,#4575b4,#ffffbf,#d73027); }}
    .legend-scale {{ display:flex; justify-content:space-between; color:{c['slate_60']}; }}
    iframe {{ border-radius:12px; }}

    /* ---- Streamlit widget re-skin ---- */
    .stButton>button, .stDownloadButton>button {{ background-color:#2E7D6B; color:#fff; border-radius:8px; border:none; font-weight:500; }}
    .stButton>button:hover, .stDownloadButton>button:hover {{ opacity:.9; color:#fff; }}
    [data-testid="stMetric"] {{ {glass} border-radius:12px; padding:14px 16px; }}
    [data-testid="stMetricValue"] {{ font-family:'IBM Plex Sans',sans-serif; color:{c['slate']}; }}
    [data-testid="stMetricLabel"] {{ color:{c['slate_60']}; }}
    [data-testid="stDataFrame"] {{ {glass} border-radius:12px; overflow:hidden; }}
    [data-testid="stExpander"] {{ {glass} border-radius:12px; }}
    [data-baseweb="select"] > div, [data-baseweb="input"] > div {{ background-color:{c['input_bg']} !important; border-color:{c['border']} !important; backdrop-filter:blur(12px); }}
    /* ---- Selectbox / multiselect (Streamlit >= 1.5x uses React Aria, NOT BaseWeb, so hook on
       data-testid + ARIA roles). Colours are forced so they stay readable even when the
       browser/OS is in dark mode and Streamlit picks its dark theme. ---- */
    /* the dropdown list panel */
    [data-testid="stSelectboxVirtualDropdown"], [data-testid="stMultiSelectDropdown"] {{
        background-color:{c['popover']} !important; border:1px solid {c['border']}; border-radius:10px;
        box-shadow:0 12px 32px rgba(0,0,0,.18); backdrop-filter:none !important; -webkit-backdrop-filter:none !important; opacity:1 !important; }}
    /* option text sits inside a stMarkdownContainer that this theme colours slate -> keep it slate on the light panel */
    [data-testid="stSelectboxVirtualDropdown"] *, [data-testid="stMultiSelectDropdown"] * {{ color:{c['slate']} !important; text-shadow:none !important; }}
    /* hovered / keyboard-focused / selected row */
    [data-testid="stSelectboxVirtualDropdown"] [data-hovered] [data-item-hl], [data-testid="stSelectboxVirtualDropdown"] [data-focused] [data-item-hl],
    [data-testid="stSelectboxVirtualDropdown"] [aria-selected="true"] [data-item-hl], [data-testid="stSelectboxVirtualDropdown"] [data-selected] [data-item-hl],
    [data-testid="stMultiSelectDropdown"] [data-hovered] [data-item-hl], [data-testid="stMultiSelectDropdown"] [data-focused] [data-item-hl],
    [data-testid="stMultiSelectDropdown"] [aria-selected="true"] [data-item-hl] {{ background-color:{c['green_tint']} !important; }}
    /* the closed box */
    [data-testid="stSelectbox"] [role="group"], [data-testid="stMultiSelect"] [role="group"] {{ background-color:{c['input_bg']} !important; border-color:{c['border']} !important; }}
    [data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input, [data-testid="stSelectbox"] button, [data-testid="stSelectbox"] svg {{ color:{c['slate']} !important; }}
    .stSelectbox label, .stSlider label, .stMultiSelect label {{ font-size:13px; color:{c['slate_60']}; }}
    </style>
    """, unsafe_allow_html=True)

    return c


def style_fig(fig):
    """Apply the GreenGrid look to a Plotly figure (inner pages are light)."""
    c = LIGHT
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=c["slate"]),
        colorway=[c["green"], c["coral"], c["blue"], "#7FC4B1", "#F08A67", "#8DBCE0"],
    )
    fig.update_xaxes(gridcolor=c["border"], zerolinecolor=c["border"])
    fig.update_yaxes(gridcolor=c["border"], zerolinecolor=c["border"])
    return fig


def top_nav(active):
    """Shared dark top bar (brand + 4 module tabs).
    `active` is one of: 'home', 'hotspot', 'driver', 'scenario', 'optimizer'."""
    with st.container(key="top_nav"):
        cols = st.columns([2, 1, 1, 1.3, 1])
        with cols[0]:
            if active == "home":
                st.markdown(
                    '<div class="brand"><div class="mark"><span></span><span></span><span></span><span></span></div>GreenGrid</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.page_link("Home.py", label="GreenGrid")
        for i, key in enumerate(["hotspot", "driver", "scenario", "optimizer"]):
            with cols[i + 1]:
                if active == key:
                    st.markdown(f'<div class="tab-active">{PAGES[key]["label"]}</div>', unsafe_allow_html=True)
                else:
                    st.page_link(PAGES[key]["file"], label=PAGES[key]["label"])


def footer():
    """Shared dark footer. Call once at the very end of every page."""
    st.markdown(
        '<div class="gg-footer">'
        '<div class="brand"><div class="mark"><span></span><span></span><span></span><span></span></div>GreenGrid</div>'
        '<div class="tag">Science. Data. Solutions. &nbsp;|&nbsp; Cooler cities. Stronger communities.</div>'
        '<div class="tag">greengrid.org</div>'
        '</div>',
        unsafe_allow_html=True,
    )