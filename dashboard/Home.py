import base64
import os
import streamlit as st
import theme as _theme

st.set_page_config(page_title="GreenGrid — cooling our cities", layout="wide")

if not hasattr(_theme, "footer"):
    st.error("theme.py is out of date. Replace it with the latest theme.py, then restart Streamlit.")
    st.stop()

from theme import apply_theme, top_nav, footer

# ---- Assets ----
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


@st.cache_data(show_spinner=False)
def _img_b64(filename: str) -> str:
    with open(os.path.join(ASSETS_DIR, filename), "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


try:
    aurora = _img_b64("parallax_aurora.jpg")   # aurora waves — page-wide parallax background
except FileNotFoundError:
    aurora = None                              # falls back to the plain dark gradient

c = apply_theme("dark", backdrop=aurora)
top_nav("home")

img_earth = _img_b64("earth_globe.png")        # hero — scroll-zoom globe

# ---- Hero (scroll-zoom globe: pinned image, alternating-side text, pure CSS) ----
# Uses CSS view-timeline / animation-timeline (scroll-driven animations, Chromium/Edge 115+).
# On browsers without support the globe simply stays at its first frame.
st.markdown(f"""
<style>
.earth-scrolly {{ position:relative; height:340vh; margin-bottom:8px;
    view-timeline-name:--earthScroll; view-timeline-axis:block; }}
.earth-stage {{ position:sticky; top:0; height:100vh; border-radius:16px; overflow:hidden;
    display:flex; align-items:center; justify-content:center; z-index:1;
    background:radial-gradient(ellipse 70% 60% at 50% 50%,{c['coral_tint']} 0%,transparent 65%),{c['mist']}; }}
.earth-img {{ width:52vmin; height:52vmin; object-fit:contain;
    filter:drop-shadow(0 0 70px rgba(217,96,59,.28));
    animation-name:earthZoom; animation-duration:1s; animation-fill-mode:both;
    animation-timing-function:ease-in-out;
    animation-timeline:--earthScroll; animation-range:cover 0% cover 100%; }}
@keyframes earthZoom {{
    0%   {{ transform:scale(1) translate(0,0); }}
    25%  {{ transform:scale(2.1) translate(32%,-10%); }}
    50%  {{ transform:scale(1.15) translate(0,0); }}
    75%  {{ transform:scale(2.1) translate(-32%,8%); }}
    100% {{ transform:scale(.6) translate(0,-10%); }}
}}
@media (prefers-reduced-motion: reduce) {{ .earth-img {{ animation:none; }} }}
.earth-text-overlay {{ position:absolute; inset:0; z-index:2; pointer-events:none; }}
.earth-stop {{ height:85vh; display:flex; align-items:center; padding:0 6vw; }}
.earth-stop.center {{ align-items:flex-end; padding-bottom:10vh; }}
.earth-copy {{ pointer-events:auto; max-width:440px;
    background:linear-gradient(135deg,rgba(255,255,255,.10),rgba(255,255,255,.03)),rgba(10,18,20,.62);
    border:1px solid {c['glass_border']};
    backdrop-filter:blur(18px) saturate(140%); -webkit-backdrop-filter:blur(18px) saturate(140%);
    border-radius:16px; padding:22px 26px; box-shadow:0 10px 34px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.14); }}
.earth-copy h1 {{ font-size:36px; line-height:1.22; margin-bottom:14px; }}
.earth-copy h2 {{ font-family:'Space Grotesk',sans-serif; font-size:26px; line-height:1.25; margin-bottom:10px; }}
.earth-copy p {{ font-size:15px; color:{c['slate_60']}; line-height:1.65; }}
.earth-stop.left  {{ justify-content:flex-start; }}
.earth-stop.right {{ justify-content:flex-end; text-align:right; }}
.earth-stop.right .earth-copy {{ margin-left:auto; }}
.earth-stop.center {{ justify-content:center; text-align:center; }}
.earth-stop.center .earth-copy {{ max-width:520px; }}
</style>
<div class="earth-scrolly">
  <div class="earth-stage">
    <img class="earth-img" src="data:image/png;base64,{img_earth}" alt="Global surface temperature" />
  </div>
  <div class="earth-text-overlay">
    <div class="earth-stop left">
      <div class="earth-copy">
        <span class="badge">Urban heat island planning</span>
        <h1>Cooling our cities,<br>one block at a time</h1>
        <p>GreenGrid combines urban systems, environmental intelligence and geospatial technology to identify heat risk and design effective cooling interventions for healthier, more resilient cities.</p>
      </div>
    </div>
    <div class="earth-stop left">
      <div class="earth-copy">
        <span class="eyebrow">Where it starts</span>
        <h2>Heat concentrates in specific blocks</h2>
        <p>A dense cluster of impervious surface and thin canopy can run degrees hotter than the streets around it — GreenGrid finds those blocks first.</p>
      </div>
    </div>
    <div class="earth-stop right">
      <div class="earth-copy">
        <span class="eyebrow">Where it pays off</span>
        <h2>Every hotspot, paired with a fix</h2>
        <p>Canopy, cool roofs, reflective pavement — GreenGrid ranks the interventions that cool each block fastest for the budget available.</p>
      </div>
    </div>
    <div class="earth-stop center">
      <div class="earth-copy">
        <h2>One dataset. Every block.</h2>
        <p>From satellite scan to funded plan — the same data carries through every step of the decision.</p>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

hcol1, hcol2, _ = st.columns([1, 1, 3])
with hcol1:
    st.page_link("pages/1_Hotspot_Map.py", label="View the plan  →")
with hcol2:
    st.page_link("pages/4_Optimizer.py", label="See the data  →")

st.write("")
st.write("")

# ---- Statement band (glass, so the aurora shows through without touching the text) ----
st.markdown(
    '<div class="card-white" style="text-align:center;padding:34px 24px;">'
    f'<p style="font-family:\'Space Grotesk\',sans-serif;font-size:19px;line-height:1.5;max-width:640px;margin:0 auto;color:{c["slate"]};">'
    'Every hotspot GreenGrid flags is <strong>traced back to a cause</strong> — '
    'and paired with an intervention sized to fix it.</p></div>',
    unsafe_allow_html=True,
)

st.write("")
st.write("")

# ---- Problem ----
st.markdown('<div class="eyebrow">The problem</div>', unsafe_allow_html=True)
st.markdown('<h2 class="sec-title">Heat isn\'t spread evenly across a city</h2>', unsafe_allow_html=True)
st.markdown(
    '<p class="sec-sub">A few square kilometres of impervious surface and low canopy can push local '
    'temperatures degrees above the citywide average — and drive the cost of cooling, health and energy '
    'for everyone nearby.</p>',
    unsafe_allow_html=True,
)
st.write("")

p1, p2, p3 = st.columns(3)
stats = [
    ("41.2°C", "Peak surface temp, Sector 4 — Industrial District"),
    ("14", "Hotspots flagged in a single scan"),
    ("-6.7°C", "Modelled reduction from a full intervention plan"),
]
for col, (n, label) in zip([p1, p2, p3], stats):
    with col:
        st.markdown(
            f'<div class="card-white"><div class="stat-lg">{n}</div>'
            f'<p style="font-size:13.5px;color:{c["slate_60"]};margin-top:4px;">{label}</p></div>',
            unsafe_allow_html=True,
        )

st.write("")
st.write("")

# ---- Solutions ----
st.markdown('<div class="eyebrow">The platform</div>', unsafe_allow_html=True)
st.markdown('<h2 class="sec-title">Four tools, one pipeline</h2>', unsafe_allow_html=True)
st.markdown(
    '<p class="sec-sub">From spotting hotspots to justifying a budget — GreenGrid carries the same '
    'data through every step of the decision.</p>',
    unsafe_allow_html=True,
)
st.write("")

tools = [
    ("Hotspot maps", "See where surface temperature runs highest, layer by season and neighbourhood.", "pages/1_Hotspot_Map.py"),
    ("Driver analysis", "Rank the physical factors — canopy, surface, density — behind each hotspot.", "pages/2_Driver_Analysis.py"),
    ("Scenario simulator", "Test canopy, cool roofs and pavement changes before committing budget.", "pages/3_Scenario_Simulator.py"),
    ("Optimizer", "Get the highest-cooling combination of interventions for a fixed budget.", "pages/4_Optimizer.py"),
]
tcols = st.columns(4)
for col, (title, desc, page) in zip(tcols, tools):
    with col:
        st.markdown(
            f'<div class="card-white"><h3 style="font-family:\'Manrope\',sans-serif;font-size:16px;'
            f'margin-bottom:6px;">{title}</h3>'
            f'<p style="font-size:13.5px;color:{c["slate_60"]};line-height:1.55;">{desc}</p></div>',
            unsafe_allow_html=True,
        )
        st.page_link(page, label="Open →")

st.write("")
st.write("")

# ---- Approach ----
st.markdown('<div class="eyebrow">Our approach</div>', unsafe_allow_html=True)
st.markdown('<h2 class="sec-title">From raw heat to a funded plan</h2>', unsafe_allow_html=True)
st.write("")

steps = [
    ("01 · Heat", "Identify hotspots", "Satellite land-surface temperature, resolved to the block."),
    ("02 · Data", "Analyze drivers", "Multi-source data explains why a block runs hot."),
    ("03 · Intervention", "Design + simulate", "Targeted solutions, tested before ground is broken."),
    ("04 · Cooler cities", "Evaluate impact", "Track cooling against cost, for healthier, livable cities."),
]
scols = st.columns(4)
for col, (num, title, desc) in zip(scols, steps):
    with col:
        st.markdown(
            f'<div class="card-white">'
            f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:14px;color:{c["coral_text"]};'
            f'font-weight:600;margin-bottom:8px;">{num}</div>'
            f'<h3 style="font-family:\'Manrope\',sans-serif;font-size:15.5px;margin-bottom:6px;">{title}</h3>'
            f'<p style="font-size:13.5px;color:{c["slate_60"]};line-height:1.55;">{desc}</p></div>',
            unsafe_allow_html=True,
        )

st.write("")
st.write("")

# ---- Audience ----
st.markdown('<div class="eyebrow">Built for</div>', unsafe_allow_html=True)
st.markdown('<h2 class="sec-title">People who shape cities</h2>', unsafe_allow_html=True)
st.write("")

audience = [
    ("Researchers", "Explainable, evidence-based models to build on."),
    ("Engineers", "Site-level metrics ready for feasibility work."),
    ("Architects", "Local heat context to inform building design."),
    ("Environmentalists", "Track canopy and cooling gains over time."),
    ("City planners", "Budget-ranked plans ready for a council meeting."),
]
acols = st.columns(5)
for col, (title, desc) in zip(acols, audience):
    with col:
        st.markdown(
            f'<div class="card-glass-green">'
            f'<h3 style="font-family:\'Manrope\',sans-serif;font-size:14.5px;margin-bottom:5px;">{title}</h3>'
            f'<p style="font-size:13px;color:{c["slate_60"]};line-height:1.5;">{desc}</p></div>',
            unsafe_allow_html=True,
        )

# ---- Footer (dark, edge to edge) ----
footer()