"""Camera focus link for Nuke 15. Run show_panel() from Nuke's Script Editor."""
__author__ = "Vikas Patwa"

import math
import nuke

# The focus plane is expressed in the same encoding as the depth channel.
MODES = {
    'Distance': ('depth', '{distance}'),
    'Negative_distance': ('-depth', '-({distance})'),
    'Inverse_distance': ('far = 0', '1/({distance})'),
    'Negative_inverse_distance': ('far = -0', '-1/({distance})'),
}
SCALE = 'czf_unit_scale'
OFFSET = 'czf_focus_offset'


def _camera(node):
    return (node.Class().startswith('Camera') and
            node.knob('focal_point') is not None)


def link(camera, target=None, image=None, channel='depth.Z',
         mode='Distance', scale=1.0, offset=0.0):
    """Link an existing ZDefocus, or create one in the current group.

    scale converts camera scene units to depth-pass distance units; offset is
    added in depth-pass distance units BEFORE inverse/sign encoding.
    Call from Nuke's main thread. All edits belong to one Undo operation.
    """
    if not _camera(camera):
        raise ValueError('Choose a Camera with a focal_point (focus distance) knob.')
    if target is not None and target.Class() not in ('ZDefocus', 'ZDefocus2'):
        raise ValueError('The target must be a ZDefocus node.')
    if mode not in MODES:
        raise ValueError('Unsupported depth encoding.')
    scale, offset = float(scale), float(offset)
    if not math.isfinite(scale) or scale <= 0 or not math.isfinite(offset):
        raise ValueError('Unit scale must be positive; scale and offset must be finite.')
    if not channel or any(c.isspace() for c in channel):
        raise ValueError('Enter a channel name, for example depth.Z.')
    source = target.input(0) if target is not None else image
    if source is not None and channel not in source.channels():
        raise ValueError('The image input does not contain channel: ' + channel)
    if camera['focal_point'].value() * scale + offset <= 0:
        raise ValueError('Scaled focus distance must be positive. Check scale and offset.')
    if target is not None:
        for name in (SCALE, OFFSET):
            if target.knob(name) is not None and target[name].Class() != 'Double_Knob':
                raise ValueError('A conflicting custom knob already exists: ' + name)

    camera_path = 'root.' + camera.fullName() + '.focal_point'
    distance = 'max(1e-9,({}*{}+{}))'.format(camera_path, SCALE, OFFSET)
    expression = MODES[mode][1].format(distance=distance)
    created = target is None
    old = {}
    added = []
    undo = nuke.Undo()
    undo.begin('Link ZDefocus to Camera')
    try:
        if created:
            target = nuke.nodes.ZDefocus2()
            if image is not None:
                target.setInput(0, image)
                target.setXYpos(image.xpos(), image.ypos() + 100)
        for name in ('center', 'math', 'z_channel', SCALE, OFFSET):
            if target.knob(name) is not None:
                old[name] = target[name].toScript()
        if 'czf_tab' not in target.knobs():
            target.addKnob(nuke.Tab_Knob('czf_tab', 'Camera Focus'))
            added.append('czf_tab')
        for name, label, value in ((SCALE, 'Camera to depth unit scale', scale),
                                   (OFFSET, 'Focus offset (depth units)', offset)):
            if target.knob(name) is None:
                knob = nuke.Double_Knob(name, label)
                target.addKnob(knob)
                added.append(name)
            target[name].clearAnimated()
            target[name].setValue(value)
        target[SCALE].setTooltip('Multiply camera focus distance by this to match the depth pass units.')
        target[OFFSET].setTooltip('Added after unit conversion, before depth encoding. Distance is clamped above zero.')
        # Select by label rather than depending on menu indices.
        values = target['math'].values()
        wanted = MODES[mode][0].replace(' ', '')
        matched = next((v for v in values if v.replace(' ', '') == wanted), None)
        if matched is None:
            raise ValueError('This ZDefocus does not offer the required depth math mode.')
        target['math'].setValue(matched)
        target['z_channel'].setValue(channel)
        target['center'].clearAnimated()
        target['center'].setExpression(expression)
        target['center'].value()  # Resolve the reference now, before accepting the edit.
        return target
    except Exception:
        if created and target is not None:
            nuke.delete(target)
        elif target is not None:
            for name in reversed(added):
                target.removeKnob(target[name])
            for name, script in old.items():
                target[name].fromScript(script)
        raise
    finally:
        undo.end()


def show_panel():
    """Use one selected ZDefocus, or create one below one selected image node."""
    cameras = sorted((node for node in nuke.allNodes(group=nuke.root(), recurseGroups=True)
                      if _camera(node)), key=lambda node: node.fullName())
    if not cameras:
        nuke.message('Add a Camera with a focus distance control, then run this tool again.')
        return
    selected = nuke.selectedNodes()
    targets = [node for node in selected if node.Class() in ('ZDefocus', 'ZDefocus2')]
    if len(targets) > 1:
        nuke.message('Select only one ZDefocus to link.')
        return
    target = targets[0] if targets else None
    images = [node for node in selected
              if not _camera(node) and node.Class() != 'Viewer']
    if target is None and len(images) > 1:
        nuke.message('Select one image node, or one existing ZDefocus.')
        return
    image = images[0] if target is None and images else None
    chosen = [node for node in selected if node in cameras]
    if chosen:
        cameras.remove(chosen[0])
        cameras.insert(0, chosen[0])
    panel = nuke.Panel('Camera to ZDefocus | Nuke 15')
    panel.setWidth(510)
    panel.addEnumerationPulldown('Camera', ' '.join(node.fullName() for node in cameras))
    panel.addSingleLineInput('Depth channel', target['z_channel'].value() if target else 'depth.Z')
    modes = list(MODES)
    if target:
        current = target['math'].value().replace(' ', '')
        matching = [key for key in modes if MODES[key][0].replace(' ', '') == current]
        if matching:
            modes.remove(matching[0])
            modes.insert(0, matching[0])
    panel.addEnumerationPulldown('Depth encoding', ' '.join(modes))
    panel.addSingleLineInput('Camera to depth unit scale', str(target[SCALE].value())
                             if target and target.knob(SCALE) else '1.0')
    panel.addSingleLineInput('Focus offset (depth units)', str(target[OFFSET].value())
                             if target and target.knob(OFFSET) else '0.0')
    panel.addNotepad('Action', 'Link selected ZDefocus' if target else 'Create a linked ZDefocus')
    panel.addButton('Cancel')
    panel.addButton('Link')
    if not panel.show():
        return
    try:
        camera = next(node for node in cameras if node.fullName() == panel.value('Camera'))
        result = link(camera, target, image,
                      panel.value('Depth channel').strip(), panel.value('Depth encoding'),
                      float(panel.value('Camera to depth unit scale')),
                      float(panel.value('Focus offset (depth units)')))
        nuke.show(result)
    except Exception as exc:
        nuke.message('Camera Focus Link: ' + str(exc))


if __name__ == '__main__':
    show_panel()
