# Translating


Thanks for considering to translate the project!

There are 2 options for translating:

- Translate online with [Crowdin](https://crowdin.com/project/panel-cleaner/invite?h=5c2a97ea5dd60dc872c64a138e0705f61973200)

- Translate offline by using git to fork the repository and submit a pull request.

Note: The German translations are official and may provide additional context if the English is ambiguous.
Improvements are nonetheless welcome.

### Language not supported yet?

Open an issue on Github and I will add it to Crowdin.

### Notice

- You may localize the name of the project in the app, though this will need to be reflected in the 
  PanelCleaner.desktop file as well, which cannot be done through Crowdin.

- If you see the word `&apos;` in the text, it is a single quote ('), which has no significance for formatting.
  Remove them from your translation if they are not needed.

- Any # characters in the text are for Markdown formatting. You can adjust the line wrapping as needed, 
  beginning new lines with another #.

## Online

Sign up for [Crowdin](https://crowdin.com/project/panel-cleaner/invite?h=5c2a97ea5dd60dc872c64a138e0705f61973200) and join the project, then you can translate online. Changes are automatically synced to the repository after approval.

DeepL suggestions are available for most languages, to hopefully speed up the process.

## Offline

You can fork the repository and edit the Qt .ts files in the `translations` folder.
You need to install the [Qt Linguist](https://www.qt.io/download) tool to edit these files.

![Qt Linguist](https://github.com/VoxelCubes/PanelCleaner/blob/master/media/screenshots/linguist.png)

This Program will provide previews and better context than Crowdin, but you can also simply use it for the context alone, while inputting translations into Crowdin.

Note: This method requires some additional experience with git.

You can test your translations if you build the project from source. 
You can also download the edited Qt .ts file from Crowdin and use it locally.

- Overwrite the file you were editing with Qt Linguist in the `translations` folder.

- Ensure your language is already included in the file `pcleaner/gui/supported_languages.py` and also enabled (the True). For American English, it would look like this:
```Python
"en_US": ("English (US)", True),
```

- Run `make refresh-assets` in the project's root folder to update the translations from your local file.

- Then run Panel Cleaner from source, select your new language, then restart to see the changes.
