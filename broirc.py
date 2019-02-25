import socket
import ssl
import threading
import time
import os
import sys

class BroIRC():
    def __init__(self):
        self.ircServer = "chat.freenode.net"
        self.ircPort = 6697
        self.channels = ["#python"]
        self.hiddenChannels = []
        self.nickname = ""
        self.password = ""
        self.ping = "PING "
        self.pong = "PONG "
        self.identified = False
        self.listNames = False
        self.selectedChannel = ""
        self.promptActive = False
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

    def bro(self, command):
        if command == "!bro rawmode on":
            print("[+] Enabling Raw Mode")
            self.rawmode = True

        elif command == "!bro rawmode off":
            print("[+] Disabling Raw Mode")
            self.rawmode = False

        elif command == "!bro help":
            print(self.help)

        elif command == "!bro clear":
            os.system("clear")

        elif command == "!bro list channels":
            print("[+] Listing channels")
            counter = 0
            for channel in self.channels:
                counter += 1
                if channel in self.hiddenChannels:
                    print(str(counter)+". "+channel+" (hidden)")
                else:
                    print(str(counter)+". "+channel)

        elif command.startswith("!bro mute "):
            try:
                channelToHide = command.split("!bro mute ")[1]
                if channelToHide in self.channels:
                    if channelToHide not in self.hiddenChannels:
                        self.hiddenChannels.append(channelToHide)
                        print("[+] Messages from "+channelToHide+" are now hidden")
                else:
                    print("[-] Channel not recognized")
            except Exception as e:
                print("Error: "+str(e))

        elif command.startswith("!bro unmute "):
            try:
                channelToUnhide = command.split("!bro unmute ")[1]
                if channelToUnhide in self.channels:
                    if channelToUnhide in self.hiddenChannels:
                        self.hiddenChannels.remove(channelToUnhide)
                        print("[+] Messages from "+channelToHide+" are now shown")
                else:
                    print("[-] Channel not recognized")
            except Exception as e:
                print("Error: "+str(e))

        elif command.startswith("!bro select "):
            try:
                channelToSelect = command.split("!bro select ")[1]
                if channelToSelect in self.channels:
                    self.selectedChannel = channelToSelect
                else:
                    print("[-] Channel not recognized")
            except Exception as e:
                print("Error: "+str(e))

        elif command == ("!bro status"):
            print("[+] Showing status")
            print("- Selected channel: "+self.selectedChannel)

        elif command.startswith("!bro list users "):
            try:
                channelToList = command.split("!bro list users ")[1]
                if channelToList in self.channels:
                    self.listNames = True
                    self.ircCommSend("NAMES "+channelToList)
                else:
                    print("[-] Channel not recognized")
            except Exception as e:
                print("Error: "+str(e))

        elif command == "!bro list users":
            if self.selectedChannel:
                self.listNames = True
                self.ircCommSend("NAMES "+self.selectedChannel)

        elif command.startswith("!bro join "):
            channelToJoin = command.split("!bro join ")[1]
            if channelToJoin not in self.channels:
                if channelToJoin.startswith("#"):
                    self.ircCommSend("JOIN "+channelToJoin)
                    self.channels.append(channelToJoin)
            else:
                print("[-] Channel seems to be joined already. Be aware that BroIRC doesn't verify if a channel join succeeds. You can verify channel joins by enabling raw mode")

        elif command.startswith("!bro leave "):
            channelToLeave = command.split("!bro leave ")[1]
            if channelToLeave in self.channels:
                self.ircCommSend("LEAVE "+channelToLeave)
                self.channels.remove(channelToLeave)
            else:
                print("[-] Can't leave a channel, that is not joined")
        else:
            print("[-] Command not recognized")

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
                    if fromChannel not in self.hiddenChannels:
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
                message = input("["+self.nickname+"@"+self.selectedChannel.lstrip("#")+"] ")
                self.promptActive = True
                if message.startswith("!bro"):
                    self.bro(message)
                else:
                    if self.selectedChannel != "":
                        self.ircCommSend("PRIVMSG "+self.selectedChannel+" :"+message)
                    else:
                        print("You must select a channel first. Use !bro select <channel>")
            except KeyboardInterrupt:
                self.client.close()
                sys.exit("[+] Closing connection!")


ircClient = BroIRC()
ircClient.init()
ircClient.login()
