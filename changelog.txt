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