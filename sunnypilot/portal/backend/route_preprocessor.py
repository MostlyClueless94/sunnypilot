"""
Compatibility shim for moved module

This module was moved to sunnypilot.portal.backend.routes.preprocessor during modularization.
This file provides backward compatibility for any code still importing from the old location.

DEPRECATED: Import from sunnypilot.portal.backend.routes.preprocessor instead
"""

# Re-export everything from the new location
from sunnypilot.portal.backend.routes.preprocessor import *  # noqa: F401, F403

# Support running as a script
if __name__ == "__main__":
    from sunnypilot.portal.backend.routes.preprocessor import main
    main()
