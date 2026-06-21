# Graphics And Animation Note

The current game renders with Panda3D but uses procedural placeholder geometry: boxes, cylinders, cones, flat tile quads, and simple transform tracks. That keeps iteration fast and testable, but limits animation quality because there is no skeletal rig, keyframed model data, texture atlas, normal maps, or authored VFX.

The highest-impact improvements that fit this framework are stronger silhouettes, distinct color/material palettes, better facing math, smoother transform curves, more readable hit reactions, and deterministic terrain/detail variation. A larger jump in original low-poly fidelity would require imported models, rigged character animations, authored item sprites/models, and an asset pipeline.
