# This code does two things -- 1. Convert excel to html
# 2. Add definite header and trailer to the generated html

import paths
from xlsx2html import xlsx2html

header_content = '''{% extends "layout.html" %}
{% block page_title %} Details on replace_text !{% endblock %}
{% block body %}
    {{ super() }}
'''

trailer_content = '{% endblock %}'


def excel_to_html(input_path, sheet_name):
    xlsx2html(input_path, paths.flask2_templates + 'TEMP.html', sheet=sheet_name)

    # The below part takes care of adding headed and trailer to TEMP.html
    input_file = paths.flask2_templates + 'TEMP.html'
    with open(input_file, 'r') as contents:  # First time opening the file
        save = contents.read()
    with open(input_file,
              'w') as contents:  # On the ame file appending the header text, this deletes the original content
        contents.write(header_content.replace('replace_text', sheet_name))
    with open(input_file, 'a') as contents:  # This time appending the original content
        contents.write(save)
    with open(input_file, 'a') as contents:  # This time appending the trailer content
        contents.write(trailer_content)
    return input_file
