# SubiPilot

SubiPilot is a Subaru-first fork for comma devices maintained by `MostlyClueless94`.
The active `MostlyClueless` development branch is now based on BluePilot 6.0, with Subaru compatibility and SubiPilot-specific UI polish layered on top.

## Branches

- `subi-1.0`: stable branch for existing users
- `subi-staging`: broader validation branch
- `MostlyClueless`: active development branch

## Install URLs

- Stable: `https://installer.comma.ai/MostlyClueless94/subi-1.0`
- Testing: `https://installer.comma.ai/MostlyClueless94/subi-staging`
- Development: `https://installer.comma.ai/MostlyClueless94/MostlyClueless`

## Credits

SubiPilot is built on top of work from:

- [BluePilotDev/bluepilot](https://github.com/BluePilotDev/bluepilot)
- [sunnypilot/sunnypilot](https://github.com/sunnypilot/sunnypilot)
- [commaai/openpilot](https://github.com/commaai/openpilot)

SubiPilot builds on work that would not have been possible without Jacob Waller and BluePilot.

Thank you to Jacob Waller for publishing Subaru-related work that served as an important reference point while expanding Subaru support in this fork.

Thank you as well to BluePilot for making their work publicly available. In direct testing, the BluePilot-based stack was found to provide better Subaru control behavior than base SunnyPilot and stock openpilot, and that result strongly influenced the direction of this project.

SubiPilot is a separate fork, but it is built with clear appreciation for the publicly released work that helped make it possible.

## Scope

This repository keeps the current `MostlyClueless -> subi-staging -> subi-1.0` promotion flow.
Truck-specific and Subaru-specific work should continue to be validated on `MostlyClueless` before anything is promoted to the broader branches.

## Licensing

This repository contains original work as well as code derived from BluePilot, sunnypilot, and commaai/openpilot.
See [LICENSE](LICENSE) and [LICENSE.md](LICENSE.md) for the applicable terms and required notices.
