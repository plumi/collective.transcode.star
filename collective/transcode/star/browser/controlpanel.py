from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from collective.transcode.star.interfaces import ITranscodeSettings
from plone.z3cform import layout

class TranscodeControlPanelForm(RegistryEditForm):
    schema = ITranscodeSettings

TranscodeControlPanelView = layout.wrap_form(TranscodeControlPanelForm, ControlPanelFormWrapper)

