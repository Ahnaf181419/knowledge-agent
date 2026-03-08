"""
Material Design Theme CSS
Dual theme support: light/dark with softer, readable colors
"""

import streamlit as st


def apply_custom_styles():
    """Apply Material Design styles with light/dark theme support"""
    
    theme = st.session_state.get('theme', 'dark')
    
    if theme == 'light':
        apply_light_theme()
    else:
        apply_dark_theme()


def apply_dark_theme():
    """Apply dark theme with softer, readable colors"""
    
    st.markdown("""
    <style>
    /* CSS Variables - Dark Theme (Soft) */
    :root {
        --bg-primary: #1a1a2e;
        --bg-secondary: #16213e;
        --bg-tertiary: #1f2940;
        --bg-input: #232d42;
        --border-color: #2d3a52;
        --text-primary: #e8eaed;
        --text-secondary: #a8b2c1;
        --text-muted: #6b7785;
        --accent-color: #5c9eff;
        --accent-hover: #4a8ae8;
        --accent-light: rgba(92, 158, 255, 0.15);
        --success-color: #4ade80;
        --warning-color: #fbbf24;
        --error-color: #f87171;
        --info-color: #60a5fa;
    }
    
    /* Base Styles */
    * {
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    /* Hide Sidebar */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Hide native nav */
    [data-testid="stSidebarNav"] { 
        display: none !important; 
    }
    
    /* Main Content */
    .main .block-container {
        padding: 1.5rem;
        max-width: 100%;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--accent-color);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-hover);
    }
    
    .stButton > button[kind="secondary"] {
        background-color: transparent;
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--bg-input);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-color);
        box-shadow: 0 0 0 2px var(--accent-light);
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-muted);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--text-primary);
        font-size: 1.75rem;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricDelta"] {
        color: var(--success-color);
    }
    
    /* Alerts */
    .stSuccess { 
        background-color: rgba(74, 222, 128, 0.1); 
        border-left: 3px solid var(--success-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    .stError { 
        background-color: rgba(248, 113, 113, 0.1); 
        border-left: 3px solid var(--error-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    .stWarning { 
        background-color: rgba(251, 191, 36, 0.1); 
        border-left: 3px solid var(--warning-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    .stInfo { 
        background-color: rgba(96, 165, 250, 0.1); 
        border-left: 3px solid var(--info-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    
    /* Code */
    code {
        background-color: var(--bg-tertiary);
        color: #93c5fd;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.875rem;
    }
    
    pre code {
        color: var(--text-primary);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3d4a62; }
    
    /* Divider */
    hr {
        border-color: var(--border-color);
        margin: 1rem 0;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: var(--border-color);
    }
    
    .stProgress > div > div > div > div {
        background-color: var(--accent-color);
    }
    
    /* Dataframe/Tables */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    /* Cards */
    .ka-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 8px;
    }
    
    .ka-card-header {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .ka-stat-value {
        font-size: 28px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .ka-stat-label {
        font-size: 11px;
        color: var(--text-secondary);
        text-transform: uppercase;
    }
    
    /* Badges - softer colors */
    .ka-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
    }
    
    .ka-badge-blue { background: rgba(92, 158, 255, 0.2); color: #93c5fd; }
    .ka-badge-green { background: rgba(74, 222, 128, 0.2); color: #86efac; }
    .ka-badge-orange { background: rgba(251, 191, 36, 0.2); color: #fcd34d; }
    .ka-badge-purple { background: rgba(167, 139, 250, 0.2); color: #c4b5fd; }
    .ka-badge-red { background: rgba(248, 113, 113, 0.2); color: #fca5a5; }
    
    /* Section headers */
    .section-header {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
    }
    
    /* URL Cards */
    .url-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    
    .url-card.pending { border-left: 3px solid var(--warning-color); }
    .url-card.completed { border-left: 3px solid var(--success-color); }
    .url-card.failed { border-left: 3px solid var(--error-color); }
    .url-card.processing { border-left: 3px solid var(--accent-color); }
    
    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .badge-pending { background: rgba(251, 191, 36, 0.2); color: #fcd34d; }
    .badge-completed { background: rgba(74, 222, 128, 0.2); color: #86efac; }
    .badge-failed { background: rgba(248, 113, 113, 0.2); color: #fca5a5; }
    .badge-processing { background: rgba(92, 158, 255, 0.2); color: #93c5fd; }
    
    /* Type Badge */
    .type-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
    }
    
    .type-normal { background: rgba(92, 158, 255, 0.2); color: #93c5fd; }
    .type-novel { background: rgba(167, 139, 250, 0.2); color: #c4b5fd; }
    .type-heavy { background: rgba(251, 191, 36, 0.2); color: #fcd34d; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        border-radius: 8px 8px 0 0;
        background: var(--bg-tertiary);
        color: var(--text-secondary);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent-color);
        color: #ffffff;
    }
    
    /* Select */
    .stSelectbox > div > div {
        background-color: var(--bg-input);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    /* Slider */
    .stSlider [data-baseweb="slider"] {
        color: var(--accent-color);
    }
    
    /* Checkbox */
    .stCheckbox > label > div:first-child {
        color: var(--text-primary);
    }
    
    .stCheckbox > label {
        color: var(--text-primary);
    }
    
    /* Radio */
    .stRadio > label > div:first-child {
        color: var(--text-primary);
    }
    
    .stRadio > label {
        color: var(--text-primary);
    }
    
    /* Number Input */
    .stNumberInput > div > div > input {
        background-color: var(--bg-input);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    /* Multiselect */
    .stMultiSelect > div > div {
        background-color: var(--bg-input);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    /* Typography */
    h1 { font-size: 1.75rem !important; color: var(--text-primary) !important; font-weight: 600 !important; }
    h2 { font-size: 1.5rem !important; color: var(--text-primary) !important; }
    h3 { font-size: 1.25rem !important; color: var(--text-primary) !important; }
    h4 { font-size: 1rem !important; color: var(--text-primary) !important; }
    
    /* Captions */
    .stCaption {
        color: var(--text-secondary);
    }
    
    /* Json output */
    .stJson {
        background-color: var(--bg-tertiary);
        border-radius: 8px;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem; }
        .ka-stat-value { font-size: 22px; }
        .main .block-container { padding: 1rem; }
    }
    
    @media (max-width: 480px) {
        .main .block-container { padding: 0.5rem; }
        h1 { font-size: 1.5rem !important; }
        .ka-card { padding: 12px; }
    }
    </style>
    """, unsafe_allow_html=True)


