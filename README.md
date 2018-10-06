# Kite Python Assistant

Kite is an AI-powered programming assistant that helps you write Python code inside Sublime Text 3. The 
[Kite Engine](https://kite.com/) needs to be installed in order for the package to work properly. The package itself
provides the frontend that interfaces with the Kite Engine, which performs all the code analysis and machine learning.


## Features

Kite's goal is to help you write code faster by showing you the right information at the right time. At a high level,
Kite provides you with:
* 🧠 __Smart autocompletions__ powered by machine learning models trained on the entire open source code universe
* 👀 __Advanced function signatures__ that show you not only the official signature of a function, but also the most 
popular ways other developers call the function
* 🔍 __Instant documentation__ for the symbol underneath your cursor


## Requirements

* macOS 10.10+ or Windows 7+
* Sublime Text build 3000+
* [Kite Engine](https://kite.com/)


## Installation

### Installing the Kite Engine

__macOS Instructions__
1. Download the [installer](https://kite.com/download) and open the downloaded `.dmg` file.
2. Drag the Kite icon into the `Applications` folder.
3. Run `Kite.app` to start the Kite Engine.

__Windows Instructions__
1. Download the [installer](https://kite.com/download) and run the downloaded `.exe` file.
2. The installer should run the Kite Engine automatically after installation is complete.

### Installing the Kite Assistant for Sublime

When running the Kite Engine for the first time, you'll be guided through a setup process which will allow you to install
the Sublime package. You can also install or uninstall the Sublime package at any time using the Kite Engine's [plugin
manager](https://help.kite.com/article/62-managing-editor-plugins).

Alternatively, you can `git clone` this repoistory directly into your Sublime `Packages` directory. You can locate your
`Packages` directory by opening Sublime, clicking on the `Preferences` menu item, then selecting `Browse Packages...`.


## Usage

This is a quick guide to using Kite in its default configuration.
