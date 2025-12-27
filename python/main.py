#!/usr/bin/env python3
import socket
import random
import threading
import struct
import version_1_pb2 as pb

CM_HOST = "151.219.13.224"
CM_PORT = 12345
THREADS = 10
OFFSET_X = 00
OFFSET_Y = 00

def recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)

def read_msg(socket):
    raw_len = recv_exact(socket, 2)
    if not raw_len:
        return None
    
    msg_len = struct.unpack('>H', raw_len)[0]

    data = recv_exact(socket, msg_len)
    if not data:
        return None

    msg = pb.Envelope()
    try:
        msg.ParseFromString(data)
        return msg
    except Exception:
        return None

def get_server(socket):
    msg = read_msg(socket)
    connect_to = msg.connect_to
    host = connect_to.host
    port = connect_to.port
    return host, port

def get_pixels(socket):
    pixels = []
    while True:
        msg = read_msg(socket)
        if msg is None:
            break
        add_pixel = msg.add_pixel
        x = add_pixel.x_cord
        y = add_pixel.y_cord
        cords = (x, y)
        color = add_pixel.color
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        col = (r, g, b)
        pixels.append((cords, col))
    return pixels

def image_to_pixels(imagepath):
    img = Image.open(imagepath)
    img = img.convert("RGBA")
    imgalpha = img.getchannel("A")
    pixels = []
    for y in range(1, img.height):
        for x in range(1, img.width):
            if imgalpha.getpixel((x,y)) == 255:
                pixels.append(((x,y), img.getpixel((x, y))))
        
    return pixels

def image_to_shuffled(socket):
    pixels = get_pixels(socket)
    random.shuffle(pixels)
    return pixels


def split_to_sets(pixels, threads):
    pixelsets = []
    for x in range(0, threads):
        pixelsets.append(pixels[x::max(threads, 1)])
    return pixelsets

def pixels_to_instructions(pixels, offset_x, offset_y):
    instructions = []

    for pix in pixels:
        x = pix[0][0]
        y = pix[0][1]
        r = pix[1][0]
        g = pix[1][1]
        b = pix[1][2]
        instructions.append(f"PX {int(x) + offset_x} {int(y) + offset_y} {r:02X}{g:02X}{b:02X}\n")

    return "".join(instructions)

def looped_send(host, port, instructions):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            while True:
                s.sendall(instructions.encode("utf-8"))

def thread_main(host, port, pixels):
    instructions = pixels_to_instructions(pixels, OFFSET_X, OFFSET_Y)
    looped_send(host, port, instructions)


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CM_HOST, CM_PORT))
        host, port = get_server(s)
    
        pixelsets = split_to_sets(image_to_shuffled(s), THREADS) 

    threads = []

    for pxset in pixelsets:
        threads.append(threading.Thread(target=thread_main, args=(host, port, pxset)))

    for thread in threads:
        thread.start()
