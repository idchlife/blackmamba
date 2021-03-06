#!python3

from blackmamba.uikit.picker import PickerView, PickerItem, PickerDataSource
import editor
import console
import os
import jedi
from blackmamba.config import get_config_value
import blackmamba.log as log
import blackmamba.ide.tab as tab
import blackmamba.ide.source as source


class LocationPickerItem(PickerItem):
    def __init__(self, path, line, display_folder):
        super().__init__(
            '{}, line {}'.format(os.path.basename(path), line),
            display_folder
        )
        self.path = path
        self.line = line

    def matches_title(self, terms):
        if not terms:
            return True

        start = 0
        for t in terms:
            start = self.path.find(t, start)

            if start == -1:
                return False

            start += len(t)

        return True


class LocationDataSource(PickerDataSource):
    def __init__(self, definitions):
        super().__init__()

        home_folder = os.path.expanduser('~/Documents')

        items = [
            LocationPickerItem(
                definition.module_path,
                definition.line,
                ' • '.join(os.path.dirname(definition.module_path)[len(home_folder) + 1:].split(os.sep))
            )
            for definition in definitions
        ]

        self.items = items


def _select_location(definitions):
    def open_location(item, shift_enter):
        tab.open_file(item.path, line=item.line)

    v = PickerView()
    v.name = '{} usages'.format(definitions[0].name)
    v.datasource = LocationDataSource(definitions)

    v.shift_enter_enabled = False
    v.help_label.text = (
        '⇅ - select • Enter - open file and scroll to location'
        '\n'
        'Esc - close • Cmd . - close with Apple smart keyboard'
    )
    v.textfield.placeholder = 'Start typing to filter usages...'
    v.did_select_item_action = open_location
    v.present('sheet')
    v.wait_modal()


def main():
    if not get_config_value('general.jedi', False):
        log.warn('find_usages disabled, you can enable it by setting general.jedi to True')
        return

    path = editor.get_path()
    if path is None:
        return

    if not path.endswith('.py'):
        return

    tab.save()

    text = editor.get_text()
    if not text:
        return

    line = source.get_line_number()
    column = source.get_column_index()

    if line is None or column is None:
        return

    script = jedi.api.Script(text, line, column, path)
    definitions = [
        d for d in script.usages()
        if d.module_path and d.line
    ]

    if not definitions:
        console.hud_alert('Definition not found', 'error')
        return

    _select_location(definitions)


if __name__ == '__main__':
    main()
