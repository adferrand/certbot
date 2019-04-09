"""Certbot PyLint plugin.

http://docs.pylint.org/plugins.html

"""
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
            'Forbidden use of os module, certbot.compat.os must be used instead',
            'os-module-forbidden',
            'Some methods from standard os modules cannot be used for security reasons on Windows: '
            'the safe wrapper certbot.compat.os must be used instead in Certbot.'
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
