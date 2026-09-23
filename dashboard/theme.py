import streamlit as st

# ---------------------------------------------------------------------------
# GreenGrid "Aurora" theme
#   * Every inner page : LIGHT background, glass cards, DARK nav + DARK footer.
#   * Home ONLY        : apply_theme("dark") -> dark background all the way down.
#     After the earth scroll-zoom, parallax_css() adds a two-layer scroll
#     parallax band built from parallax_thermal.jpg + parallax_aurora.jpg.
#   * Two font families only: Space Grotesk (display: big headings & stat
#     numbers) and Inter (everything else, including sub-headings/h3/h4).
# ---------------------------------------------------------------------------
LIGHT = {
    "mist": "#FAF7F2",                    # page background
    "mist_rgb": "250,247,242",            # same colour, components only (for rgba() use)
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
    "mist_rgb": "10,18,20",
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

# Deterministic category -> colour mapping (used by Driver Analysis instead of
# cycling colours by row position, so colour actually encodes something).
CATEGORY_COLORS = {
    "surface": "#D9603B",
    "vegetation": "#2E7D6B",
    "density": "#4A90C4",
    "climate": "#7FC4B1",
    "geometry": "#F08A67",
}
CATEGORY_FALLBACK_COLOR = "#8DBCE0"

# One distinct colour per driver (Driver Analysis). Assigned by rank in the full
# driver ranking, so the top 6 are always six different colours and a driver
# keeps the same colour everywhere it appears on the page.
DRIVER_COLORS = [
    "#D9603B",  # coral
    "#4A90C4",  # blue
    "#2E7D6B",  # green
    "#D4941A",  # amber
    "#8A5BB5",  # purple
    "#C2477A",  # rose
    "#3AA7B8",  # cyan
    "#7FA83A",  # lime
    "#5B6C8F",  # slate blue
    "#A0674B",  # clay
    "#E07A5F",  # light coral
    "#6B7280",  # grey
]

PAGES = {
    "hotspot":  {"label": "hotspot maps",       "file": "pages/1_Hotspot_Map.py"},
    "driver":   {"label": "driver analysis",    "file": "pages/2_Driver_Analysis.py"},
    "scenario": {"label": "scenario simulator", "file": "pages/3_Scenario_Simulator.py"},
    "optimizer":{"label": "optimizer",          "file": "pages/4_Optimizer.py"},
}


def apply_theme(mode="light"):
    """Call once near the top of every page, including Home.

    Inner pages use mode="light" (default). Home alone uses mode="dark".
    The nav bar and footer are dark in both modes.

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

    # ---- page background (flat, no fixed backdrop) ----
    if dark:
        glow_g, glow_c, glow_b, grid_ln = ".18", ".14", ".16", "rgba(255,255,255,.035)"
    else:
        glow_g, glow_c, glow_b, grid_ln = ".13", ".11", ".12", "rgba(30,43,46,.035)"
    bg_css = f"""
    html, body, .stApp, [data-testid="stApp"] {{ background:{c['mist']} !important; color:{c['slate']}; }}
    .stApp {{ isolation:isolate; }}
    [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"] {{ background:transparent !important; }}
    /* faint colour glows + city grid so the glass cards have something to blur */
    .stApp::before {{ content:""; position:fixed; inset:0; z-index:-1; pointer-events:none;
        background:
            radial-gradient(600px 420px at 8% 4%,   rgba(46,125,107,{glow_g}), transparent 70%),
            radial-gradient(720px 520px at 92% 14%, rgba(217,96,59,{glow_c}),  transparent 70%),
            radial-gradient(640px 520px at 50% 104%, rgba(74,144,196,{glow_b}), transparent 70%),
            linear-gradient({grid_ln} 1px, transparent 1px) 0 0/40px 40px,
            linear-gradient(90deg, {grid_ln} 1px, transparent 1px) 0 0/40px 40px; }}
    """

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{ font-family:'Inter',sans-serif; color-scheme:{'dark' if dark else 'light'}; }}
    {bg_css}
    /* Two-family system: Space Grotesk for big display headings & stat numbers,
       Inter (bold) for everything else — sub-headings, card titles, body text. */
    h1, h2 {{ font-family:'Space Grotesk',sans-serif; font-weight:600; }}
    h3, h4, h5, h6 {{ font-family:'Inter',sans-serif; font-weight:700; }}
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
    /* tap target: min-height 44px per WCAG 2.5.5 / 2.5.8 guidance, was 6px/10px padding before */
    .st-key-top_nav [data-testid="stPageLink"] a {{ border-radius:8px; padding:12px 14px; min-height:44px;
        display:inline-flex; align-items:center; justify-content:center; line-height:1; box-sizing:border-box; }}
    .st-key-top_nav [data-testid="stPageLink"] a:hover {{ background:rgba(255,255,255,.08); }}
    .st-key-top_nav [data-testid="stPageLink"] a:hover p {{ color:#fff; }}
    .st-key-top_nav a:focus-visible {{ outline-color:#4DB397; }}
    .tab-active {{ font-size:14px; font-weight:600; color:{ON_DARK}; border-bottom:2px solid #4DB397; padding-bottom:4px; width:fit-content; line-height:1.4;
        min-height:44px; display:inline-flex; align-items:center; box-sizing:border-box; }}

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
    .sec-sub {{ font-size:15.5px; color:{c['slate_60']}; max-width:640px; line-height:1.65; margin-bottom:8px; }}
    .page-title {{ font-family:'Space Grotesk',sans-serif; font-size:2rem; font-weight:600; color:{c['slate']}; margin:0 0 14px 0; }}

    /* ---- Glass cards / chips / stats / rows / bars / buttons ---- */
    .chip {{ display:inline-block; {glass} font-size:12px; padding:6px 12px; border-radius:20px; margin-right:8px; color:{c['slate']}; }}
    .card {{ {glass} border-radius:12px; padding:14px 16px; }}
    /* renamed from "card-white": it was never white in dark contexts, just a glass panel */
    .card-surface {{ {glass} border-radius:14px; padding:20px 22px; }}
    .card-glass-green {{ {glass} background:{c['green_glass']}; border-color:{c['green_glass_border']}; border-radius:12px; padding:16px 14px; }}
    .stat {{ font-family:'Inter',sans-serif; font-weight:600; font-size:16px; color:{c['slate']}; }}
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

    /* ---- Real button-styled page links (for primary/secondary CTAs) ----
       Wrap st.page_link calls in st.container(key="cta-primary") or
       st.container(key="cta-outline") to get real button treatment instead
       of a bare text link — used for the two homepage hero CTAs so the most
       important actions on the site get the strongest visual weight. ---- */
    .st-key-cta-primary [data-testid="stPageLink"] a {{
        background:#2E7D6B; border-radius:8px; padding:12px 20px; min-height:44px;
        display:inline-flex; align-items:center; justify-content:center; box-sizing:border-box;
    }}
    .st-key-cta-primary [data-testid="stPageLink"] p {{ color:#fff !important; font-weight:600; font-size:14.5px; }}
    .st-key-cta-primary [data-testid="stPageLink"] a:hover {{ opacity:.9; }}
    .st-key-cta-outline [data-testid="stPageLink"] a {{
        border:1px solid {c['border']}; border-radius:8px; padding:12px 20px; min-height:44px;
        display:inline-flex; align-items:center; justify-content:center; box-sizing:border-box;
    }}
    .st-key-cta-outline [data-testid="stPageLink"] p {{ color:{c['slate']} !important; font-weight:600; font-size:14.5px; }}
    .st-key-cta-outline [data-testid="stPageLink"] a:hover {{ background:{c['bar_bg']}; }}

    /* ---- Page pieces ---- */
    .st-key-controls_panel {{ {glass} border-radius:14px; padding:14px 18px 20px 18px; }}
    .st-key-controls_panel h3 {{ font-size:1.1rem; margin:4px 0 14px 0; }}
    .section-label {{ font-size:.9rem; font-weight:600; color:{c['slate']}; margin:14px 0 6px 0; }}
    .legend-box {{ {glass} border-radius:10px; padding:10px 12px; font-size:.85rem; color:{c['slate']}; }}
    .legend-gradient {{ width:100%; height:12px; border-radius:3px; margin:6px 0 4px 0; background:linear-gradient(to right,#4575b4,#ffffbf,#d73027); }}
    .legend-scale {{ display:flex; justify-content:space-between; color:{c['slate_60']}; }}
    iframe {{ border-radius:12px; }}

    /* ---- Streamlit widget re-skin ---- */
    .stButton>button, .stDownloadButton>button {{ background-color:#2E7D6B; color:#fff; border-radius:8px; border:none; font-weight:600; min-height:44px; }}
    .stButton>button:hover, .stDownloadButton>button:hover {{ opacity:.9; color:#fff; }}
    /* button labels live in a <p> that the global "p {{ color }}" rule would otherwise darken */
    .stButton>button *, .stDownloadButton>button * {{ color:#fff !important; }}
    [data-testid="stMetric"] {{ {glass} border-radius:12px; padding:14px 16px; }}
    [data-testid="stMetricValue"] {{ font-family:'Inter',sans-serif; font-weight:700; color:{c['slate']}; }}
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


def parallax_css(aurora=None, thermal=None):
    """Scroll parallax band for Home, placed right after the earth scroll-zoom.

    Three depths move at different speeds while the band scrolls through the
    viewport:  thermal (back, slower than the page)  ->  copy (page speed)  ->
    aurora (front, faster than the page, screen-blended over the thermal layer).
    Driven by CSS scroll-driven animations (Chromium / Edge 115+, Safari 26+).
    Where unsupported, or with prefers-reduced-motion, the layers just stay still.

    aurora / thermal : base64-encoded JPEG strings. Either can be None; the band
                       then falls back to a dark gradient so the page still works.
    """
    def _bg(b64, pos="center"):
        if not b64:
            return "display:none;"
        return f"background:url(data:image/jpeg;base64,{b64}) {pos}/cover no-repeat;"

    st.markdown(f"""
    <style>
    .para-band {{ position:relative; height:39vh; min-height:240px; overflow:hidden; isolation:isolate;
        border-radius:16px; margin:8px 0; display:flex; align-items:center; justify-content:center;
        background:
            radial-gradient(ellipse 60% 55% at 28% 30%, rgba(217,96,59,.38), transparent 70%),
            radial-gradient(ellipse 60% 55% at 76% 74%, rgba(74,144,196,.32), transparent 70%),
            #060C0E;
        view-timeline-name:--paraBand; view-timeline-axis:block; }}
    .para-layer {{ position:absolute; left:0; right:0; pointer-events:none; will-change:transform; }}
    .para-thermal {{ inset:-30% 0; z-index:0; {_bg(thermal)} filter:saturate(1.1); }}
    .para-aurora  {{ inset:-45% 0; z-index:1; {_bg(aurora)} mix-blend-mode:screen; opacity:.85; }}
    /* darkens the artwork a little so the copy panel stays readable, and vignettes the edges */
    .para-veil {{ position:absolute; inset:0; z-index:2; pointer-events:none;
        background:radial-gradient(ellipse at center, rgba(5,9,11,.30) 0%, rgba(5,9,11,.55) 100%); }}
    .para-content {{ position:relative; z-index:3; padding:0 24px; width:100%; max-width:760px; text-align:center; }}
    .para-copy {{ background:linear-gradient(135deg,rgba(255,255,255,.10),rgba(255,255,255,.03)),rgba(10,18,20,.62);
        border:1px solid rgba(255,255,255,.16);
        backdrop-filter:blur(18px) saturate(140%); -webkit-backdrop-filter:blur(18px) saturate(140%);
        border-radius:16px; padding:34px 32px; box-shadow:0 10px 34px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.14); }}
    .para-copy, .para-copy p, .para-copy span {{ color:#F3F6F5; }}
    .para-copy p {{ font-family:'Space Grotesk',sans-serif; font-size:21px; line-height:1.5; margin:0 auto; max-width:620px; }}
    .para-copy .eyebrow {{ display:block; color:#4DB397; }}
    @supports (animation-timeline: view()) {{
        .para-layer {{ animation-duration:1s; animation-fill-mode:both; animation-timing-function:linear;
            animation-timeline:--paraBand; animation-range:cover 0% cover 100%; }}
        .para-thermal {{ animation-name:paraBack; }}
        .para-aurora  {{ animation-name:paraFront; }}
    }}
    @keyframes paraBack  {{ from {{ transform:translateY(-10%) scale(1.04); }} to {{ transform:translateY(10%) scale(1.04); }} }}
    @keyframes paraFront {{ from {{ transform:translateY(14%); }} to {{ transform:translateY(-14%); }} }}
    @media (prefers-reduced-motion: reduce) {{ .para-layer {{ animation:none !important; }} }}
    </style>
    """, unsafe_allow_html=True)


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