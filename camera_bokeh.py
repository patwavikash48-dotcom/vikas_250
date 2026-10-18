"""Camera focus/lens links for Nuke 15 Bokeh and compatible pgBokeh nodes."""
__author__ = "Vikas Patwa"

import math
import nuke

SCALE = 'cpb_unit_scale'
OFFSET = 'cpb_focus_offset'
CLASSES = ('Bokeh', 'pgBokeh')
STYLES = {'Distance': 'Real', 'Inverse_distance': '1/z'}


def is_camera(node):
    return node.Class().startswith('Camera') and node.knob('focal_point') is not None


def _enum(knob, label):
    value = next((v for v in knob.values() if v.lower() == label.lower()), None)
    if value is None:
        raise ValueError('Unsupported {} option: {}'.format(knob.name(), label))
    knob.setValue(value)


def link(camera, target=None, image=None, channel='depth.Z', style='Distance',
         scale=1.0, offset=0.0, lens=False):
    """Create/link Bokeh with native expressions; one Undo restores all edits.

    focalPlane is always a distance, including when depthStyle is 1/z.
    Scene units are selected separately in Bokeh's Lens tab.
    """
    if not is_camera(camera):
        raise ValueError('Choose a Camera with a focal_point focus-distance knob.')
    if target is not None and target.Class() not in CLASSES:
        raise ValueError('Select one Bokeh or pgBokeh node.')
    if style not in STYLES:
        raise ValueError('Choose Distance or Inverse_distance.')
    scale, offset = float(scale), float(offset)
    if not math.isfinite(scale) or scale <= 0 or not math.isfinite(offset):
        raise ValueError('Unit scale must be positive; both values must be finite.')
    if camera['focal_point'].value() * scale + offset <= 0:
        raise ValueError('Scaled camera focus distance must be positive.')
    if not channel or any(c.isspace() for c in channel):
        raise ValueError('Enter a depth channel such as depth.Z.')
    source = target.input(0) if target is not None else image
    if source is not None and channel not in source.channels():
        raise ValueError('Image input does not contain ' + channel + '.')
    lens_links = {'focalLength': 'focal', 'fStop': 'fstop',
                  'apertureWidth': 'haperture', 'apertureHeight': 'vaperture'}
    if lens:
        missing = [name for name in lens_links.values() if camera.knob(name) is None]
        if missing:
            raise ValueError('Camera is missing lens controls: ' + ', '.join(missing))
    if target is not None:
        for name in (SCALE, OFFSET):
            if target.knob(name) is not None and target[name].Class() != 'Double_Knob':
                raise ValueError('Conflicting custom knob: ' + name)

    created = target is None
    saved, added = {}, []
    old_camera_input = None
    input_changed = False
    undo = nuke.Undo()
    undo.begin('Link Camera to Bokeh')
    try:
        if created:
            target = nuke.nodes.Bokeh()
            if image is not None:
                target.setInput(0, image)
                target.setXYpos(image.xpos(), image.ypos() + 100)
        required = ['focalPlane', 'depthChannel', 'depthStyle']
        if lens:
            required += list(lens_links) + ['realWorldLens', 'filmFormat']
        missing = [name for name in required if target.knob(name) is None]
        if missing:
            raise ValueError('Unsupported Bokeh version; missing: ' + ', '.join(missing))
        for name in required + [SCALE, OFFSET]:
            if target.knob(name) is not None:
                saved[name] = target[name].toScript()
        # Bokeh input 2 is Camera (input 0 is image, input 1 is kernel).
        # Disconnect the native override so the expressions and unit controls apply.
        old_camera_input = target.input(2)
        target.setInput(2, None)
        input_changed = True
        if target.knob('cpb_tab') is None:
            target.addKnob(nuke.Tab_Knob('cpb_tab', 'Camera Focus'))
            added.append('cpb_tab')
        for name, label, value in ((SCALE, 'Camera to depth unit scale', scale),
                                  (OFFSET, 'Focus offset (depth units)', offset)):
            if target.knob(name) is None:
                target.addKnob(nuke.Double_Knob(name, label))
                added.append(name)
            target[name].clearAnimated()
            target[name].setValue(value)
        target[SCALE].setTooltip('Convert camera scene units to depth-pass distance units.')
        target[OFFSET].setTooltip('Add after unit conversion. Final distance is clamped above zero.')
        _enum(target['depthStyle'], STYLES[style])
        target['depthChannel'].setValue(channel)
        path = 'root.' + camera.fullName()
        target['focalPlane'].clearAnimated()
        target['focalPlane'].setExpression('max(1e-9,{}.focal_point*{}+{})'.format(path, SCALE, OFFSET))
        if lens:
            target['realWorldLens'].setValue(True)
            _enum(target['filmFormat'], 'Custom')
            for destination, source_name in lens_links.items():
                target[destination].clearAnimated()
                target[destination].setExpression(path + '.' + source_name)
        for name in ['focalPlane'] + (list(lens_links) if lens else []):
            target[name].value()
        return target
    except Exception:
        if created and target is not None:
            nuke.delete(target)
        elif target is not None:
            for name in reversed(added):
                target.removeKnob(target[name])
            for name, script in saved.items():
                target[name].fromScript(script)
            # Only restore if input handling was reached.
            if input_changed:
                target.setInput(2, old_camera_input)
        raise
    finally:
        undo.end()


