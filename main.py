import logging
import socket
import time
import os
from threading import Thread

# =====================================================================
# SİMÜLE EDİLMİŞ KLASÖR YAPILARI (KLASÖRLERDEN KURTULMAK İÇİN TEK YERDE)
# =====================================================================

class Device:
    """Eski Logic.Device klasörünün simülasyonu"""
    def __init__(self, client):
        self.client = client

class Players:
    """Eski Logic.Player klasörünün simülasyonu"""
    def __init__(self, device):
        self.device = device
        self.low_id = int(time.time()) & 0xffffffff  # Rastgele benzersiz ID
        self.ClientDict = {}

class Utils:
    """Eski Utility.Utils klasörünün simülasyonu"""
    connected_clients = {'ClientsCount': 0}

class LobbyInfoMessage:
    """Eski Packets.Messages.Server.Home... klasörünün simülasyonu"""
    def __init__(self, client, player, client_count):
        self.client = client
        self.player = player
        self.client_count = client_count

    def send(self):
        # v20 Lobi Paket Yapısı (Giriş Başarılı Sinyali)
        # Normalde klasörden gelen paket baytlarını burada doğrudan simüle ediyoruz
        packet_id = 24101  # LoginOk / LobbyInfo paket ID'si
        packet_data = b'\x00\x00\x00\x00' # Boş veri (Geliştirilebilir)
        header = packet_id.to_bytes(2, 'big') + len(packet_data).to_bytes(3, 'big') + b'\x00\x00'
        try:
            self.client.send(header + packet_data)
        except:
            pass

# Tetiklenebilir hazır paketlerin listesi (Eski AvailablePackets)
AvailablePackets = {}

# =====================================================================
# ANA SUNUCU KODLARI
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
        # Render (Linux) üzerinde port hatası almamak için soketi yeniden kullanılabilir yapıyoruz
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port = port
        self.ip = ip

    def start(self):
        self.server.bind((self.ip, self.port))
        _(f'Server started! Ip: {self.ip}, Port: {self.port}')
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
                print("Receive Error!")
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
                    
                    # Giriş yapan oyuncuya doğrudan lobi bilgisini basıyoruz
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
                    print(f"[INFO] Ip: {self.address[0]} disconnected!")
                    self.client.close()
                    break
        except ConnectionAbortedError:
            print(f"[INFO] Ip: {self.address[0]} disconnected!")
            self.client.close()
        except ConnectionResetError:
            print(f"[INFO] Ip: {self.address[0]} disconnected!")
            self.client.close()
        except TimeoutError:
            print(f"[INFO] Ip: {self.address[0]} disconnected!")
            self.client.close()

if __name__ == '__main__':
    # Render üzerinde sunucunun ayağa kalkması için '0.0.0.0' olarak kalmalı
    server = Server('0.0.0.0', 9339)
    server.start()