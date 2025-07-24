# Object Location Tones

* **Author**: Joseph Lee
* **Maintainer**: Dalen
* **Download**: [Stable Version][1]
* **NVDA Compatibility**: 2023.1 and later

After installing this add-on and restarting NVDA, you will hear tones to indicate the location of different objects on the screen as you navigate. To turn off object location reporting, press `Ctrl+NumpadDelete`. To enable it again, use the same gesture. Object Location Tones will remember your preference, and when NVDA starts, it will retain the last state. All settings will persist, even after disabling and re-enabling the add-on.

## Features:

* **Report Focused Object's Location**: During navigation, a positional tone will indicate the currently focused object's location. This feature helps you understand an application's or website's layout, scroll through long menus or file lists faster, and gain a better sense of how your OS behaves visually.
* **Report Caret Location in Text Fields**: When navigating within editable input fields, positional tones will indicate the caret's location. This helps you perceive how the document is scrolled both horizontally and vertically, how long your lines are and when and where they are wrapped, better manage indentations, and more.
* **Toggle Positional Tones**: You can toggle the automatic positional tones on or off using `Ctrl+NumpadDelete` gesture. This feature lets you activate positional tones during navigation only when you need it.
* **Toggle Caret Reporting**: Use `Ctrl+Windows+NumpadDelete` gesture to turn caret location reporting on or off. This allows you to keep positional tones active during navigation while disabling them for text fields (or vice versa).
* **Explicitly Report Object Location**: Press `NumpadDelete` to explicitly report the focused object's location. In editable input fields, it will report the caret's position if caret reporting is turned on. This is useful when tones during navigation are off, or when you want to hear the location of the focused object again without having to navigate away from it first.
* **Explicitly Report Mouse Cursor Location**: Use `Windows+NumpadDelete` gesture to report the mouse cursor's location via a positional tone.
* **Report Object's Outline**: Use `Ctrl+Shift+NumpadDelete` gesture to hear a positional tone indicating the outline of the currently focused graphical object. This gives you a sense of the size and location of UI controls or other elements, which can be helpful in understanding how visual elements are arranged on the screen. This feature is very useful in GUI development.
* **Report Parent's Outline**: Use `Ctrl+Alt+Shift+NumpadDelete` gesture to hear the outline of the currently focused object's parent. Pressing it multiple times moves further up the ancestry chain. This feature helps you understand the relationships between the focused object and its ancestors, which is particularly useful for GUI development.
* **Continuous Mouse Location Reporting**: Use `Shift+NumpadDelete` gesture to turn on continuous reporting of the mouse cursor's location in relation to a reference point. This feature plays one tone for the mouse and another for the reference point. The reference point is by default set to be a location of currently focused object or system caret if caret reporting is enabled, but it can be changed in the settings panel. Other options are the location of the center of the screen, the center of the foreground window or top left corner of both mentioned, or None, which excludes the reference point from the output. The feature remains active until the same gesture is used to turn it off or the mouse stops moving. This is helpful in applications or websites where interaction is only possible with the mouse, and it can also assist with text editing and selection. This feature can be automatically activated upon mouse movement if thus selected in Object Location Tones settings panel.
* **Cycle Through Caret Reporting Modes**: Use the `Ctrl+Alt+Windows+NumpadDelete` gesture to cycle through different caret reporting modes. Available modes include: **Lines**: Reports caret movements only when moving up or down lines; **Columns**: Reports caret movements only when moving left or right across text; **Lines & Columns**: Reports caret movements in both vertical and horizontal directions; **None**: Disables caret movement reporting in editable text fields. This feature allows for precise customization of how you receive feedback while editing text, adapting to various workflows and preferences.
* **Use Musical Instrument Digital Interface (MIDI) for tone generation**: This feature allows you to use software or hardware musical synthesizers that support MIDI to produce tones instead of the classic NVDA beeps. You can opt for tones produced by any instrument defined by General Midi Level 1 standard. Microsoft Windows has a built-in MIDI synthesizer so you can use the feature right away. The feature can be activated in Object Location Tones settings panel. Although stable, this feature is still in its experimental stage, because it relies on resources otside of NVDA's control. Please read the section below on using MIDI and how to correctly set it up so that you get positional tones that correctly reflect the on-screen locations.
* **Settings Panel**: The settings panel allows for further customization of positional tone reporting. You can adjust the tone duration for navigation and caret reporting individually, choose how caret movements are reported (lines, columns, both, or none), and decide whether caret movements during typing are reported or not. Mouse-related settings include automatic start of real-time monitoring when the mouse moves and adjusting the timeout duration for mouse monitoring, choosing a reference point for the mouse monitoring and setting the distance to targeted location sensibility. There are options controlling the volume level of positional tones and their stereo direction as well. You may also choose to use MIDI for tones instead of classic NVDA beeps and choose the MIDI instrument to use. More options will be added in future releases.

