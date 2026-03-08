"""
Shadcn UI Helpers - Card containers and styling utilities
"""

from streamlit_extras.stylable_container import stylable_container


def card_container(key=None):
    """Card container with dark theme styling"""
    return stylable_container(key=key, css_styles=[
        """
        {
            background: #141414;
            border: 1px solid #252525;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }
        """,
        """
        > div:not(:first-child) {
            width: 100%;
            min-width: 1px;
            overflow: visible;
        }
        """,
        """
        > div:first-child {
            display: none;
        }
        """,
        """
        > div:not(:first-child) > iframe {
            display: inline-block;
            width: 100%;
            min-width: 1px;
            border: none;
        }
        """,
        """
        > div:not(:first-child) canvas {
            display: inline-block;
            width: 100% !important;
            min-width: 1px;
            border: none;
        }
        """
    ])
