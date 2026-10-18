"""Register ColourMix in Nuke's Color menu and Tab search."""
import os
import nuke


def create_colourmix(path=os.path.join(os.path.dirname(__file__), 'ColourMix.nk')):
    """Create a portable Group containing the complete ColourMix graph."""
    return nuke.nodePaste(path)


nuke.menu('Nodes').addCommand('Color/ColourMix', create_colourmix)


def launch_camera_bokeh():
    import camera_bokeh
    camera_bokeh.show_panel()


def launch_camera_zdefocus():
    import camera_zdefocus
    camera_zdefocus.show_panel()


nuke.menu('Nuke').addCommand('Camera Tools/Link Camera to Bokeh', launch_camera_bokeh)
nuke.menu('Nuke').addCommand('Camera Tools/Link Camera to ZDefocus', launch_camera_zdefocus)
