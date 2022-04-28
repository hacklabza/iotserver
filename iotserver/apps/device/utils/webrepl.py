# Original code from https://github.com/micropython/webrepl/blob/master/webrepl_cli.py

import os
import socket
import struct
import sys

DEBUG = 0
CLIENT_HANKSHAKE_HEADER = b'''\
GET / HTTP/1.1\r
Host: echo.websocket.org\r
Connection: Upgrade\r
Upgrade: websocket\r
Sec-WebSocket-Key: foo\r
\r
'''

# Define to 1 to use builtin 'uwebsocket' module of MicroPython
USE_BUILTIN_UWEBSOCKET = 0

WEBREPL_REQ_S = '<2sBBQLH64s'
WEBREPL_PUT_FILE = 1
WEBREPL_GET_FILE = 2
WEBREPL_GET_VER = 3


def debug_msg(msg):
    if DEBUG:
        print(msg)


def client_handshake(sock):
    client = sock.makefile('rwb', 0)
    client.write(CLIENT_HANKSHAKE_HEADER)
    line = client.readline()
    while 1:
        line = client.readline()
        if line == b'\r\n':
            break


class WebSocket:
    def __init__(self, _socket):
        self.socket = _socket
        self.buffer = b''

    def write(self, data):
        length = len(data)
        if length < 126:
            hdr = struct.pack('>BB', 0x82, length)
        else:
            hdr = struct.pack('>BBH', 0x82, 126, length)
        self.socket.send(hdr)
        self.socket.send(data)

    def recvexactly(self, sz):
        res = b''
        while sz:
            data = self.socket.recv(sz)
            if not data:
                break
            res += data
            sz -= len(data)
        return res

    def read(self, size, text_ok=False):
        if not self.buffer:
            while True:
                hdr = self.recvexactly(2)
                assert len(hdr) == 2
                fl, sz = struct.unpack('>BB', hdr)
                if sz == 126:
                    hdr = self.recvexactly(2)
                    assert len(hdr) == 2
                    (sz,) = struct.unpack('>H', hdr)
                if fl == 0x82:
                    break
                if text_ok and fl == 0x81:
                    break
                debug_msg(
                    'Got unexpected websocket record of type %x, skipping it' % fl
                )
                while sz:
                    skip = self.socket.recv(sz)
                    debug_msg('Skip data: %s' % skip)
                    sz -= len(skip)
            data = self.recvexactly(sz)
            assert len(data) == sz
            self.buffer = data

        d = self.buffer[:size]
        self.buffer = self.buffer[size:]
        assert len(d) == size, len(d)
        return d

    def ioctl(self, req, val):
        assert req == 9 and val == 2


def login(ws, passwd):
    while True:
        c = ws.read(1, text_ok=True)
        if c == b':':
            assert ws.read(1, text_ok=True) == b' '
            break
    ws.write(passwd.encode('utf-8') + b'\r')


def read_resp(ws):
    data = ws.read(4)
    sig, code = struct.unpack('<2sH', data)
    assert sig == b'WB'
    return code


def send_req(ws, op, sz=0, fname=b''):
    rec = struct.pack(WEBREPL_REQ_S, b'WA', op, 0, 0, sz, len(fname), fname)
    debug_msg('%r %d' % (rec, len(rec)))
    ws.write(rec)


def get_ver(ws):
    send_req(ws, WEBREPL_GET_VER)
    d = ws.read(3)
    d = struct.unpack('<BBB', d)
    return d


def put_file(ws, local_file, remote_file):
    sz = os.stat(local_file)[6]
    dest_fname = remote_file.encode('utf-8')
    rec = struct.pack(
        WEBREPL_REQ_S, b'WA', WEBREPL_PUT_FILE, 0, 0, sz, len(dest_fname), dest_fname
    )
    debug_msg('%r %d' % (rec, len(rec)))
    ws.write(rec[:10])
    ws.write(rec[10:])
    assert read_resp(ws) == 0
    cnt = 0
    with open(local_file, 'rb') as f:
        while True:
            sys.stdout.write('Sent %d of %d bytes\r' % (cnt, sz))
            sys.stdout.flush()
            buf = f.read(1024)
            if not buf:
                break
            ws.write(buf)
            cnt += len(buf)
    assert read_resp(ws) == 0


