"""Register ColourMix in Nuke's Color menu and Tab search."""
import os
import nuke


def create_colourmix(path=os.path.join(os.path.dirname(__file__), 'ColourMix.nk')):
    """Create a portable Group containing the complete ColourMix graph."""
    return nuke.nodePaste(path)


nuke.menu('Nodes').addCommand('Color/ColourMix', create_colourmix)