def show_panel():
    cameras = sorted((n for n in nuke.allNodes(group=nuke.root(), recurseGroups=True)
                      if is_camera(n)), key=lambda n: n.fullName())
    if not cameras:
        nuke.message('Add a Camera with a focus-distance control, then run the tool again.')
        return
    selected = nuke.selectedNodes()
    targets = [n for n in selected if n.Class() in CLASSES]
    if len(targets) > 1:
        nuke.message('Select only one Bokeh / pgBokeh node.')
        return
    target = targets[0] if targets else None
    images = [n for n in selected if not is_camera(n) and n.Class() != 'Viewer']
    if target is None and len(images) > 1:
        nuke.message('Select one image node, or one existing Bokeh / pgBokeh.')
        return
    image = images[0] if target is None and images else None
    chosen = [n for n in selected if n in cameras]
    if chosen:
        cameras.remove(chosen[0])
        cameras.insert(0, chosen[0])
    styles = list(STYLES)
    if target and target['depthStyle'].value() == '1/z':
        styles.reverse()
    panel = nuke.Panel('Camera to Bokeh | Nuke 15')
    panel.setWidth(540)
    panel.addEnumerationPulldown('Camera', ' '.join(n.fullName() for n in cameras))
    panel.addSingleLineInput('Depth channel', target['depthChannel'].value() if target else 'depth.Z')
    panel.addEnumerationPulldown('Depth encoding', ' '.join(styles))
    panel.addSingleLineInput('Camera to depth unit scale', str(target[SCALE].value())
                             if target and target.knob(SCALE) else '1.0')
    panel.addSingleLineInput('Focus offset (depth units)', str(target[OFFSET].value())
                             if target and target.knob(OFFSET) else '0.0')
    panel.addBooleanCheckBox('Also link focal length, f-stop and filmback', False)
    panel.addNotepad('Action', ('Link selected Bokeh / pgBokeh' if target else 'Create linked Bokeh') +
                     '. Uses expressions; any existing Camera input is disconnected. One Undo restores changes.')
    panel.addButton('Cancel')
    panel.addButton('Link')
    if not panel.show():
        return
    try:
        camera = next(n for n in cameras if n.fullName() == panel.value('Camera'))
        result = link(camera, target, image, panel.value('Depth channel').strip(),
                      panel.value('Depth encoding'),
                      float(panel.value('Camera to depth unit scale')),
                      float(panel.value('Focus offset (depth units)')),
                      bool(panel.value('Also link focal length, f-stop and filmback')))
        nuke.show(result)
    except Exception as exc:
        nuke.message('Camera Bokeh Link: ' + str(exc))


if __name__ == '__main__':
    show_panel()