def apply_light_theme():
    """Apply light theme with softer, readable colors"""
    
    st.markdown("""
    <style>
    /* CSS Variables - Light Theme (Soft) */
    :root {
        --bg-primary: #f8fafc;
        --bg-secondary: #ffffff;
        --bg-tertiary: #f1f5f9;
        --bg-input: #ffffff;
        --border-color: #e2e8f0;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --accent-color: #3b82f6;
        --accent-hover: #2563eb;
        --accent-light: rgba(59, 130, 246, 0.1);
        --success-color: #22c55e;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --info-color: #3b82f6;
    }
    
    /* Base Styles */
    * {
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    /* Hide Sidebar */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Hide native nav */
    [data-testid="stSidebarNav"] { 
        display: none !important; 
    }
    
    /* Main Content */
    .main .block-container {
        padding: 1.5rem;
        max-width: 100%;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--accent-color);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-hover);
    }
    
    .stButton > button[kind="secondary"] {
        background-color: transparent;
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--bg-input);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-color);
        box-shadow: 0 0 0 2px var(--accent-light);
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-muted);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--text-primary);
        font-size: 1.75rem;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricDelta"] {
        color: var(--success-color);
    }
    
    /* Alerts */
    .stSuccess { 
        background-color: rgba(34, 197, 94, 0.08); 
        border-left: 3px solid var(--success-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    .stError { 
        background-color: rgba(239, 68, 68, 0.08); 
        border-left: 3px solid var(--error-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    .stWarning { 
        background-color: rgba(245, 158, 11, 0.08); 
        border-left: 3px solid var(--warning-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    .stInfo { 
        background-color: rgba(59, 130, 246, 0.08); 
        border-left: 3px solid var(--info-color); 
        border-radius: 0 8px 8px 0;
        color: var(--text-primary);
    }
    
    /* Code */
    code {
        background-color: var(--bg-tertiary);
        color: #2563eb;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.875rem;
    }
    
    pre code {
        color: var(--text-primary);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #cbd5e1; }
    
    /* Divider */
    hr {
        border-color: var(--border-color);
        margin: 1rem 0;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: var(--border-color);
    }
    
    .stProgress > div > div > div > div {
        background-color: var(--accent-color);
    }
    
    /* Dataframe/Tables */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    /* Cards */
    .ka-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .ka-card-header {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    .ka-stat-value {
        font-size: 28px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .ka-stat-label {
        font-size: 11px;
        color: var(--text-secondary);
        text-transform: uppercase;
    }
    
    /* Badges - softer colors */
    .ka-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
    }
    
    .ka-badge-blue { background: rgba(59, 130, 246, 0.12); color: #1d4ed8; }
    .ka-badge-green { background: rgba(34, 197, 94, 0.12); color: #16a34a; }
    .ka-badge-orange { background: rgba(245, 158, 11, 0.12); color: #d97706; }
    .ka-badge-purple { background: rgba(139, 92, 246, 0.12); color: #7c3aed; }
    .ka-badge-red { background: rgba(239, 68, 68, 0.12); color: #dc2626; }
    
    /* Section headers */
    .section-header {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-color);
    }
    
    /* URL Cards */
    .url-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    
    .url-card.pending { border-left: 3px solid var(--warning-color); }
    .url-card.completed { border-left: 3px solid var(--success-color); }
    .url-card.failed { border-left: 3px solid var(--error-color); }
    .url-card.processing { border-left: 3px solid var(--accent-color); }
    
    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .badge-pending { background: rgba(245, 158, 11, 0.12); color: #d97706; }
    .badge-completed { background: rgba(34, 197, 94, 0.12); color: #16a34a; }
    .badge-failed { background: rgba(239, 68, 68, 0.12); color: #dc2626; }
    .badge-processing { background: rgba(59, 130, 246, 0.12); color: #1d4ed8; }
    
    /* Type Badge */
    .type-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
    }
    
    .type-normal { background: rgba(59, 130, 246, 0.12); color: #1d4ed8; }
    .type-novel { background: rgba(139, 92, 246, 0.12); color: #7c3aed; }
    .type-heavy { background: rgba(245, 158, 11, 0.12); color: #d97706; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        border-radius: 8px 8px 0 0;
        background: var(--bg-tertiary);
        color: var(--text-secondary);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent-color);
        color: #ffffff;
    }
    
    /* Select */
    .stSelectbox > div > div {
        background-color: var(--bg-input);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    /* Slider */
    .stSlider [data-baseweb="slider"] {
        color: var(--accent-color);
    }
    
    /* Checkbox */
    .stCheckbox > label > div:first-child {
        color: var(--text-primary);
    }
    
    .stCheckbox > label {
        color: var(--text-primary);
    }
    
    /* Radio */
    .stRadio > label > div:first-child {
        color: var(--text-primary);
    }
    
    .stRadio > label {
        color: var(--text-primary);
    }
    
    /* Number Input */
    .stNumberInput > div > div > input {
        background-color: var(--bg-input);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    /* Multiselect */
    .stMultiSelect > div > div {
        background-color: var(--bg-input);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    /* Typography */
    h1 { font-size: 1.75rem !important; color: var(--text-primary) !important; font-weight: 600 !important; }
    h2 { font-size: 1.5rem !important; color: var(--text-primary) !important; }
    h3 { font-size: 1.25rem !important; color: var(--text-primary) !important; }
    h4 { font-size: 1rem !important; color: var(--text-primary) !important; }
    
    /* Captions */
    .stCaption {
        color: var(--text-secondary);
    }
    
    /* Json output */
    .stJson {
        background-color: var(--bg-tertiary);
        border-radius: 8px;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .stApp { padding: 0.5rem; }
        .ka-stat-value { font-size: 22px; }
        .main .block-container { padding: 1rem; }
    }
    
    @media (max-width: 480px) {
        .main .block-container { padding: 0.5rem; }
        h1 { font-size: 1.5rem !important; }
        .ka-card { padding: 12px; }
    }
    </style>
    """, unsafe_allow_html=True)