def get_file(ws, local_file, remote_file):
    src_fname = remote_file.encode('utf-8')
    rec = struct.pack(
        WEBREPL_REQ_S, b'WA', WEBREPL_GET_FILE, 0, 0, 0, len(src_fname), src_fname
    )
    debug_msg('%r %d' % (rec, len(rec)))
    ws.write(rec)
    assert read_resp(ws) == 0
    with open(local_file, 'wb') as f:
        cnt = 0
        while True:
            ws.write(b'\0')
            (sz,) = struct.unpack('<H', ws.read(2))
            if sz == 0:
                break
            while sz:
                buf = ws.read(sz)
                if not buf:
                    raise OSError()
                cnt += len(buf)
                f.write(buf)
                sz -= len(buf)
                sys.stdout.write('Received %d bytes\r' % cnt)
                sys.stdout.flush()
    assert read_resp(ws) == 0


def get_websocket(host, port, passwd):
    _socket = socket.socket()

    address_info = socket.getaddrinfo(host, port)
    address = address_info[0][4]

    _socket.connect(address)
    client_handshake(_socket)

    web_socket = WebSocket(_socket)

    login(web_socket, passwd)
    print('Remote WebREPL version:', get_ver(web_socket))

    # Set websocket to send data marked as 'binary'
    web_socket.ioctl(9, 2)

    return _socket, web_socket


def help(rc=0):
    exename = sys.argv[0].rsplit('/', 1)[-1]
    print(
        '%s - Perform remote file operations using MicroPython WebREPL protocol'
        % exename
    )
    print('Arguments:')
    print(
        '  [-p password] <host>:<remote_file> <local_file> - Copy remote file to local file'
    )
    print(
        '  [-p password] <local_file> <host>:<remote_file> - Copy local file to remote file'
    )
    print('Examples:')
    print('  %s script.py 192.168.4.1:/another_name.py' % exename)
    print('  %s script.py 192.168.4.1:/app/' % exename)
    print('  %s -p password 192.168.4.1:/app/script.py .' % exename)
    sys.exit(rc)


def error(msg):
    print(msg)
    sys.exit(1)


def parse_remote(remote):
    host, fname = remote.rsplit(':', 1)
    if fname == '':
        fname = '/'
    port = 8266
    if ':' in host:
        host, port = host.split(':')
        port = int(port)
    return (host, port, fname)


def main():
    if len(sys.argv) not in (3, 5):
        help(1)

    passwd = None
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-p':
            sys.argv.pop(i)
            passwd = sys.argv.pop(i)
            break

    if not passwd:
        import getpass

        passwd = getpass.getpass()

    if ':' in sys.argv[1] and ':' in sys.argv[2]:
        error('Operations on 2 remote files are not supported')
    if ':' not in sys.argv[1] and ':' not in sys.argv[2]:
        error('One remote file is required')

    if ':' in sys.argv[1]:
        op = 'get'
        host, port, src_file = parse_remote(sys.argv[1])
        dst_file = sys.argv[2]
        if os.path.isdir(dst_file):
            basename = src_file.rsplit('/', 1)[-1]
            dst_file += '/' + basename
    else:
        op = 'put'
        host, port, dst_file = parse_remote(sys.argv[2])
        src_file = sys.argv[1]
        if dst_file[-1] == '/':
            basename = src_file.rsplit('/', 1)[-1]
            dst_file += basename

    if True:
        print('op:%s, host:%s, port:%d, passwd:%s.' % (op, host, port, passwd))
        print(src_file, '->', dst_file)

    _socket = socket.socket()

    address_info = socket.getaddrinfo(host, port)
    address = address_info[0][4]

    _socket.connect(address)
    client_handshake(_socket)

    web_socket = WebSocket(_socket)

    login(web_socket, passwd)
    print('Remote WebREPL version:', get_ver(web_socket))

    # Set websocket to send data marked as 'binary'
    web_socket.ioctl(9, 2)

    if op == 'get':
        get_file(web_socket, dst_file, src_file)
    elif op == 'put':
        put_file(web_socket, src_file, dst_file)

    _socket.close()


if __name__ == '__main__':
    main()
