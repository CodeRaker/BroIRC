import socket
import ssl
import threading
import time
import os
import sys
from settings import *

class BroIRC():
    def __init__(self):
        self.ircServer = ircServer
        self.ircPort = ircPort
        self.channels = ircChannels
        self.channelsMuted = []
        self.channelSelected = ""
        self.nickname = nickname
        self.password = password
        self.ping = "PING "
        self.pong = "PONG "
        self.identified = False
        self.listNames = False
        self.promptActive = False
        self.dMethods = {"toggle-rawmode":self.toggleRawmode, "help":self.showHelp, "clear":self.clearScreen, "list-channels":self.listChannels, "mute-channels":self.muteChannels, "unmute-channels":self.unmuteChannels, "select-channel":self.selectChannel, "status":self.showStatus, "list-users":self.listUsers}
        self.dMethodsRequiringData = ["mute-channels","unmute-channels","select-channel","list-users"]
        self.help = '''
These are your commands:
!bro help                    show help
!bro rawmode <on/off>        enable/disable rawmode
!bro clear                   clear the screen
!bro unmute <channel>        show channel messages
!bro mute <channel>          mute channel messages
!bro list channels           list all channels
!bro select <channel>        selects a channel for chat
!bro list users <channel>    shows users in a channel
!bro statistics              shows statistics (under development)
!bro join <channel>          (under development)
!bro leave <channel>         (under development)
'''
        self.banner = '''

M#"""""""'M                    M""M MM"""""""`MM MM'""""'YMM
##  mmmm. `M                   M  M MM  mmmm,  M M' .mmm. `M
#'        .M 88d888b. .d8888b. M  M M'        .M M  MMMMMooM
M#  MMMb.'YM 88'  `88 88'  `88 M  M MM  MMMb. "M M  MMMMMMMM
M#  MMMM'  M 88       88.  .88 M  M MM  MMMMM  M M. `MMM' .M
M#       .;M dP       `88888P' M  M MM  MMMMM  M MM.     .dM
M#########M                    MMMM MMMMMMMMMMMM MMMMMMMMMMM v0.1

'''

    def init(self):
        print(self.banner)
        self.questions()
        self.connect()
        t1 = threading.Thread(target=self.ircCommRecv)
        t1.daemon = True
        t1.start()
        self.promptActive = True

    def questions(self):
        print("All commands start with !bro. To see available commands type: !bro help")
        a1 = input("Do you want to enable raw mode and show server messages? [yes/NO] ")
        if "yes" in a1.lower():
            print("[+] Enabling Raw Mode")
            self.rawmode = True
        else:
            print("[+] Continuing in Normal Mode")
            self.rawmode = False

    def bro(self, command, data):
        if command in self.dMethods:
            if command in self.dMethodsRequiringData:
                if not data:
                    print("[-] Seems as if the command is missing data.")
                else:
                    self.dMethods[command](data)
            else:
                self.dMethods[command]()
        else:
            print("[-] Command not recognized")

    #bro methods
    def toggleRawmode(self):
        if not self.rawmode:
            self.rawmode = True
            print("[+] Enabled Rawmode")
        else:
            self.rawmode = False
            print("[+] Disabled Rawmode")

    def showHelp(self):
        print(self.help)

    def clearScreen(self):
        os.system("clear")

    def listChannels(self):
        print("[+] Listing channels")
        for counter, channel in enumerate(self.channels):
            print(str(counter+1)+". "+channel+" (muted)" if channel in self.channelsMuted else str(counter+1)+". "+channel)

    def muteChannels(self, channels):
        for channel in channels:
            if channel in self.channels:
                if channel not in self.channelsMuted:
                    self.channelsMuted.append(channel)
                    print("[+] Muted "+channel)
            else:
                print("[-] "+channel+" not a known channel")

    def unmuteChannels(self, channels):
        for channel in channels:
            if channel in self.channels:
                if channel in self.channelsMuted:
                    self.channelsMuted.remove(channel)
                    print("[+] Unmuted "+channel)
            else:
                print("[-] "+channel+" not a known channel")

    def selectChannel(self, channel):
        if channel in self.channels:
            self.channelSelected = channel
        else:
            print("[-] "+str(channel)+" not a known channel")

    def showStatus(self):
        pass

    def listUsers(self, channel):
        if channel[0] in self.channels:
            self.listNames = True
            self.ircCommSend("NAMES "+channelToList)
        else:
            print("[-] "+channel+" not a known channel")

    def connect(self):
        self.client = socket.socket()
        self.client = ssl.wrap_socket(self.client)
        self.client.connect((self.ircServer, self.ircPort))

    def login(self):
        self.ircCommSend("NICK "+self.nickname)
        self.ircCommSend("USER "+self.nickname+" 0 * :"+self.nickname+"Blah")
        self.ircCommSend("NS IDENTIFY "+self.password)
        print("[+] Waiting for identification ...")
        while self.identified == False:
            time.sleep(1)
        print("[+] Identified!")
        for channel in self.channels:
            print("[+] Joining "+channel)
            self.ircCommSend("JOIN "+channel)
        self.getUserInput()

    def ircCommSend(self, message):
        """Sends messages and encodes them to bytes like object for Python3 compatibility"""
        message += "\r\n"
        try:
            self.client.send(message.encode("utf-8"))
        except Exception as e:
            print("Error: "+str(e))

    def ircCommRecv(self):
        """Receives messages and prettifies them"""
        while True:
            try:
                data = self.client.recv(2048)
                data = data.decode()
                if not self.identified:
                    if "You are now identified for" in data:
                        self.identified = True
                isChannel = False
                for channel in self.channels:
                    if "PRIVMSG "+channel in data:
                        isChannel = True

                if isChannel:
                    fromUser = data.split("!")[0]
                    data = data.split("PRIVMSG ")[1]
                    fromUser = fromUser.lstrip(":")
                    fromChannel = data.split()[0]
                    messageContent = data.split(fromChannel+" :")[1]
                    if fromChannel not in self.channelsMuted:
                        if self.promptActive:
                            print("")
                            self.promptActive = False
                        print("["+fromChannel.lstrip("#")+"@"+fromUser+"] "+messageContent.strip("\r\n"))

                elif data.startswith(self.ping):
                        resp = data.strip(self.ping);
                        self.ircCommSend(self.pong + resp)

                elif self.listNames:
                    if " 353 "+self.nickname in data:
                        if self.promptActive:
                            print("")
                            self.promptActive = False
                        print(data.rstrip("\n\r"))
                        self.listNames = False

                else:
                    if self.rawmode:
                        if self.promptActive:
                            print("")
                            self.promptActive = False
                        print(data.rstrip("\n\r"))
            except KeyboardInterrupt:
                pass

            time.sleep(0.2)

    def getUserInput(self):
        while True:
            try:
                message = input("["+self.nickname+"@"+self.channelSelected.lstrip("#")+"] ")
                self.promptActive = True
                if message.startswith("!bro "):
                    message = message.split()
                    command = message[1]
                    del message[0:2]
                    self.bro(command, message)
                else:
                    if self.channelSelected != "":
                        self.ircCommSend("PRIVMSG "+self.channelSelected+" :"+message)
                    else:
                        print("You must select a channel first. Use !bro select <channel>")
            except KeyboardInterrupt:
                self.client.close()
                sys.exit("[+] Closing connection!")


ircClient = BroIRC()
ircClient.init()
ircClient.login()
