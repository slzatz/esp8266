'''
Based on Paul Sokolovsky's work on micropython mqtt client
Note MicroPython socket module supports file interface directly (read)
'''

import socket
import ustruct as struct

class MQTTClient:

    def __init__(self, client_id, server, port=1883):
        self.client_id = client_id.encode('utf-8')
        self.sock = socket.socket()
        print("server =",server)
        print(server,port)
        self.addr = socket.getaddrinfo(server, port)[0][-1]
        self.pid = 0

    # the staticmethod is to create a bytes object that is used in a callback
    @staticmethod
    def mtpPublish(topic, msg):
        mtopic = bytes([len(topic) >> 8, len(topic) & 255]) + topic.encode('utf-8')
        return  bytes([0b00110001, len(mtopic) + len(msg)]) + mtopic + msg.encode('utf-8')

    def send_str(self, s):
        # H = use two bytes to represent number
        self.sock.send(struct.pack("!H", len(s)))
        self.sock.send(s)

    def connect(self):
        print("connect")
        self.sock.connect(self.addr)
        msg = bytearray(b"\x10\0\0\x04MQTT\x04\x02\0\0")
        msg[1] = 10 + 2 + len(self.client_id)
        self.sock.send(msg)
        self.send_str(self.client_id)
        resp = self.sock.recv(4)
        assert resp == b"\x20\x02\0\0", resp
        print(resp)

    def disconnect(self):
        self.sock.send(b"\xe0\0")
        self.sock.close()

    def publish(self, topic, msg, qos=0, retain=False):
        assert qos == 0
        pkt = bytearray(b"\x30\0")
        pkt[0] |= qos << 1 | retain
        pkt[1] = 2 + len(topic) + len(msg)
        self.sock.send(pkt)
        self.send_str(topic.encode('utf-8'))
        self.sock.send(msg.encode('utf-8'))

    def subscribe(self, topic):
        print("subscribe")
        pkt = bytearray(b"\x82\0\0\0")
        self.pid += 1
        # B=1 byte; H = 2 bytes,!=network or big endian and offset is 1
        struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
        self.sock.send(pkt)
        self.send_str(topic.encode('utf-8'))
        self.sock.send(b"\0")
        resp = self.sock.recv(5)
        print(resp)
        assert resp[0] == 0x90
        assert resp[2] == pkt[2] and resp[3] == pkt[3]
        assert resp[4] == 0

    def check_msg(self):
        self.sock.setblocking(False)
        res = self.sock.read(1)
        if res is None:
            return None

        #if res[0] >> 4 !=3: #more general but not handling QoS > 0 right now
        if res[0] in (48,49):
            self.sock.setblocking(True)
            sz = self.sock.recv(1)[0]
            if sz > 127:
                sz1 = self.sock.recv(1)[0]
                #sz = sz1*128 + sz - 128
                sz+= (sz1<<7) - 128

            z = self.sock.recv(sz)
            # topic length is first two bytes of variable header
            topic_len = z[:2]
            topic_len = (topic_len[0] << 8) | topic_len[1]
            topic = z[2:topic_len+2]
            msg = z[topic_len+2:]
            return (topic, msg)

        elif res[0]>>4==13:
            self.sock.setblocking(True)
            s = self.sock.recv(1) # second byte of pingresp should be 0
            return 13

        else:
            return res

    def ping(self):
        pkt = bytearray([0b11000000,0x0])
        self.sock.send(pkt)

