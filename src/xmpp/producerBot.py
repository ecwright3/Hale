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

import sleekxmpp, random, time

class Singleton(type):
    """
    Singleton pattern used to only create one 
    ProducerBot instance
    """
    
    def __init__(cls, name, bases, dict):
        """
        Constructor
        """
        
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None
 
    def __call__(cls, *args, **kw):
        """
        Return instance
        """
        
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
 
        return cls.instance

class ProducerBot(object):
    """
    Producer put logs to a group room on a 
    XMPP server
    """
    
    __metaclass__ = Singleton
    
    def __init__(self, xmppConf):
        """
        Constructor, set up event handlers and register
        plugins
        """
        
        self.currentId = 0
        self.monitoredBotnets = []
        self.foundTrack = False
        self.password = xmppConf.get("xmpp", "password")
        self.server = xmppConf.get("xmpp", "server")
        self.jid = xmppConf.get("xmpp", "jid");
        self.sharechannel = xmppConf.get("xmpp", "datashare_channel") + "@conference." + self.server
        self.sharepass = xmppConf.get("xmpp", "datashare_pass")
        self.coordchannel = xmppConf.get("xmpp", "coordination_channel") + "@conference." + self.server
        self.coordpass = xmppConf.get("xmpp", "coordination_pass")
        
        self.port = xmppConf.get("xmpp", "port")
        self.xmpp = sleekxmpp.ClientXMPP(self.jid, self.password)
        self.xmpp.registerPlugin("xep_0045")
        self.xmpp.add_event_handler("session_start", self.handleXMPPConnected)
        self.xmpp.add_event_handler("disconnected", self.handleXMPPDisconnected)
        self.xmpp.add_event_handler("groupchat_message", self.handleIncomingGroupChatMessage) 
        
    def disconnect(self, reconnect=False):
        """
        Close connection to XMPP server
        """
        
        self.xmpp.sendPresence(pshow='unavailable')
        self.xmpp.disconnect(reconnect)
        
    def run(self):
        """
        Connect to XMPP server and start thread
        """

        self.xmpp.connect((self.server, int(self.port)))
        self.xmpp.process()
        
    def handleXMPPDisconnected(self, event):
    
        print ""

    def handleXMPPConnected(self, event):
        """
        On sucessful connection join specified
        group room
        """
        
        self.xmpp.sendPresence()
        muc = self.xmpp.plugin["xep_0045"]
        join = muc.joinMUC(self.sharechannel, self.jid.split('@')[0], password=self.sharepass)
        join = muc.joinMUC(self.coordchannel, self.jid.split('@')[0], password=self.coordpass)
        
    def handle_trackReq(self, iqObject):
        print "got trackreq!"
        
    def sendTrackReq(self, botnet):
        """
        TODO
        """
        
        randomId = str(random.randint(1, 10000))
        self.currentId = randomId
        msg = 'trackReq id=' + randomId + " " + 'botnet=' + botnet
        self.xmpp.sendMessage(self.coordchannel, msg, None, "groupchat")
        time.sleep(2)
        self.currentId = 0
        if self.foundTrack:
            self.foundTrack = False
            return True
        self.monitoredBotnets.append(botnet)
        return False 
        
    def removeBotnet(self, botnet):
        """
        TODO
        """
        
        self.monitoredBotnets.remove(botnet)
        
    def getMonitoredBotnets(self):
        """
        TODO
        """
        
        return self.monitoredBotnets
        
    def handleIncomingGroupChatMessage(self, message):
        """
        TODO
        """
        
        channel = str(message['from'])
        coordchan = self.coordchannel.split('@')[0]
        if channel.split('@')[0] == coordchan:
            body = message['body'].split(' ')
            if body[0] == 'trackReq' and len(body) == 3:
                idStr = body[1].split('=')[1]
                botnetStr = body[2].split('=')[1]
                
                if botnetStr in self.monitoredBotnets and idStr != self.currentId:
                    msg = "trackAnswer id=" + idStr
                    self.xmpp.sendMessage(self.coordchannel, msg, None, "groupchat")
                    
            if body[0] == 'trackAnswer' and len(body) == 2:
                idStr = body[1].split('=')[1]
                if self.currentId == idStr:
                    self.foundTrack = True
                 
    
    def sendLog(self, msg):
        """
        Send logs to group room
        """
        
        self.xmpp.sendMessage(self.sharechannel, msg, None, "groupchat")
        
        