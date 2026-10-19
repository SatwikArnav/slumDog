# Shanti Nagar — Mumbai-inspired environment, first street section

This Blender 4.0 environment develops the approved Indian basti direction as a detailed street section: a roughly 28-metre gully, tea stall, local shops, residential fronts, and a branching workshop courtyard. Surrounding buildings suggest the continuation of the neighbourhood. This is a fictional place informed by Dharavi references, not a reconstruction of a named real street.

## View the scene

Open Shanti_Nagar_Level.blend. Textures are packed. The Street walkthrough camera is animated at walking height; Numpad 0 enters the camera view. Space plays the scene. Timeline markers identify the entrance, tea stall, tarp-covered section, and courtyard. The smoking character retains its anatomical skin rig and original 216-frame action.

Material Preview shows the textures; Rendered mode shows final lighting and smoke. A rendered MP4 and stills are supplied for convenient inspection without Blender. The lightweight environment preview is sampled below the native animation frame rate and interpolated for playback, with volumetric smoke disabled. The Blender scene retains the editable smoke effects.

Collections separate Architecture, Roofs and terraces, Street infrastructure, Shopfronts and signs, Domestic props, Reusable CC0 props, Character, Lighting, Cameras, and Collision. Collision contains simple hidden building volumes. These are starting volumes, not a tested engine navigation mesh or complete game collision system.

## Art and layout

Incremental brick-and-plaster construction, upper-storey additions, tin awnings, rooftop water tanks, window grilles, service pipes, overhead cables, a blue tarp canopy, patched concrete, drain crossings, local-language signs, a tea counter, household storage, plants, and drying clothes establish the street character. Detail is concentrated at pedestrian height. Wear follows exposed edges and water paths, with maintained domestic areas alongside weathered surfaces.

The level is an editable environment scene, not a standalone playable game. The finished street section establishes the visual direction before expanding the entire planned neighbourhood. Additional interiors, a varied population, sound, engine-specific lighting, collision, and performance work remain separate production steps.

## Rebuild

The raylib version now has five expanded, furnished shop interiors. Its exporter
applies `upgrade_shops.py` to this original scene before baking textures. Run
`blender -b --python upgrade_shops.py` from this directory to save an editable
`Shanti_Nagar_Shops.blend` with those changes. The original scene remains intact.

Use Blender 4.0 or compatible newer versions:

    blender -b --python build_level.py

The script saves the native scene and renders review stills. Keep assets beside it. The source package includes the original character input under ../character/Rook_Rebuilt.blend. Procedural materials and volumetric smoke are native Blender effects; a game-engine export will need material baking/conversion and an engine smoke implementation.

## Reference sources

- URBZ — Homegrown Street / Sangam Gully: https://www.urbz.net/homegrown
- URBZ — The Story of a Lane in Dharavi / Bareilly Compound: https://www.urbz.net/articles/story-lane-dharavi
- CEPT — Remodelling Kumbharwada: https://portfolio.cept.ac.in/fp/from-utopias-to-heterotopias-migrant-housing-values-of-time-density-culture-and-energy-ur2005-spring-2020/from-utopias-to-hetertopias-remodelling-kumbharwada-spring-2020-ua6717
- Wikimedia — Streets in Dharavi: https://commons.wikimedia.org/wiki/Category:Streets_in_Dharavi

Reference photographs were used as research, not embedded as texture assets.

## Reused assets and credits

Poly Haven assets are CC0: https://polyhaven.com/license

- Concrete Wall 003 texture — Dimitrios Savva and Rico Cilliers: https://polyhaven.com/a/concrete_wall_003
- Corrugated Iron 02 texture — Sergej Majboroda and Jenelle van Heerden: https://polyhaven.com/a/corrugated_iron_02
- Plastic Monobloc Chair 01 — Kuutti Siitonen: https://polyhaven.com/a/plastic_monobloc_chair_01
- Barrel 02 — Jorge Camacho: https://polyhaven.com/a/Barrel_02

Human topology, morphs, textures, source skeleton and skin weights originate from MakeHuman CC0 graphical assets, adapted in the preceding Rook character project. See the character's embedded START HERE text for its original credits.

Noto Sans Devanagari is distributed under the SIL Open Font License; its license is included with the font. Local signage, layout, modular architecture, scene dressing, procedural materials, camera work, and scene assembly were created for this environment.