## MIDI-based tone generation

MIDI (Musical Instrument Digital Interface) is not audio, it is a protocol used to tell a MIDI compatible synthesizer which note to play, which instrument to use, how loud, and for how long. Using MIDI for location tones gives you a more musical way to hear position on the screen. You can choose different instruments, get more distinctive pitch steps using all 128 MIDI notes, and generally create a more pleasant listening experience that gives potentially more expressive and intelligible sound cues.
When you enable the **Use Musical Instrument Digital Interface (MIDI) for tone generation** option in settings, Object Location Tones will start sending MIDI note events instead of using NVDA's built-in tones.beep() function. These events go directly to the default MIDI output device set in your Windows system. Most of the time, this will be the **Microsoft GS Wavetable Synth**, a built-in software synthesizer that has been included since **Windows 98**.
Right after you activate the checkbox, you will be warned that the option is experimental and asked for confirmation. This is because tone production using MIDI instructions depends on software and hardware elements outside of NVDA's control and there can be so many different setups. For example, if something is wrong with your software synthesizer, a synthesizer volume is down or your hardware synthesizer is turned off or configured incorrectly you will simply not hear positional tones while Object Location Tones add-on will not be aware that anything is wrong. Usual occurrence with third party synthesizers will be that they will stop working after computer wakes up from sleep or hibernation or when virtual machine resumes execution. In these cases, going to settings, disabling and reenabling MIDI will solve the problem. The experimental warning will be changed or removed after collected feedback from users helps mitigate mentioned problems.

### Limitations of Microsoft's built-in synth

While it works out of the box, which is excellent because it allows Object Location Tones to work with MIDI with no additional requirements, the Microsoft GS Wavetable Synth has some serious limitations:

* It is old and inefficient and has not been updated in decades.
* It has **noticeable latency**, often between **30 ms and over 1 second**, depending on your machine and audio drivers. This lag is especially bad for mouse monitoring or fast navigation , where you need instant feedback.
* It cannot load or change SoundFonts. You are limited to the General MIDI instruments it ships with.
* It does not support audio effects like reverb, chorus, or filter envelopes. Because of this, instruments often sound dry, flat, and lacking in spatial depth.
* Some instruments don’t play the full range of MIDI notes (0–127), which means parts of the screen may give incorrect tones for vertical navigation.

That said, one good thing about GS Wavetable Synth is that instruments **are mono**, which helps with accurate horizontal spatial mapping.

### You can get better results with third-party software synthesizers

If you want more responsive and flexible sound, you can install a better software synthesizer. Two popular ones that are free:

