import logging
import sys
import os
import copy, StringIO, json
import volatility.conf as conf
import volatility.obj as obj
import volatility.registry as registry
import volatility.commands as commands
import volatility.addrspace as addrspace
import volatility.constants as constants
import volatility.exceptions as volexc
from volatility.plugins import imageinfo
import volatility.debug as debug
import volatility.utils as utils

import logging
logger = logging.getLogger(__name__)


##
# Patch the volatility debug to prevent sys.exit calls
##
def new_error(msg):
    raise Exception(msg)

debug.error = new_error

plugin_filters = {
    "drop": ['crashdump', 'crashinfo', 'volshell', 'chromecookies', 'poolpeek', 'impscan', 'hivedump']
}

vol_version = constants.VERSION


def profile_list():
    prof_list = ['AutoDetect']
    profs = registry.get_plugin_classes(obj.Profile)
    for profile in profs.iterkeys():
        prof_list.append(profile)
    return sorted(prof_list)


class RunVol:
    def __init__(self, profile, mem_path):
        # Setup Vol Debugger
        debug.setup()

        registry.PluginImporter()
        self.memdump = mem_path
        self.osprofile = profile
        self.config = None
        self.addr_space = None
        self.init_config()

    def init_config(self):
        """Creates a volatility configuration."""
        if self.config is not None and self.addr_space is not None:
            return self.config

        self.config = conf.ConfObject()
        self.config.optparser.set_conflict_handler("resolve")
        registry.register_global_options(self.config, commands.Command)
        registry.register_global_options(self.config, addrspace.BaseAddressSpace)
        base_conf = {
            "profile": "WinXPSP2x86",
            "use_old_as": None,
            "kdbg": None,
            "help": False,
            "kpcr": None,
            "tz": None,
            "pid": None,
            "output_file": None,
            "physical_offset": None,
            "conf_file": None,
            "dtb": None,
            "output": None,
            "info": None,
            "location": "file://" + self.memdump,
            "plugins": None,
            "debug": 4,
            "cache_dtb": True,
            "filename": None,
            "cache_directory": None,
            "verbose": None,
            "write": False
        }

        if self.osprofile:
            base_conf["profile"] = self.osprofile

        for key, value in base_conf.items():
            self.config.update(key, value)

        self.plugins = registry.get_plugin_classes(commands.Command, lower=True)

        return self.config

    def profile_list(self):
        prof_list = []
        profs = registry.get_plugin_classes(obj.Profile)
        for profile in profs.iterkeys():
            prof_list.append(profile)
        return sorted(prof_list)

    def list_plugins(self):
        plugin_list = []
        cmds = registry.get_plugin_classes(commands.Command, lower=True)
        profs = registry.get_plugin_classes(obj.Profile)
        profile_type = self.config.PROFILE
        if profile_type not in profs:
            print "Not a valid profile"
        profile = profs[profile_type]()
        for cmdname in sorted(cmds):
            command = cmds[cmdname]
            helpline = command.help() or ''

            if command.is_valid_profile(profile):
                plugin_list.append([cmdname, helpline])
        return plugin_list

    def get_dot(self, plugin_class):
        strio = StringIO.StringIO()
        plugin = plugin_class(copy.deepcopy(self.config))
        plugin.render_dot(strio, plugin.calculate())
        return strio.getvalue()
   
    def get_json(self, plugin_class):
        strio = StringIO.StringIO()
        plugin = plugin_class(copy.deepcopy(self.config))
        plugin.render_json(strio, plugin.calculate())
        return json.loads(strio.getvalue())

    def get_text(self, plugin_class):
        strio = StringIO.StringIO()
        plugin = plugin_class(copy.deepcopy(self.config))
        plugin.render_text(strio, plugin.calculate())
        plugin_data = strio.getvalue()

        # Return a json object from our string so it matches the json output.
        # Also going to drop in pre tags here
        return {'columns': ['Plugin Output'], 'rows': [['<pre>\n{0}\n</pre>'.format(plugin_data)]]}

    def run_plugin(self, plugin_name, pid=None, dump_dir=None, plugin_options=None, hive_offset=None, output_style="json"):

        # Get Valid commands
        cmds = registry.get_plugin_classes(commands.Command, lower=True)

        if plugin_name in cmds.keys():
            command = cmds[plugin_name]

            # Set PID
            self.config.PID = pid

            self.config.DUMP_DIR = dump_dir

            self.config.hive_offset = hive_offset

            # Add any other options
            if plugin_options:
                for option, value in plugin_options.iteritems():
                    self.config.update(option, value)
                    
            # Plugins with specific output types
            if plugin_name == 'pstree':
                output_data = self.get_dot(command)
                return output_data
                
            # Just for imageinfo as it occasionally throws unicode errors at me
            elif plugin_name == 'imageinfo':
                output_data = self.get_text(command)
                return output_data
            
            elif plugin_name == 'memdump':
                if not pid:
                    return None
                output_data = self.get_text(command)
                return output_data

            elif plugin_name == 'dumpfiles':
                if 'PHYSOFFSET' not in plugin_options:
                    logger.debug('No Offset Provided')
                    return None
                print self.config.REGEX
                output_data = self.get_text(command)
                print "a"
                print output_data
                return output_data

            # All other plugins
            else:

                if output_style == 'json':
                    output_data = self.get_json(command)
                    return output_data

                if output_style == 'text':
                    output_data = self.get_text(command)
                    return output_data

        else:
            return 'Error: Not a valid plugin'
