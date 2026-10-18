# Rook — rebuilt human character

Blender 4.0 scene with an anatomical human mesh, fitted field jacket and jeans, textured skin and eyes, short hair, surface stubble, a healed brow scar, and a cigarette smoking action.

## Playback

Open Rook_Rebuilt.blend in Blender 4.0 or newer. Press Space to play frames 1–216 (9 seconds at 24 fps). Camera view is Numpad 0. Rendered shading shows the smoke; Solid mode does not display volume materials.

The action starts idle, raises the right hand along an elbow-controlled arc, holds the cigarette at the lips for a draw, lowers the hand, exhales, and returns to idle. The ember brightens during the draw. There is a thin rising wisp at the cigarette tip and a separate animated exhaled plume.

## Rig controls

Select ROOK • skin rig, enter Pose Mode, and use the Controls bone collection:

- CTRL_master: move or rotate the entire character and its IK targets.
- CTRL_hand.R / CTRL_hand.L: wrist position and grip orientation.
- CTRL_elbow.R / CTRL_elbow.L: elbow bend direction.
- CTRL_foot.R / CTRL_foot.L: foot position and orientation.
- CTRL_knee.R / CTRL_knee.L: knee bend direction.

Enable the Fingers collection to edit the three joints of each finger. Enable Deformation for the spine, neck, head, shoulders, and other body bones. The Face collection exposes the source mesh's face, eye, jaw, and tongue bones. There is also a small animated Exhale • lip purse shape key.

Existing right-hand and elbow animation keys will override manual edits when changing frames. Insert new keys, enable Auto Key, or unlink the Smoking action to create a different performance.

## Mesh and materials

The human is a connected anatomical mesh with smooth, normalized skin weights and subdivision. Arm and leg twist halves are merged into full limb segments for the two-bone IK chains. The fitted clothing uses weights interpolated from its anatomical binding. Armature modifiers preserve volume.

The complete body mesh is retained. A non-destructive Clothing coverage mask hides skin under the outfit. Disable that modifier if removing or replacing the clothing.

All used image textures are packed into the blend. The cigarette has separate paper, filter, ember, and ash materials and follows the wrist's skin transform. Its filter is placed at the lip contact point during the held draw.

The smoke uses animated procedural volume fields with spatial falloff and turbulence. It is an art-directed effect, not a baked fluid simulation. No external smoke cache is required. This is an editable character scene, not a claimed photorealistic film-production asset or a ready-made game export.

## Source package

Run build.py with Blender's Python, keeping performance.py, smoke.py, finalize.py, README.md and the assets directory beside it. Example:

    blender -b --python build.py

The script saves the scene and renders two stills. Set ROOK_RENDER_ANIMATION=1 to render the preview sequence into frames/. Preview frames are sampled at 12 fps; the supplied MP4 is interpolated to 24 fps. The native Blender action remains continuous at 24 fps.

## Asset credits

Human topology, morph targets, skeleton definitions, skin weights, eyes, hair, eyebrows, skin texture, fitted clothing, and shoes originate from the MakeHuman community's CC0 assets. Scene assembly, rig adaptation and controls, hand posing, smoking animation, cigarette, stubble, scar, smoke fields, and lighting were added for this project.

Sources:
- https://github.com/makehumancommunity/makehuman
- https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md
- https://github.com/s20220526/makehuman-assets (mirror of the MakeHuman bundled assets)
- https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html

The upstream asset headers credit Data Collection AB, Joel Palmius, Jonas Hauquier and the MakeHuman contributors. The bundled graphical assets were released under CC0 in September 2020. Their original headers are retained in the source package.