* [**CoolSoft VirtualMIDISynth**](https://coolsoft.altervista.org/en/virtualmidisynth)  
  Easy to use, comes with a nice interface, and can set itself as the system's default MIDI device. Lets you load your own SoundFonts and configure everything from a control panel.

* [**FluidSynth**](https://www.fluidsynth.org/)  
  Designed for real-time audio with very low latency. It is powerful and fast, but has no built-in GUI. It is more suitable if you are comfortable with command-line tools or external front-ends like Qsynth.

To use either of these with Object Location Tones, you will need to make sure they’re set as your default MIDI output. CoolSoft can handle this automatically. Otherwise, you will need to adjust the system MIDI Mapper or use a routing tool. You will also need to download and set a SoundFont to use with any of the two synthesizers.
You can find a good selection of free SoundFonts listed on the official website of the [**CoolSoft VirtualMIDISynth**](https://coolsoft.altervista.org/en/virtualmidisynth) 

### SoundFonts: what to look for

SoundFonts are files (*.sf2) that contain sampled instruments. Your synthesizer will use these to actually play the MIDI notes. For this add-on, you don’t need anything fancy, but you should keep a few things in mind:

* The instrument used for positional tones must be **mono**. Stereo instruments (like many pianos) can distort the screen position to stereo space mapping and your horizontal plane location output will be wrong.
* The instrument must not have a slow attack or fade-in at the start (common in string instruments), otherwise the note can be inaudible because of the tone duration settings and even if it can be heard, you will have a delayed positional feedback.
* The instrument  should cover **all 128 MIDI notes (0 to 127)**. If it doesn’t, you’ll have incorrect tone pitch to vertical plane mapping
* Try to pick a **compact SoundFont**, something around **32 MB** in size. This keeps memory usage low while still sounding good. Huge SoundFonts made for music production don’t add anything useful here and just waste RAM.

You can choose which instrument the add-on uses from its settings. After selecting one, it’s a good idea to test how it behaves when used for positional feedback. To check this, navigate across fixed interface areas like the desktop, taskbar, Start menu, and system tray. If notes drop out or feel mismatched in height, especially toward screen's top and bottom edges, or elements that are one below another such as menu items are reported to have drastically different horizontal position, especially between screen's top or bottom edges, switch to another instrument.

### For advanced users

If you are a musician or have MIDI gear, you can also route the MIDI output to a **hardware synthesizer** or **MIDI sound module**. As long as the device shows up as a standard MIDI output and can be set as the default, it will work with this add-on. This setup gives you full control over sound and latency, though it takes a little bit more effort to configure.

## Important Notes:

* The `Ctrl+NumpadDelete` gesture will disable both navigation and caret reporting if it is enabled. This is done for convenience and backward compatibility. Using the gesture again will enable the caret reporting as well, unless it has been explicitly turned off using its gesture or via settings panel before that. To enable caret reporting while navigation reporting is off either use the settings panel, or the `Ctrl+Windows+NumpadDelete` gesture after disabling positional tones for navigation.
* If a control is somewhere off-screen, tones for its location will not be played.
* Some caret location reports may be inaccurate in certain types of input fields, especially in applications with non-native GUI controls. Errors usually occur at the end of documents or when documents are empty.
* If you choose to use MIDI for tone generation, make sure that the chosen instrument from the chosen sound font is mono and has no delay at note beginnings. Otherwise positional tones will not match positions on the screen or can be inaudible due to the positional tone duration, or both. Also, ensure that the instrument covers whole 0-128 note range in order to be sure that the positional tones are correct and/or audible.
* If an application's progress bars begin reporting when the interface is brought to focus, and your progress bar reports are set to beeps, and you are not using MIDI for tone generation, there may be some confusion, as Object Location Tones will also produce beeps. Using MIDI or adjusting the positional tone duration in the settings panel may help differentiate between progress bar beeps and positional tones.
* If another add-on uses emulated keypresses (especially with added beeps while you are not using MIDI), interference may occur until you identify how the tones from both add-ons interact. For example, Braille Extender may use emulated keypresses to improve routing experience.
* If another add-on modifies certain parts of NVDA (especially if outdated or incompatible), some events might not be detected by Object Location Tones. For example, Braille Extender might prevent Object Location Tones from detecting typing, resulting in the location of the caret being reported while you type regardless of your settings, which may be annoying.

[1]: https://github.com/dbernaca/objLocationTones/releases/25.1.0
