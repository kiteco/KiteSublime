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

The following is a brief guide to using Kite in its default configuration.

### Hover

Hover your mouse cursor over a symbol to view a short summary of what the symbol represents.

![hover](https://ucba9366f31fbb1d34e249290424.previews.dropboxusercontent.com/p/thumb/AAPflyMkT7THcJ9X1SIS4pa4DCW1Etqiaf2IXWuB2UizheI7qstKEUjEdxEz-N1G-oxX9xT_zsIXYkw-5iSPIgs7NT1vEF-lRF9RtFcFmv3MM4JAbHAgw4i5ebdUofYc8aJmCXHYKEd9vdC13vpt1Wp_pjooKxM25GxdCoIxF8fQ8leHNjong4PZmKH_oYV1pS_LsKp25GfV8XCl4MnVQapBhRnv5gZ4fOXWF05JtiHLCg/p.png?size=2048x1536&size_mode=3)

If the built-in `show_definition` preference is enabled, Kite will show you the definitions and references found in the 
Sublime index as usual.

![hover-show-definition](https://uccb328d6cfc4a140ccc8e701308.previews.dropboxusercontent.com/p/thumb/AANB1bPZpvCl9x66bQFywkzIF2C6oqAu7fmy-b1fudNZcW-AEd1jTo6rsRvWnebkGSobjcw92piXY-IqnmpHY9Ljamaj51AGLAMMMRdOVjuKZVVBCJ82N14UZE1Rf1iWM8PMgGdryzsgXcqdc-7V4MrGSoP7LpK6aL2RTzLBB2e9eSrSkjOE5-tba8N-9JayIT2uIP7vylMu6uZlwbbZQNEorO6K8N12hQvCyzcS07VDKg/p.png?size=2048x1536&size_mode=3)

### Documentation

Click on the `Docs` link in the hover popup to open the documentation for the symbol inside the Copilot, Kite's standalone
reference tool.

![copilot](https://uc18d1e287a81a61f02d957c2b01.previews.dropboxusercontent.com/p/thumb/AAOpgZ0ddsXiuS4PaRFW0AKxDVbR9Upw4PCCgDLJm_gIGsRpbH31sirZ-bnOxz4Wu-9xH3G8OniKhpK3wugSLomAVS4ZtaiIIE2zba7FChKeHzug0LMgNUTlpjt9om56WJ_UZC65M9kVtC2DbTQj7fFnHT_sHGSOLQDsW3wZKg96PUT7KxztuiT5Ixj2J2Js_Rj-Cd4aX9Oo3fRaghKqLHHwIH4Gvgb5k2TnTP68g3KMDg/p.png?size=2048x1536&size_mode=3)

### Definitions

If a `Def` link is available in the hover popup, clicking on it will jump to the definition of the symbol.

### Autocompletions

Simply start typing in a saved Python file and Kite will automatically suggest completions for what you're typing.

![completions](https://uc55943b22c530f3ea08b2ccc0f8.previews.dropboxusercontent.com/p/thumb/AAMnAHmtberVIB3XFzbVATFxUfl5yBfOEH90dwXa1MVyAIPKEJExG2DRy-2-SPcz2FycybLmaiGDJj3lKG_JS9NKnjTHtUGW1eCC2l5GKsmES-9DbKZBM-36aPUmUJ-gXMdHPGivmUMr8nUBHkb_oQl0tIrug86JQauH5B9aye3WC0G6PUVLz6S9liF0VtbNMI9jDWiaIl9EMDIAcKosPKB2PaHQ4HDLmlQmhu49gxWG1A/p.png?size=2048x1536&size_mode=3)

### Function Signatures

When you call a function, Kite will show you the arguments required to call it.

![signatures](https://uccaea4be55c637923d518bba883.previews.dropboxusercontent.com/p/thumb/AAO2nJ5kXP6gFyXBYgUscG050zlj6xHmnGzRSvTFw4UxfSNsSKA2MjJkpkIqyKognZdKr2zypGLy7-1PL6CSVDgWQFWqhPEMKcwN0hTSh2w5Ru7ab_Q6GB8bPeEm8SD03QCnfKXxhZDKE2dn3l-NdX53y3oHflPevtGKcWERvGkWuyKM3BVEH8bREJTrQlSksNR5oigmQKXKuAeANgU1tn2pVwPwNx5SCnbNHhMWDancnw/p.png?size=2048x1536&size_mode=3)

Kite also shows you `How others used this` function, which are the most popular calling patterns inferred from all the
open source code on the internet.

### Commands and Keyboard Shortcuts

In case you prefer to not use the mouse, most of Kite's features can be triggered from the command palette.

![commands](https://ucfd0f13fad79640bd12f3843382.previews.dropboxusercontent.com/p/thumb/AAPtO-Gh4jL_6dtFgyvsJwj1O5dbjtlTO4_We1TU_z423asVfB97KuOh_VGEZ6Lu29rChLKzy3WhnSIjpP7-5kjGNyXlMAb_lVLb6Oa9kBEsYSFKr3WkRybvVato2OlwobsmzDe8_8oP-KmolAx7vyTutBpHxjxl_-NUWr7NVu67TP0HJM_a4hbOAxwF-0u1dZtPNaoSPZDDvKyM8-kYYoZ9Mpikxu20ljKT1gd9BzqVZw/p.png?size=2048x1536&size_mode=3)

Furthermore, Kite comes with the following default keyboard shortcuts:

|Command|Shortcut|Description|
|:---|:---|:---|
|**H**over|`ctrl`+`alt`+*__`H`__*|Show the hover popup at your current cursor position|
|**D**ocumentation|`ctrl`+`alt`+*__`D`__*|Show documentation in the Copilot|
|F**U**nction Signatures|`ctrl`+`alt`+*__`U`__*|Show the function signature panel|
|Ke**Y**word Arguments|`ctrl`+`alt`+*__`Y`__*|Show/hide keyword arguments (when function signature panel is shown)|
|**P**opular Patterns|`ctrl`+`alt`+*__`P`__*|Show/hide popular calling patterns (when function signature panel is shown)|

## Configuration

You can change Kite's settings by clicking on `Preferences`, then `Package Settings`, then `Kite`. Alternatively, you can 
access the preferences files from the command palette using `Kite: Package Settings`. The default preferences file should
be self documenting.

## Contact Us

Feel free to contact us with bug reports, feature requests, or general comments at feedback@kite.com.

Happy coding!
