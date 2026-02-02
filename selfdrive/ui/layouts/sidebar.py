"""
Sidebar adapter - uses BluePilot's modular sidebar implementation
"""
from bluepilot.ui.widgets.sidebar import SidebarBP
from bluepilot.ui.lib.constants import BPConstants

# Export SidebarBP as Sidebar for compatibility
Sidebar = SidebarBP

# Export width constant
SIDEBAR_WIDTH = BPConstants.SIDEBAR_WIDTH
