"""Provides a class for handling templates such as XML files or XML fragments with placeholders.
Loads a file matching the given name (without extension).

If no template folder is provided, the folder 'templates' will be used by default.

Usage example:
t = Template('template_name')
t.replace('ph1', 123).replace('ph2', 'abc')
print(t)

"""

import os


class Template:
    PH_PREFIX, PH_SUFFIX = '${', '}'
    DEFAULT_TEMPLATES_FOLDER = 'templates'

    def __init__(self, template_name: str, templates_folder: str = DEFAULT_TEMPLATES_FOLDER):
        matches = [f for f in os.listdir(templates_folder) if f.startswith(template_name)]
        if len(matches) < 1:
            raise ValueError(f"ERROR: no matching template file {template_name} found in {templates_folder}.")
        if len(matches) > 1:
            raise ValueError(f"ERROR: ambiguous: {len(matches)} matching files {matches} in {templates_folder}.")

        template_file_path = os.path.join(templates_folder, matches[0])

        with open(file=template_file_path, encoding='utf-8', mode='r') as template_file:
            self.template_text = template_file.read()
        self.rendered_text = self.template_text

    def replace(self, placeholder: str, value):
        self.rendered_text = self.rendered_text.replace(self.PH_PREFIX + placeholder + self.PH_SUFFIX, str(value))
        return self

    def __str__(self):
        return self.rendered_text
