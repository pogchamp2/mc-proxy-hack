"""
"Quiet mode" example proxy
Allows a client to turn on "quiet mode" which hides chat messages
This client doesn't handle system messages, and assumes none of them contain chat messages
"""
from __future__ import print_function
import argparse
import socket
import math
from sys import argv
import struct
from twisted.internet import reactor,ssl
from quarry.types.uuid import UUID
from quarry.net.proxy import DownstreamFactory, Bridge
import twisted.internet._sslverify as v
from mcrcon import MCRcon
v.platformTrust = lambda : None
argv.pop(0)
class QuietBridge(Bridge):
    quiet_mode = False
    fly = 0
    hover = 0
    freeze = False
    def packet_upstream_chat_command(self, buff):
        command = buff.unpack_string()

        if command == "quiet":
            self.toggle_quiet_mode()
            buff.discard()

        elif command.split(" ")[0] == "levitate":
            self.send_system("Levitating")
            buff.save()
            if self.fly == 0:
                self.fly = 0.5
            else:
                self.fly = 0
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x, y+self.fly, z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on [all] failed")
            buff.discard()

        elif command.split(" ")[0] == "tpw":
            self.send_system("Teleporting on the [all] axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x+int(command.split(" ")[1]), y+int(command.split(" ")[2]), z+int(command.split(" ")[3]), yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on [all] failed")
            buff.discard()
        elif command.split(" ")[0] == "tpy":
            self.send_system("Teleporting on the Y axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x, y+int(command.split(" ")[1]), z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on Y failed")
            buff.discard()
        elif command.split(" ")[0] == "tpz":
            self.send_system("Teleporting on the Z axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x, y, z+int(command.split(" ")[1]), yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on Z failed")
            buff.discard()
        elif command.split(" ")[0] == "tpx":
            self.send_system("Teleporting on the X axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x+int(command.split(" ")[1]), y, z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on X failed")
            buff.discard()

        else:
            buff.restore()
            self.upstream.send_packet("chat_command", buff.read())

    def packet_upstream_chat_message(self, buff):
        buff.save()
        chat_message = self.read_chat(buff, "upstream")
        self.logger.info(" >> %s" % chat_message)

        if chat_message.startswith(".quiet"):
            self.toggle_quiet_mode()
        
        elif chat_message == ".freeze":
            self.freeze = not self.freeze

        elif self.quiet_mode and not chat_message.startswith("."):
            # Don't let the player send chat messages in quiet mode
            msg = "Can't send messages while in quiet mode, moron."
            self.send_system(msg)

        elif chat_message.split(" ")[0] == ".rcon":
            cmd = chat_message[6:]
            rcon = MCRcon("10.0.0.16","test",12346)
            rcon.connect()
            try:
                self.send_system(str(rcon.command(cmd)))
            except Exception as e:
                self.send_system("Rcon command execution failed")
                self.send_system(str(e))

        elif chat_message.split(" ")[0] == ".levitate":
            buff.save()
            msg = ""
            if self.fly == 0:
                self.fly = 0.125
                msg = ""
            else:
                self.fly = 0
                msg = "Not "
            self.send_system(f"{msg}levitating")
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x, y+self.fly, z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Could not levitate")
            buff.discard()

        elif chat_message.split(" ")[0] == ".float":
            buff.save()
            msg = ""
            if self.fly == 0:
                self.fly = 0.00125
                msg = ""
            else:
                self.fly = 0
                msg = "Not "
            self.send_system(f"{msg}floating")
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x, y+self.fly, z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Could not float")
            buff.discard()
        
        elif chat_message == ".hlp":
            self.send_system("AxelProxy HELP:")
            self.send_system(".rcon <command> - Use RCON to run a command\n(Note: you can't run actual op commands in CHAT)\n(aka: use rcon for op commands)")
            self.send_system(".tp<x,y, or z> <amount> - Teleports you on <x,y, or z> by <amount>")
            self.send_system(".tpw <x> <y> <z> - Teleports you by x, y, and z on x, y, and z respectively")
            self.send_system(".hover - Displays you 1 block above your real position\n(For everyone BUT you)")
            self.send_system(".levitate - Makes you go up 1/8 of a block every packet")
            self.send_system(".hlp - Hey, what's your IQ?")

        elif chat_message.split(" ")[0] == ".hover":
            buff.save()
            msg = ""
            if self.hover == 0:
                self.hover = 1
                msg = ""
            else:
                self.hover = 0
                msg = "Not "
            self.send_system(f"{msg}hovering")
            buff.discard()

        elif chat_message.split(" ")[0] == ".tpw":
            self.send_system("Teleporting on the [all] axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x+int(chat_message.split(" ")[1]), y+int(chat_message.split(" ")[2]), z+int(chat_message.split(" ")[3]), yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on [all] failed")
            buff.discard()
        elif chat_message.split(" ")[0] == ".tpy":
            self.send_system("Teleporting on the Y axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x, y+int(chat_message.split(" ")[1]), z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on Y failed")
            buff.discard()
        elif chat_message.split(" ")[0] == ".tpz":
            self.send_system("Teleporting on the Z axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x, y, z+int(chat_message.split(" ")[1]), yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on Z failed")
            buff.discard()
        elif chat_message.split(" ")[0] == ".tpx":
            self.send_system("Teleporting on the X axis")
            buff.save()
            try:
                x, y, z, ground = self.prev_pos
                yaw, pitch, ground = self.prev_look
                buf = struct.pack('>dddffBBB', x+int(chat_message.split(" ")[1]), y, z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf)
            except:
                self.send_system("Teleport on X failed")
            buff.discard()


        else:
            # Pass to upstream
            buff.restore()
            self.upstream.send_packet("chat_message", buff.read())
            print(f"Sent message: \"{chat_message}\"")

    def toggle_quiet_mode(self):
        # Switch mode
        self.quiet_mode = not self.quiet_mode

        action = self.quiet_mode and "enabled" or "disabled"
        msg = "Quiet mode %s" % action

        self.send_system(msg)

    def packet_upstream_player_position(self, buff):
        if self.freeze == False:
            buff.save()
            x, y, z, ground = struct.unpack('>dddB', buff.read())
            print(f"[*] player_position {x} / {y} / {z} | {ground}")
            self.prev_pos = (x, y, z, ground)
            if self.fly > 0:
                yaw,pitch,_ = self.prev_look
                buf2 = struct.pack('>dddffBBB', x, y+self.fly, z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf2)

            buf = struct.pack('>dddB', x, y+self.hover, z, ground)        
            self.upstream.send_packet('player_position', buf)
        else:
            buff.save()
            x, y, z, ground = struct.unpack('>dddB', buff.read())
            print(f"[*] player_position {x} / {y} / {z} | {ground}\nreal packet: {x} / {y} / {z} | {ground}")
            buf = struct.pack('>dddB', self.prev_pos[0], self.prev_pos[1], self.prev_pos[2], self.prev_pos[3])        
            self.upstream.send_packet('player_position', buf)

    def packet_upstream_player_position_and_look(self, buff):
        if self.freeze == False:
            buff.save()
            x, y, z, yaw, pitch, ground = struct.unpack('>dddffB', buff.read())
            print(f"[*] player_position+player_look {x} / {y} / {z} | {yaw} / {pitch} | {ground}")
            self.prev_pos = (x, y, z, ground)
            self.prev_look = (yaw, pitch, ground)
            if self.fly > 0:
                buf2 = struct.pack('>dddffBBB', x, y+self.fly, z, yaw, pitch, 0, 0, 0)
                self.downstream.send_packet('player_position_and_look', buf2)

            buf = struct.pack('>dddffB', x, y+self.hover, z, yaw, pitch, ground)        
            self.upstream.send_packet('player_position_and_look', buf)
        else:
            buff.save()
            x, y, z, yaw, pitch, ground = struct.unpack('>dddffB', buff.read())
            print(f"[*] player_position+player_look {x} / {y} / {z} | {yaw} / {pitch} | {ground}\nreal packet: {x} / {y} / {z} | {yaw} / {pitch} | {ground}")
            buf = struct.pack('>dddffB', self.prev_pos[0], self.prev_pos[1], self.prev_pos[2], self.prev_look[0], self.prev_look[1], self.prev_pos[3])        
            self.upstream.send_packet('player_position_and_look', buf)

    def packet_upstream_player_look(self, buff):
        if self.freeze == False:
            buff.save()
            yaw, pitch, ground = struct.unpack('>ffB', buff.read())
            print(f"[*] player_look {yaw} / {pitch} | {ground}")
            self.prev_look = (yaw, pitch, ground)
            buf = struct.pack('>ffB', yaw, pitch, ground)
            self.upstream.send_packet('player_look', buf)
        else:
            buff.save()
            yaw, pitch, ground = struct.unpack('>ffB', buff.read())
            print(f"[*] player_look {self.prev_look[0]} / {self.prev_look[1]} | {self.prev_look[2]}\nreal packet: {yaw} / {pitch} | {ground}")
            buf = struct.pack('>ffB', self.prev_look[0], self.prev_look[1], self.prev_look[2])
            self.upstream.send_packet('player_look', buf)

    def packet_downstream_chat_message(self, buff):
        chat_message = self.read_chat(buff, "downstream")
        self.logger.info(" :: %s" % chat_message)

        # All chat messages on 1.19+ are from players and should be ignored in quiet mode
        if self.quiet_mode and self.downstream.protocol_version >= 759:
            return

        # Ignore message that look like chat when in quiet mode
        if chat_message is not None and self.quiet_mode and chat_message.startswith("<"):
            return

        # Pass to downstream
        buff.restore()
        self.downstream.send_packet("chat_message", buff.read())

    def read_chat(self, buff, direction):
        buff.save()
        if direction == "upstream":
            p_text = buff.unpack_string()
            buff.discard()

            return p_text
        elif direction == "downstream":
            # 1.19.1+
            if self.downstream.protocol_version >= 760:
                p_signed_message = buff.unpack_signed_message()
                buff.unpack_varint()  # Filter result
                p_position = buff.unpack_varint()
                p_sender_name = buff.unpack_chat()

                buff.discard()

                if p_position not in (1, 2):  # Ignore system and game info messages
                    # Sender name is sent separately to the message text
                    return ":: <%s> %s" % (
                    p_sender_name, p_signed_message.unsigned_content or p_signed_message.body.message)

                return

            p_text = buff.unpack_chat().to_string()

            # 1.19+
            if self.downstream.protocol_version == 759:
                p_unsigned_text = buff.unpack_optional(lambda: buff.unpack_chat().to_string())
                p_position = buff.unpack_varint()
                buff.unpack_uuid()  # Sender UUID
                p_sender_name = buff.unpack_chat()
                buff.discard()

                if p_position not in (1, 2):  # Ignore system and game info messages
                    # Sender name is sent separately to the message text
                    return "<%s> %s" % (p_sender_name, p_unsigned_text or p_text)

            elif self.downstream.protocol_version >= 47:  # 1.8.x+
                p_position = buff.unpack('B')
                buff.discard()

                if p_position not in (1, 2) and p_text.strip():  # Ignore system and game info messages
                    return p_text

            else:
                return p_text

    def send_system(self, message):
        if self.downstream.protocol_version >= 760:  # 1.19.1+
            self.downstream.send_packet("system_message",
                               self.downstream.buff_type.pack_chat(message),
                               self.downstream.buff_type.pack('?', False))  # Overlay false to put in chat
        elif self.downstream.protocol_version == 759:  # 1.19
            self.downstream.send_packet("system_message",
                               self.downstream.buff_type.pack_chat(message),
                               self.downstream.buff_type.pack_varint(1))  # Type 1 for system chat message
        else:
            self.downstream.send_packet("chat_message",
                               self.downstream.buff_type.pack_chat(message),
                               self.downstream.buff_type.pack('B', 0),
                               self.downstream.buff_type.pack_uuid(UUID(int=0)))


class QuietDownstreamFactory(DownstreamFactory):
    bridge_class = QuietBridge
    motd = "Axel's Proxy Server"


def main(argv):
    # Parse options
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl.CertificateOptions(verify=False)
    # Create factory
    factory = QuietDownstreamFactory()
    factory.connect_host = "10.0.0.16"
    factory.connect_port = 12345

    # Listen
    factory.listen("localhost", 25565)
    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])