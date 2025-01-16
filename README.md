# Object Location Tones

* **Author**: Joseph Lee
* **Maintainer**: Dalen
* **Download**: [Stable Version][1]
* **NVDA Compatibility**: 2023.1 and later

After installing this add-on and restarting NVDA, you'll hear tones to indicate the location of different objects on the screen as you navigate. To turn off object location reporting, press `Ctrl+NumpadDelete`. To enable it again, use the same gesture. Object Location Tones will remember your preference, and when NVDA starts, it will retain the last state. All settings will persist, even after disabling and re-enabling the add-on.

## Features:

* **Report Focused Object's Location**: During navigation, a positional tone will indicate the currently focused object's location. This feature helps you understand an application's or website's layout, scroll through long menus or file lists faster, and gain a better sense of how your OS behaves visually.
* **Report Caret Location in Text Fields**: When navigating within editable input fields, positional tones will indicate the caret's location. This helps you perceive how the document is scrolled both horizontally and vertically, how long your lines are and when and where they are wrapped, better manage indentations, and more.
* **Toggle Positional Tones**: You can toggle the automatic positional tones on or off using `Ctrl+NumpadDelete` gesture. This feature lets you activate positional tones during navigation only when you need it.
* **Toggle Caret Reporting**: Use `Ctrl+Windows+NumpadDelete` gesture to turn caret location reporting on or off. This allows you to keep positional tones active during navigation while disabling them for text fields (or vice versa).
* **Explicitly Report Object Location**: Press `NumpadDelete` to explicitly report the focused object's location. In editable input fields, it will report the caret's position if caret reporting is turned on. This is useful when tones during navigation are off, or when you want to hear the location of the focused object again without having to navigate away from it first.
* **Explicitly Report Mouse Cursor Location**: Use `Windows+NumpadDelete` gesture to report the mouse cursor's location via a positional tone.
* **Report Object's Outline**: Use `Ctrl+Shift+NumpadDelete` gesture to hear a positional tone indicating the outline of the currently focused graphical object. This gives you a sense of the size and location of UI controls or other elements, which can be helpful in understanding how visual elements are arranged on the screen. This feature is very useful in GUI development.
* **Report Parent's Outline**: Use `Ctrl+Alt+Shift+NumpadDelete` gesture to hear the outline of the currently focused object's parent. Pressing it multiple times moves further up the ancestry chain. This feature helps you understand the relationships between the focused object and its ancestors, which is particularly useful for GUI development.
* **Continuous Mouse Location Reporting**: Use `Shift+NumpadDelete` gesture to turn on continuous reporting of the mouse cursor's location in relation to the focused object (or system caret in text fields if caret reporting is enabled). This feature plays one tone for the mouse and another for the focused object or caret. It remains active until the same gesture is used to turn it off or the mouse stops moving. This is helpful in applications or websites where interaction is only possible with the mouse, and it can also assist with text editing and selection. This feature can be automatically activated upon mouse movement if thus selected in Object Location Tones settings panel.
* **Settings Panel**: The settings panel allows for further customization of positional tone reporting. You can adjust the tone duration for navigation and caret reporting individually, choose how caret movements are reported (lines, columns, both, or none), and decide whether caret movements during typing are reported or not. Mouse-related settings include automatic start of real-time monitoring when the mouse moves and adjusting the timeout duration for mouse monitoring. There are options controlling the volume level of positional tones and their stereo direction as well. More options will be added in future releases.

## Important Notes:

* The `Ctrl+NumpadDelete` gesture will disable both navigation and caret reporting if it is enabled. This is done for convenience and backward compatibility. Using the gesture again will enable the caret reporting as well, unless it has been explicitly turned off using its gesture or via settings panel before that. To enable caret reporting while navigation reporting is off either use the settings panel, or the `Ctrl+Windows+NumpadDelete` gesture after disabling positional tones for navigation.
* If a control is somewhere off-screen, tones for its location will not be played.
* Some caret location reports may be inaccurate in certain types of input fields, especially in applications with non-native GUI controls. Errors usually occur at the end of documents or when documents are empty.
* If an application's progress bars begin reporting when the interface is brought to focus, and your progress bar reports are set to beeps, there may be some confusion, as Object Location Tones will also produce beeps. Adjusting the positional tone duration in the settings panel may help differentiate between progress bar beeps and positional tones.
* If another add-on uses emulated keypresses (especially with added beeps), interference may occur until you identify how the tones from both add-ons interact. For example, Braille Extender may use emulated keypresses to improve routing experience.
* If another add-on modifies certain parts of NVDA (especially if outdated or incompatible), some events might not be detected by Object Location Tones. For example, Braille Extender might prevent Object Location Tones from detecting typing, resulting in the location of the caret being reported while you type regardless of your settings, which may be annoying.

[1]: https://github.com/dbernaca/objLocationTones/releases/24.07.0
