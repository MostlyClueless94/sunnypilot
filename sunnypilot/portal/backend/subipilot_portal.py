#!/usr/bin/env python3
"""SubiPilot Portal manager entrypoint."""


def main() -> None:
  from sunnypilot.portal.backend.bp_portal import main as portal_main

  portal_main()


if __name__ == "__main__":
  main()
