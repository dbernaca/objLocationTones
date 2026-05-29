### Changelog for Version 26.1.0 in relation to 25.1.0

#### **Major Updates**
- **Atomic Settings Storage**:
  - Implemented `serialization.SafeFile()` using atomic techniques from Windows API to prevent `settings.json` corruption during power loss or filesystem mishaps.
  - Settings are now saved with enhanced reliability and data integrity.

- **MIDI Engine Improvements**:
  - Fixed MIDI compatibility with Python 3.13, ensuring support for NVDA 2026.x.
  - MIDI player now handles all events in its own thread without relying on `MainLoop()` for scheduling.
  - Resolves issues with overly long or non-stopping notes while improving overall efficiency.
  - Instrument selection field is now automatically disabled in settings panel when MIDI is turned off.

#### **New Features**
- **Automatic Object Outline Playback**:
  - New feature to automatically play an object's outline when it is brought to the foreground.
  - Provides immediate spatial awareness without manual gesture invocation (enable in settings panel).
- **Pointer's position at start of navigation reference point**:
  - Added new selectable reference point for mouse monitoring that plays location from which mouse pointer started moving as the static reference
- **Dynamic Settings Panel Controls**:
  - Extended settings package to support enabling and disabling of drawn controls programmatically.
  - Added capability to control GUI elements via `enabled` argument and on-the-fly via `.enable` property.
  - Settings attributes now also support dynamic manipulation of `.show`, `.save`, and `.skip` attributes for better panel control.

#### **Fixes and Optimizations**
- **Performance Optimizations and minor bug fixes**:
  - Microoptimizations to `geometry.BBox()` by removing double memory access and extra additions.
  - Various micro-optimizations and corrected errors in code comments.
  - Fixed formatting for logging in settings package when SettingsErrors are raised
- **Enhanced Install and Update Process**:
  - Updated `installTasks.py` to support expanding to new options and handle settings migration more robustly.
- **Dependency Updates**:
  - New `pypm` packaging implemented: portmidi.dll libraries and pypm *.pyd files for both 64 and 32 bit x86 NVDA added

#### **Important Notes**
- **Python 3.13 Support**: This version is fully compatible with NVDA 2026.x and Python 3.13.
- **MIDI Thread Management**: Note scheduling is now completely managed by the Player thread, ensuring accurate note durations in all scenarios.
- **Atomic save of settings files**: Settings files are first saved to a temporary file, then moved by the OS in one swoop to targeted path.

This changelog was generated using Perplexity AI.

### Changelog for Version 25.1.0 in relation to 24.07.0

#### **Major Updates**
- **MIDI Tone Generation**:
  - Added support for producing positional tones via **Musical Instrument Digital Interface (MIDI)**.
  - Works with Windows’ built‑in synthesizer (Microsoft GS Wavetable Synth) or any other installed software or hardware synthesizer and any General MIDI Level 1 instrument.
  - Implemented using a modified `pygame.midi` with bundled `portmidi` and `pyportmidi`
  - Configurable via the settings panel; includes instrument selection.
  - **pypm added for Python 3.7 as well**, enabling MIDI functionality on NVDA 2023.x too.

- **Settings panel changes**:
  - **Mouse Monitoring Reference Points in mouse group**: Now selectable (focused object/system caret, screen/window center, or none).
  - **Cancellation Support**: Pressing **Cancel** discards all changes made while the panel was open.
  - Temporary removal of the **Restore Defaults** option due to conflicts with cancellation.

#### **New Features**
- **MIDI Tone Generation**:
  - Added support for producing positional tones via **Musical Instrument Digital Interface (MIDI)**.
  - Now you can hear positional tones produced by musical instruments if you prefer them over classical NVDA beeps
- **Enhanced Continuous Mouse Monitoring**:
  - Expanded with customizable reference points and improved auto‑start behavior.

#### **Fixes**
- Fixed a NameError in `installTasks.py` and improved module import handling (`sys.path.insert` used instead of `append`).
- Corrected issues with caret checkbox state in settings.
- Fixed bugs related to auto‑start mouse monitoring when the mouse enters a new object.

#### **Important Notes**
- **MIDI Tips**: Use mono instruments without note onset delays to ensure accurate positional feedback.  
- **Restore Defaults** temporarily unavailable; use Cancel to discard changes.  
- Known issues with caret reporting in some non‑native input fields remain; progress bar tones may overlap with positional tones if MIDI is disabled.

This changelog was generated using ChatGPT.

### Changelog for Version 24.07.0 in relation to 24.06.3

#### **Major Updates**
- **Settings Panel Redesign**:
  - Introduced a comprehensive settings panel with grouped controls, allowing for granular control of positional tone reporting. Customize settings such as:
    - **Caret Reporting**: Turn caret reporting on or off
    - **Caret Reporting Modes**: Choose from vertical, horizontal, both, or none.
    - **Independent Tone Durations**: Adjust tone durations for navigation and caret reporting separately.
    - **Typing Feedback**: Enable or disable caret location reporting while typing.
    - **Mouse Monitoring**: Auto-start continuous mouse reporting on first movement.

- **New Gestures**:
  - **Toggle Caret Reporting**: `Ctrl+Windows+NumpadDelete`.
  - **Cycle Through Caret Reporting Modes**: `Ctrl+Alt+Windows+NumpadDelete`.

#### **New Features**
- **Auto-Start Mouse Monitoring**: Begins on first mouse movement if enabled in the settings panel.
- **Enhanced Object Outline Reporting**
- **Improved Live Feedback**:
  - Settings adjustments now take effect immediately, allowing users to test changes in real time without closing the settings panel or clicking Apply each time.
  - Gestures are now synchronized with the settings panel when used, there will be no mishaps if a gesture is used while settings panel is opened.
  - Enhanced sliders and controls in settings panel for more intuitive adjustments using arrow keys.

#### **Fixes and Optimizations**
- Optimized gesture detection for better typing and caret movement tracking.
- Fixed bugs in reapplying settings 
- Addressed some issues when recognizing certain text input fields.

#### **Compatibility and Documentation**
- Added robust handling of settings from older versions during upgrades.
- Improved inline documentation for easier maintenance and better developer understanding.

#### **Important Notes**
- **Backward Compatibility**:
  - `Ctrl+NumpadDelete` toggles both navigation and caret reporting for ease of use.
  - Caret reporting must be explicitly re-enabled using the settings panel or `Ctrl+Windows+NumpadDelete` if toggled off separately.
- **Known Issues**:
  - Minor inaccuracies in caret location reporting for non-native input fields, especially at the end of documents or in empty documents.
  - Potential overlap with add-ons like Braille Extender when both produce tones or modify keypress behavior.
  - Differentiation between progress bar beeps and positional tones may require adjusting tone durations in the settings panel.

This changelog was generated using ChatGPT.