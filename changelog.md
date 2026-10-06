### Changelog for Version 26.2.0 in relation to 26.1.0

#### **Major Updates**
- **Location Presentation Modes**:
  - Added a configurable location presentation mode that determines both which object represents the current navigation position and which point within that object is presented by the positional tone.
  - Navigation can now follow either the navigator object or the focused object.
  - Each object can be represented by its centroid, the middle of its left border, or the middle of its right border.
  - The selected mode is applied immediately when changed in the settings panel and restored correctly if the settings dialog is cancelled.
  - Automatic navigation reporting and on-demand object location and outline commands now follow the selected object type.

- **Enhanced Mouse Monitoring and Keyboard Interaction**:
  - Added the navigator object's location as a selectable mouse monitoring reference point.
  - Keyboard navigation and caret movement can now be used while the pointer remains stationary to compare navigated objects or the caret with the pointer's position.
  - Navigation and caret events refresh the inactivity timeout while a dynamic focused-object or navigator-object reference point is being used.
  - Separate navigation tones are suppressed during this interaction so that mouse monitoring remains the single source of positional output.
  - NVDA mouse tracking is now enabled automatically when required by mouse monitoring and protected from being disabled while monitoring is active.
  - If the user changes NVDA's mouse-tracking setting during monitoring, the choice is remembered and applied after monitoring ends.

- **Build System Migration**:
  - Migrated the project from the legacy NVDA add-on template and SCons-based build system to `nvda-addon-kit`.
  - Replaced `buildVars.py`, manifest templates, `sconstruct`, and bundled SCons support files with the declarative `addon.toml` configuration.
  - Added build configuration for add-on metadata, compatibility information, translation sources, excluded files, and documentation rendering.
  - Configured builds to exclude the runtime `settings.json` file from generated `.nvda-addon` packages.
  - Added documentation describing how to build, install, migrate, and translate the add-on with `nvda-addon-kit`.
  - Added the required `pymdown-extensions` configuration for fenced and inline code in generated documentation.

- **Internal Architecture Refactoring**:
  - Split event handlers, input scripts, and feature-switching methods out of `GlobalPlugin` into `_events.py`, `_scripts.py`, and `_switches.py`.
  - Added `constants.py` for caret, mouse-reference, and location-presentation mode constants and their mode-detection helpers.
  - Added `meta.AutoAll()` to generate controlled module export lists and reduce imported namespaces.
  - Deferred several imports until `GlobalPlugin` initialization to reduce the add-on's module-level namespace and unnecessary startup work.
  - Reworked positional tone playback around a persistent `play` instance that stores duplicate-detection state, channel volumes, stereo direction, and the active tone generator.
  - Preserved `playCoordinates()` and `playPoints()` as aliases for backward-compatible internal use.
  - Added support for selecting a specific MIDI output device in the internal tone-generator interface as groundwork for future MIDI options.

#### **New Features**
- **Navigator Object Mouse Reference Point**:
  - Added the navigator object's location to the list of continuous mouse monitoring reference points.

- **Configurable Location Representation**:
  - Added six presentation choices combining navigator or focused objects with centroid, left-border, or right-border coordinates.
  - Left and right border positions use the vertical midpoint of the corresponding object edge.
  - Switching modes dynamically changes the NVDA event used for automatic location reporting. It is either event_becomeNavigator or event_gainFocus respectively.

- **Tabs and Spaces Caret Reporting**:
  - Added an option to report caret location only when tabs or spaces are encountered.
  - During keyboard navigation, the character at the caret is inspected before a positional tone is played.
  - During typing, the character immediately before the caret is inspected so inserted tabs and spaces can be reported. The new position of the caret is reported, not the position of inserted space or tab character.
  - The option works together with the existing caret reporting mode and the option to report caret movement while typing.

- **Optional Mouse Monitoring Stop Message**:
  - Added a setting that controls whether the natural end of mouse monitoring is announced after the configured inactivity timeout.
  - Explicit cancellation and other mouse monitoring messages remain unaffected.

- **MIDI Output Reset Command**:
  - Added an unassigned command to NVDA's Input Gestures dialog for resetting MIDI output.
  - The command reinitializes the MIDI generator, restores the selected instrument, and plays the current location when possible.
  - It provides a faster way to recover from an unresponsive software or hardware synthesizer without disabling and re-enabling MIDI in the settings panel.

