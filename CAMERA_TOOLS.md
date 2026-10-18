# Camera Focus Tools for Nuke

**Created by Vikas Patwa.**

Link a Nuke camera's animated focus distance to **Bokeh** or **ZDefocus** using expressions. The links remain live as the camera animation changes.

## Included tools

| Tool | File | Main function |
| --- | --- | --- |
| Camera to Bokeh | `camera_bokeh.py` | Links focus distance, with optional focal length, f-stop and filmback links. |
| Camera to ZDefocus | `camera_zdefocus.py` | Links focus distance with distance, negative-distance, inverse-distance or negative-inverse-distance encoding. |

Both tools can create a node or update one selected compatible node. They add a **Camera Focus** tab with unit-scale and focus-offset controls. Each operation is grouped into one Undo step.

## Installation

### Install the full tool collection

1. Download this repository using **Code → Download ZIP**, then extract it.
2. Create a folder called `VikasTools` inside your Nuke user folder (`~/.nuke` on macOS/Linux or `%USERPROFILE%\.nuke` on Windows).
3. Copy the repository's `.py`, `.nk`, and `.gizmo` files into `VikasTools`.
4. Add these lines to your existing `.nuke/init.py`, preserving its current contents:

   ```python
   import nuke
   nuke.pluginAddPath('./VikasTools')
   ```

5. Restart Nuke. Use **Camera Tools → Link Camera to Bokeh** or **Camera Tools → Link Camera to ZDefocus** from the main menu.

If you installed ColourMix using the `ColourMix` folder described in the main README, copy the two camera scripts and updated `menu.py` into that existing folder instead. Keep its existing `pluginAddPath` entry; you do not need a second installation.

### Install only the camera tools

Copy `camera_bokeh.py` and `camera_zdefocus.py` into `.nuke`, then append the following to your existing `.nuke/menu.py`. Keep any previous contents.

```python
import nuke
import camera_bokeh
import camera_zdefocus

nuke.menu('Nuke').addCommand(
    'Camera Tools/Link Camera to Bokeh', camera_bokeh.show_panel
)
nuke.menu('Nuke').addCommand(
    'Camera Tools/Link Camera to ZDefocus', camera_zdefocus.show_panel
)
```

Restart Nuke.

## Usage

1. Add or import a camera with a **focus distance** (`focal_point`) control.
2. Select one image node containing a depth channel to create a new linked defocus node, or select one existing compatible Bokeh / ZDefocus node to update it.
3. Open the appropriate **Camera Tools** menu command.
4. Choose the camera, depth channel, depth encoding, unit scale and focus offset.
5. Click **Link**.

The default channel is `depth.Z`. If an image is connected, the tool checks that the specified channel exists. The camera may be inside a Group.

## Unit scale and focus offset

The distance used by the tool is:

`camera focus distance × unit scale + focus offset`

Use the scale to match camera scene units to your depth pass. The scale must be positive, and the resulting focus distance must be positive at the current frame. During animation, the expression clamps the distance above zero.

### Bokeh

- Supports distance and inverse-distance depth passes.
- `focalPlane` remains a distance even when the depth style is `1/z`.
- Optional lens links connect focal length, f-stop, horizontal filmback and vertical filmback. This also enables real-world lens mode and selects a custom film format.
- An existing native Camera input on Bokeh is disconnected so the expression links and unit controls can apply. Undo restores the operation.
- The tool creates Nuke's `Bokeh` node by default. It can also update a compatible selected `pgBokeh` node; it does not include or install that third-party plug-in.
- Check the scene-unit setting in Bokeh's Lens controls against your image's depth units.

### ZDefocus

- Uses the camera's focus distance to drive the focus plane.
- Supports distance, negative distance, inverse distance and negative inverse distance.
- Unit conversion and offset are applied before inverse/sign encoding.
- The tool creates Nuke's native `ZDefocus2`. A legacy or third-party node with different controls may be unsupported.

## Validation

Checked in **Nuke 15.2v9** using a temporary animated Camera3:

- ZDefocus: animated focus, scale, offset and all four depth encodings.
- Bokeh: animated focus, scale, offset, inverse-depth selection and all four optional lens links.

These checks verify control values and expressions, not the visual quality of rendered defocus. Other Nuke versions and third-party pgBokeh versions have not been verified.

## Troubleshooting

- **No camera listed:** add a camera with a `focal_point` control.
- **Missing depth channel:** check the selected image node and the exact channel name.
- **Focus distance differs from the depth pass:** adjust the unit scale and offset; confirm the encoding and scene units.
- **Unsupported node/version:** use the native Bokeh or ZDefocus node provided with your Nuke version.

## License

No license file is included.
