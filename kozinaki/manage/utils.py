import os

from jinja2 import Environment, PackageLoader, meta

PACKAGE_NAME = __name__[:__name__.rfind('.')]


def render_template(template, to_file=None, context=None):
    path, template = os.path.split(template)
    jenv = Environment(loader=PackageLoader(PACKAGE_NAME, path), keep_trailing_newline=True)
    text = jenv.get_template(template).render(**context or {})
    if to_file:
        with open(to_file, 'w') as conf_file:
            conf_file.write(text)
    else:
        return text


def get_templates_vars(templates):
    vars = set()
    templates = [templates] if not isinstance(templates, list) else templates
    for filename in templates:
        path, filename = os.path.split(filename)
        jenv = Environment(loader=PackageLoader(PACKAGE_NAME, path), keep_trailing_newline=True)
        ts = jenv.loader.get_source(jenv, filename)
        pc = jenv.parse(ts[0])
        vars.update(meta.find_undeclared_variables(pc))
    return vars