- **New Interface Translations**:
  - Added Croatian, Italian, and Spanish translations.
  - Added more detailed extraction comments for translators and configured `nvda-addon-kit` to obtain Python interface strings from `UIStrings.py` only.
  - Changed the NVDA Settings and Input Gestures category name to **Positional tones**, while retaining **Object Location Tones** as the add-on title only.
  - Positioned the Positional tones settings category immediately above NVDA's Advanced category.

#### **Settings Framework Improvements**
- **Dynamic Attribute Flags**:
  - Added `CallableFlag` support for settings attributes whose `.show`, `.save`, `.skip`, or `.enable` state depends on a callable. (WIP)
  - Added locking and remembered-state capabilities to flags so a value can be enforced temporarily while preserving changes made during the lock.
  - These capabilities are used to protect NVDA mouse tracking during continuous mouse monitoring.

- **Settings Refresh Fixes**:
  - Fixed `refresh_panel()` and `refresh_instance()` processing only the first matching attribute when multiple specific attributes were supplied.
  - Added common attribute-selection helpers to support lookup by name, nickname, control identifier, or attribute object.
  - Improved restoration of default and original values.
  - Added convenient methods for attaching and removing settings panel directly through a `Settings()` instance.
  - Added support for assigning a custom settings-panel title and inserting the panel at a specific position in NVDA's category list.

#### **Fixes and Optimizations**
- **Mouse Monitoring Reliability**:
  - Fixed conflicts between continuous mouse monitoring and NVDA mouse tracking being disabled through either the Mouse settings panel or an input gesture.
  - Fixed duplicate or overlapping tones when keyboard navigation changes a focused-object, navigator-object, or caret reference point during mouse monitoring.
  - Monitoring no longer ends from pointer inactivity while the user is actively moving through objects or text with the keyboard.

- **Display Size Caching**:
  - Replaced repeated desktop-object location lookups with a cached primary-display layout.
  - The cached display dimensions are refreshed through NVDA's display-change extension point.
  - Positional tone coordinate calculations and screen-centre reference calculations now use the cached dimensions.
  - This reduces repeated API calls and provides a foundation for improved multi-display support in the future.

- **Easy Table Navigator Compatibility**:
  - Fixed the Easy Table Navigator option appearing for versions that do not provide the required external API.
  - Added version filtering to optional add-on dependency detection.
  - Corrected the dependency interface's version-check callback signature.
  - The integration setting is now shown only when a usable Easy Table Navigator installation is available.

- **Geometry Utilities**:
  - Fixed bounding-box calculations and reduced repeated location indexing and temporary tuple construction.
  - Simplified point containment checks and separated rectangle-overlap detection into an explicit `overlaps()` method.
  - Added lightweight `Point` and `StampedPoint` classes with rectangular and elliptical proximity metrics as groundwork for future pointer-location features.
  - Added cached location data and clearer representations to `BBox`.

- **Positional Tone Playback**:
  - Centralized playback state and audio settings in the `play` instance.
  - Reduced repeated argument passing for channel volumes and stereo orientation.
  - Added additional microoptimizations to frequently used geometry and namespace operations.

- **Configuration Migration**:
  - Updated `installTasks.py` to add defaults for location presentation mode, tabs-and-spaces caret reporting, and the mouse monitoring stop message when upgrading.
  - Added migration of saved mouse reference point indices to account for insertion of the navigator-object option.

- **Documentation and Translation Infrastructure**:
  - Added completed build and translation instructions to the README.
  - Corrected fenced-code rendering in generated HTML documentation.
  - Added support for preserving ordinary line breaks through the `nl2br` Markdown extension.
  - Updated the README stable-release link for version 26.2.0.
  - Improved translation comments so generated POT and PO files contain clearer interface context.

This changelog was generated using Perplexity AI.

### Changelog for Version 26.1.0 in relation to 25.1.0

#### **Major Updates**
- **Atomic Settings Storage**:
  - Finished `serialization.SafeFile()` class that uses atomic techniques from Windows API to prevent `settings.json` corruption during power loss or filesystem mishaps.
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
  - Added new selectable reference point for mouse monitoring that plays location from which mouse pointer started moving as the static reference.
  - This allows mouse monitoring location tones to be reported relative to the mouse starting position rather than only to object or screen-based reference points.
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
- **Safer Config Writes**: Settings saving now uses an atomic replacement strategy to improve resilience against interrupted writes.

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