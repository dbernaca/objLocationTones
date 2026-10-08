# Object Location Tones

* **Author**: Joseph Lee
* **Maintainer**: Dalen
* **Current Version**: [26.1.0](https://github.com/dbernaca/objLocationTones/releases/26.1.0)
* **NVDA Compatibility**: 2023.1 and later

Object Location Tones is an NVDA add-on that adds positional audio capability to the NVDA screen reader via positional tones.  
After installing this add-on and restarting NVDA, you will hear tones to indicate the location of different objects on the screen as you navigate. Higher tones represent locations nearer to the top of the screen, lower tones represent locations nearer to the bottom, and stereo balance indicates whether something is more to the left or to the right.

Object Location Tones can report the current object's location during navigation, the caret's location in editable text fields, the mouse pointer's location, object outlines, parent outlines, foreground window outlines, and continuous mouse position in relation to a configurable reference point. These positional audio cues can help you understand how applications, dialogs, websites, and text fields are arranged visually, how documents are scrolled and lines wrapped, and it can also be useful in GUI development and in tasks where the mouse or touch navigation is required.  
To produce positional tones, Object Location Tones uses native NVDA beeps, but is capable of using Musical Instrument Digital Interface (MIDI) for externally managed tone generation as well.

This README is only a shorter GitHub landing page. For complete usage information, settings details, gestures, MIDI notes, and technical explanation, please read the full documentation linked below.

* [Full documentation](https://dbernaca.github.io/objLocationTones/addon/doc/en/readme.html)
* [Technical changelog](../changelog.md)
* [Technical TODO list](../TODO.txt)
* [Latest release](https://github.com/dbernaca/objLocationTones/releases/latest)
* [Issue tracker](https://github.com/dbernaca/objLocationTones/issues)
* [License](../COPYING.txt)

***

## Installing, building, and translating

### Installing the add-on

The preferred and recommended way to install and use Object Location Tones is via NVDA's `Add-on Store`.:

1. Open the NVDA menu (`NVDA+N` or using NVDA's Taskbar icon) and go to `Tools --> Add-on store...`.
2. Use the search input field to find `Object Location Tones` or locate it manually in the list of available add-ons in the `Available add-ons` tab.
3. Press Enter on it, or use the `Actions` button to open the pop-up menu.
4. Select Install and close the `Add-on store`.

Alternatively, download pre-built `*.nvda-addon` bundle of the [latest release](https://github.com/dbernaca/objLocationTones/releases/latest), open the downloaded file, and follow the steps required by NVDA's add-on installation process.

Important bugs are fixed and published as soon as possible, together with small improvements in patch releases when needed. Therefore, a regular user will generally gain little from building and installing the add-on from source. They may instead encounter unfinished features still under development or bugs awaiting a fix.  
For regular use, the recommended installation methods are the `Add-on Store` or the pre-built `*.nvda-addon` package available from the latest release. Building from source is not recommended for regular users.

### Building the add-on

Object Location Tones uses `nvaddon` tool from NVDAAddonKit by Beka Gozalishvili as its bundling system.  
To create a `*.nvda-addon` file from source on your own, the following steps are recommended:

* Install `nvda-addon-kit` and Python Markdown extra extensions needed to build the add-on and render documentation, from Python Package Index, using pip:

```bash
python -m pip install nvda-addon-kit
python -m pip install pymdown-extensions
```

* Acquire the Object Location Tones source from the repository and enter its root directory:

```bash
git clone https://github.com/dbernaca/objLocationTones.git
cd objLocationTones
```

* Use the `nvaddon` tool on it to build the add-on package:

```bash
python -m nvaddon build
```

* Or use `nvaddon` to build and install the add-on directly into NVDA:

```bash
python -m nvaddon install
```

You do not need to run both commands. Use `build` if you only want the packaged add-on file. Use `install` if you want to build the add-on and install it immediately into NVDA for local testing.

If you have Python's Scripts directory added to your `PATH` environment variable, you can call both `pip` and `nvaddon` directly from the shell.

Note that `master` branch of the repo is being constantly used in development flow. So before you decide to build and use the add-on from source, it is recommended to check the git log first. If there are unresolved commits marked as work in progress (WIP) affecting the code present, it is possible that you will end up with the add-on containing incomplete or buggy features. If you still want to build from the source, but want a specific state that you are happy with, use `git switch` to move to the tag or commit you want before building the add-on.

For example:

```bash
git switch --detach 26.1.0
python -m nvaddon build
```

If you choose a point in history from before the add-on switched building systems from the older add-on template to NVDAAddonKit, you can still use `nvaddon` to build it, but you first have to use its migration process with the `migrate` command in order to transform the add-on's working tree to support the newer system.

Any kind of contribution is welcome, including problem reports, criticism, issues, pull requests, code improvements, documentation improvements, and translations.

### Translating the add-on

Object Location Tones has all its translatable strings in one module, `UIStrings.py`.  
They are commented and sorted mostly as they appeared along with new features in new add-on versions.
The add-on currently includes translations to Croatian, Italian, and Spanish, in addition to English.
However, `nvaddon` supports creation of a POT file from the add-on and managing new translations.
Using command:

```bash
python -m nvaddon locale-add <language_code>
```

while in the add-on's directory tree, will create both `*.pot` template and `*.po` file for the specified language in its correct location.
Using:

```bash
python -m nvaddon locale-compile
```

will compile all `*.po` files into `*.mo` for usage by gettext in NVDA.
When you use:

```bash
python -m nvaddon build
```

all your `*.po` files will be compiled automatically and appropriate manifest messages will be deposited into translated `manifest.ini` files in the locales folder before building.

If you are interested in contributing to Object Location Tones by translating it, please use `nvaddon` to create a `*.po` file for the language you want to add, translate it using your favourite editor or method, and send the result to be included in next Object Location Tones version, either via e-mail or using a pull request.

## Copyright and license

Copyright (C) 2017-2024 by Joseph Lee, released under GPL  
Copyright (C) 2024-2026 by Dalen Bernaca, released under GPL  
All rights reserved.

Object Location Tones is free software: you can redistribute it and/or modify it under the terms of the [GNU General Public License, version 2 or later](../COPYING.txt), as published by the Free Software Foundation.

Object Location Tones is distributed in the hope that it will be useful, but **without any warranty**; without even the implied warranty of merchantability or fitness for a particular purpose. See the [GNU General Public License](../COPYING.txt) for more details.
