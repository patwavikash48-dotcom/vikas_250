# ColourMix for Nuke

**Created by Vikas Patwa.**

One colour-adjustment node with exposure in stops, Grade, Saturation, ColorLookup colour matching, and an optional mask. All controls are on one **Colour** tab, with the creator credit at the bottom.

**Processing order:** Exposure → Grade → Saturation → ColorLookup → masked blend.

## Features

- **Exposure in stops:** +1 doubles RGB; −1 halves RGB.
- **Grade:** blackpoint, whitepoint, lift, gain, multiply, offset, gamma, clamp options and mix.
- **Saturation:** saturation amount, luminance math and mix.
- **ColorLookup:** Source, Target and Set RGB colour matching, with the curve editor hidden.
- **Mask:** separate input, Use Mask, channel selection and inversion.
- **Overall Mix:** blend between the original and adjusted image.
- **Appearance:** dark Group node with a “+” badge; internal nodes are included in the comp.
- Uses Nuke's built-in nodes; no third-party plug-ins are required.

## Quick use without installation

1. Download this repository using **Code → Download ZIP**, then extract it.
2. In Nuke, choose **File → Insert Comp Nodes…** and select `ColourMix.nk`.
3. Connect an image to **Source** and view the result.

You can also copy the entire text of `ColourMix.nk` and paste it into the Node Graph.

## Install in the Color menu and Tab search

1. Create a folder named **ColourMix** inside your Nuke user folder, and copy `ColourMix.nk`, `ColourMix.gizmo`, and `menu.py` into it:

   | System | Nuke user folder |
   | --- | --- |
   | Windows | `%USERPROFILE%\.nuke` |
   | macOS / Linux | `~/.nuke` |

2. Add the following to your existing `.nuke/init.py`. Create that file if needed, and keep any existing contents.

   ```python
   import nuke
   nuke.pluginAddPath('./ColourMix')
   ```

3. Restart Nuke.
4. Press **Tab**, search for **ColourMix**, and create it, or use **Color → ColourMix**.

The menu creates the portable `.nk` Group. The `.gizmo` file is also provided for users who prefer a gizmo-based pipeline; use `nuke.createNode('ColourMix')` after loading the plug-in folder.

## Using the controls

### Exposure and Grade

Use scene-linear images for photographic exposure adjustments. The initial settings leave the image unchanged. RGB is processed and the original alpha passes through. Grade's black and white clamps are initially off.

For premultiplied elements, use **Unpremult → ColourMix → Premult**.

### Source and Target colour matching

1. Set or pick the colour to change in **Source**.
2. Set or pick the desired colour in **Target**.
3. Click **Set RGB** to add that mapping to the internal ColorLookup curves.

Each click adds or updates curve points; it does not automatically reset previous matches. Source and Target affect the image after **Set RGB** is pressed. **Curve Mix** adjusts the matching strength. The curve editor is intentionally hidden from the Colour tab; advanced edits remain available inside the Group on the `Curves` node.

### Mask

1. Connect a Roto or mask image to the **Mask** input.
2. Enable **Use Mask**.
3. Choose the channel, normally `rgba.alpha`.

White applies the colour adjustment; black preserves the source; gray produces a partial adjustment. **Invert Mask** reverses this. **Overall Mix** continues to control the effect's strength. Leave Use Mask off when no mask is connected.

## Compatibility and validation

Validated in **Nuke 15.2v9**. Other versions have not been verified.

Pixel checks covered exposure, mask off/on, black/white/soft masks, mask inversion, overall Mix, and alpha preservation.

## Version

**1.0.0** — Initial public package.

## License

No license file is included.

## Feedback

Please open a GitHub issue with your Nuke version, operating system, and steps to reproduce a problem. Use a minimal sample without private footage.
