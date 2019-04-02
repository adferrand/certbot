"""Certbot PyLint plugin.

http://docs.pylint.org/plugins.html

"""
from astroid import MANAGER
from astroid import nodes
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint.checkers.utils import check_messages


def register(linter):
    """Register this module as PyLint plugin."""
    linter.register_checker(ForbidStandardOsModule(linter))


class ForbidStandardOsModule(BaseChecker):
    """
    This checker ensures that standard os module is not imported by certbot classes.
    Otherwise a 'os-module-forbidden' error will be registered for the faulty lines.
    """
    __implements__ = IAstroidChecker

    name = 'forbid-os-module'
    msgs = {
        'E5001': (
            'Use of os module is forbidden in Certbot, certbot.compat.os must be used instead',
            'os-module-forbidden',
            'Some methods from standard os modules cannot be used for security reasons on Windows: '
            'the safe wrapper certbot.compat.os must be used instead.'
        )
    }
    priority = -1

    # TODO: exclude acme module from the check
    @check_messages('os-module-forbidden')
    def visit_import(self, node):
        if 'os' in [name[0] for name in node.names]:
            self.add_message('os-module-forbidden', node=node)

    # TODO: exclude acme module from the check
    @check_messages('os-module-forbidden')
    def visit_importfrom(self, node):
        if node.modname == 'os':
            self.add_message('os-module-forbidden', node=node)


def _transform(cls):
    # fix the "no-member" error on instances of
    # letsencrypt.acme.util.ImmutableMap subclasses (instance
    # attributes are initialized dynamically based on __slots__)

    # TODO: this is too broad and applies to any tested class...

    if cls.slots() is not None:
        for slot in cls.slots():
            cls.locals[slot.value] = [nodes.EmptyNode()]

    if cls.name == 'JSONObjectWithFields':
        # _fields is magically introduced by JSONObjectWithFieldsMeta
        cls.locals['_fields'] = [nodes.EmptyNode()]


MANAGER.register_transform(nodes.Class, _transform)
