#!/usr/bin/env python3
"""SubiPilot Portal route-preprocessor manager entrypoint."""


def main() -> None:
  from sunnypilot.portal.backend.routes.preprocessor import main as preprocessor_main

  preprocessor_main()


if __name__ == "__main__":
  main()
