################################################################################
#   (c) 2010, The Honeynet Project
#   Author: Patrik Lantz  patrik@pjlantz.com
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
################################################################################

import cmd, sys, os, signal
import threading, time
from conf import configHandler
from modules import moduleManager
from utils import moduleCoordinator
from xmpp import producerBot
from ConfigParser import *

if os.name == "nt":
    try:
        import pyreadline
    except ImportError:
        print "Error: Windows PyReadline support missing"
        sys.exit(1)

class CLI(cmd.Cmd):
    """
    Handles command line input with support for 
    command line completion and command history. 
    Additionally the cmd module provides a nice help feature,
    the comments for the do_command functions are shown 
    when issuing help <command>
    """
	
    def __init__(self):
        """
        Constructor, sets up cmd variables and other
        data structures holding modules, configs etc.
        Starts a manager thread taking care of newly
        added modules and errors from module threads
        """
        
        cmd.Cmd.__init__(self)
        self.prompt = ">> "
        self.intro = "\nType help or '?' for a list of commands\n"
        moduleManager.handle_modules_onstart()
        moduleCoordinator.ModuleCoordinator().start()
        self.xmppConf = configHandler.ConfigHandler().loadXMPPConf()
        producerBot.ProducerBot(self.xmppConf).run()
        self.moduleDirChange = ModuleDirChangeThread()
        self.moduleDirChange.start()
        self.config = configHandler.ConfigHandler()
        self.modlist = []
        
    def do_exec(self, arg):
        """
        Execute a module with the current config. 
        Usage: exec modulename identifier
        """
        
        args = arg.split(' ')
        if len(args) < 2:
            print "Usage: exec modulename identifier"
            return
        arg3 = configHandler.ConfigHandler().getCurrentHash()
        moduleManager.execute(args[0], args[1], arg3)
        
    def do_xreload(self, arg):
        """
        Reload the XMPP configuration and restart
        the producer bot
        """
        
        producerBot.ProducerBot().disconnectBot(reconnect=True)
        self.xmppConf = configHandler.ConfigHandler().loadXMPPConf()
        producerBot.ProducerBot(self.xmppConf)
        producerBot.ProducerBot().run()
        
    def do_stop(self, arg):
        """
        Stops a module identified by id
        Usage: stop id
        """
        
        moduleCoordinator.ModuleCoordinator().stop(arg)
    
    def do_lsmod(self, arg):
        """
        List all modules currently installed
        """
        
        lsStr = "\nInstalled modules\n=================\n"
        self.modlist = moduleManager.get_modules()
        for mod in self.modlist:
            lsStr += mod + "\n"
        print lsStr
            
    def do_lsexec(self, arg):
        """
        List all modules being executed at the moment
        """
        
        idlist = moduleCoordinator.ModuleCoordinator().getAll()
        if len(idlist) == 0:
            print "No modules running"
        else:
            listStr = "\nModule ID\n=========\n"
            for ident in idlist:
                listStr += ident + "\n"
            print listStr
            
    def do_lsconf(self, arg):
        """
        List all configurations
        """
        
        self.config.listConf()
        
    def do_reload(self, arg):
        """
        Reload a module if changes have been made to it
        Usage: reload modulename
        """
        
        moduleManager.reload_module(arg)
        
    def do_useconf(self, arg):
        """
        Set the current config to use, if argument
        is empty, current config used is printed out
        """
        
        self.config.useConf(arg)
        
    
    def default(self, line):
        """
        Called when command input is not recognized
        and outputs an error message
        """
        
        print "Unkown command: " + line
        
    def emptyline(self):
        """
        Called when empty line was entered at the prompt
        """
        
        pass
        
    def do_quit(self, arg):
        """
        Exit the program gracefully
        """
        
        self.do_exit(arg)
        
    def do_showlog(self, arg):
        """
        Show recent logs from the monitor
        and the modules
        """
        
        moduleCoordinator.ModuleCoordinator().getErrors()
        
    def do_exit(self, arg):
        """
        Exit the program gracefully
        """
        
        print "Shutting down.."
        self.moduleDirChange.stop()
        self.moduleDirChange.join()
        moduleCoordinator.ModuleCoordinator().stopAll()
        producerBot.ProducerBot().disconnectBot()
        sys.exit(0)
        
class ModuleDirChangeThread(threading.Thread):
    """
    This thread call the function 'load_modules'
    in moduleManager periodically to check for 
    newly registered modules and modules recently removed
    """

    def __init__(self):
        """
        Constructor, sets continue flag
        """
        
        self.continueThis = True
        threading.Thread.__init__ (self)

    def run(self):
        """
        Handles the call to 'load_modules'
        """
        
        while self.continueThis:
            moduleManager.load_modules()
            time.sleep(1)
            
    def stop(self):
        """
        Mark the continue flag to stop thread
        """
        
        self.continueThis = False

def set_ctrlc_handler(func):
    """
    Catch CTRL+C and let the function
    on_ctrlc take care of it
    """
    
    signal.signal(signal.SIGINT, func)

if __name__ == "__main__":
    """
    Main program starts
    """
    
    os.environ["DJANGO_SETTINGS_MODULE"] = "webdb.settings.py"    
    
    def on_ctrlc(sig, func=None):
        """
        Ignore pressed CTRL+C
        """
        pass

    set_ctrlc_handler(on_ctrlc)
    CLI().cmdloop()
            
