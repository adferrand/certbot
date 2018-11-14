import zope

from certbot import interfaces
from certbot.plugins import common


@zope.interface.implementer(interfaces.IAuthenticator, interfaces.IInstaller)
@zope.interface.provider(interfaces.IPluginFactory)
class IISConfigurator(common.Installer):

    description = "Configure IIS"

    @classmethod
    def add_parser_arguments(cls, add):
        # Nothing to do
        pass

    def prepare(self):
        print('Hello World')
