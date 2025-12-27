#!/usr/bin/env python3
import socket
from PIL import Image
import random
import threading

IMAGES = ["arch-linux-logo-hexagon.png", "eyepain.png", "segelflieger.png", "segelfliegen.png"]
HOST = "151.219.13.203"
PORT = 1234
IMAGEPATH = IMAGES[3]
THREADS = 10
OFFSET_X = 400
OFFSET_Y = 600
RANDOM = False

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

def image_to_shuffled(imagepath):
    pixels = image_to_pixels(imagepath)
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
        if RANDOM:
            instructions.append(f"PX {int(x) + offset_x} {int(y) + offset_y} {random.randint(0,255):02X}{random.randint(0,255):02X}{random.randint(0,255):02X}\n")
        else:
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

pixelsets = split_to_sets(image_to_shuffled(IMAGEPATH), THREADS) 

threads = []

for pxset in pixelsets:
    threads.append(threading.Thread(target=thread_main, args=(HOST, PORT, pxset)))

for thread in threads:
    thread.start()
