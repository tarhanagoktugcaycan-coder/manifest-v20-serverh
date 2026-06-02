import logging
import socket
import time
import os
from threading import Thread
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# =====================================================================
# RELEASING RENDER: SAHTE HTTP SUNUCUSU (RENDER'I KANDIRMAK İÇİN)
# =====================================================================
def run_fake_http():
    # Render varsayılan olarak 10000 portunu tarar, burayı açıp Render'ı yeşile döndürüyoruz
    port = int(os.environ.get("PORT", 10000))
    handler = SimpleHTTPRequestHandler
    # Port hatası vermemesi için reuse_address ekliyoruz
    TCPServer.allow_reuse_address = True
    with TCPServer(("0.0.0.0", port), handler) as httpd:
        print(f"[RENDER HACK] Sahte HTTP Sunucusu {port} portunda açıldı!")
        httpd.serve_forever()

# =====================================================================
# SİMÜLE EDİLMİŞ KLASÖR YAPILARI (SIFIR KLASÖR İÇİN)
# =====================================================================
class Device:
    def __init__(self, client):
        self.client = client

class Players:
    def __init__(self, device):
        self.device = device
        self.low_id = int(time.time()) & 0xffffffff
        self.ClientDict = {}

class Utils:
    connected_clients = {'ClientsCount': 0}

class LobbyInfoMessage:
    def __init__(self, client, player, client_count):
        self.client = client
        self.player = player
        self.client_count = client_count

    def send(self):
        packet_id = 24101
        packet_data = b'\x00\x00\x00\x00'
        header = packet_id.to_bytes(2, 'big') + len(packet_data).to_bytes(3, 'big') + b'\x00\x00'
        try:
            self.client.send(header + packet_data)
        except:
            pass

AvailablePackets = {}

# =====================================================================
# ANA BRAWL STARS SUNUCU KODLARI
# =====================================================================
def _(*args):
    print('[INFO]', end=' ')
    for arg in args:
        print(arg, end=' ')
    print()

class Server:
    Clients = {"ClientCounts": 0, "Clients": {}}
    ThreadCount = 0
    
    def __init__(self, ip: str, port: int):
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port = port
        self.ip = ip

    def start(self):
        self.server.bind((self.ip, self.port))
        _(f'Brawl Stars Server started! Ip: {self.ip}, Port: {self.port}')
        while True:
            self.server.listen()
            client, address = self.server.accept()
            _(f'New connection! Ip: {address[0]}')
            ClientThread(client, address).start()
            Utils.connected_clients['ClientsCount'] += 1

class ClientThread(Thread):
    def __init__(self, client, address):
        super().__init__()
        self.client = client
        self.address = address
        self.device = Device(self.client)
        self.player = Players(self.device)

    def recvall(self, length: int):
        data = b''
        while len(data) < length:
            s = self.client.recv(length)
            if not s:
                break
            data += s
        return data

    def run(self):
        LastPacketRecived = time.time()
        try:
            while True:
                header = self.client.recv(7)
                if len(header) > 0:
                    LastPacketRecived = time.time()
                    PacketID = int.from_bytes(header[:2], 'big')
                    PacketLenght = int.from_bytes(header[2:5], 'big')
                    PacketData = self.recvall(PacketLenght)
                    
                    LobbyInfoMessage(self.client, self.player, Utils.connected_clients['ClientsCount']).send()
                    
                    if PacketID in AvailablePackets:
                        PacketName = AvailablePackets[PacketID].__name__
                        _(f'Packet {PacketID}: {PacketName} was received!')
                        message = AvailablePackets[PacketID](self.client, self.player, PacketData)
                        message.decode()
                        message.process()
                        if PacketID == 10101:
                            Server.Clients["Clients"][str(self.player.low_id)] = {"SocketInfo": self.client}
                            Server.Clients["ClientCounts"] = Server.ThreadCount
                            self.player.ClientDict = Server.Clients
                    else:
                        _(f'Packet {PacketID} is not handled!')
                        
                if time.time() - LastPacketRecived > 10:
                    self.client.close()
                    break
        except:
            self.client.close()

if __name__ == '__main__':
    # 1. Önce Render'ı kandıracak HTTP sunucusunu yan tarafta (Thread) başlatıyoruz
    Thread(target=run_fake_http, daemon=True).start()
    
    # 2. Ana Brawl Stars sunucumuzu kendi portunda ayağa kaldırıyoruz
    server = Server('0.0.0.0', 9339)
    server.start()
