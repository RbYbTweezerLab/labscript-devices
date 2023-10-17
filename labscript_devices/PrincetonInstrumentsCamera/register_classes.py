from labscript_devices import register_classes

register_classes(
    'PrincetonInstrumentsCamera',
    BLACS_tab='labscript_devices.PrincetonInstrumentsCamera.blacs_tabs.PrincetonInstrumentsCameraTab',
    runviewer_parser=None,
)
