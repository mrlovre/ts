#cython: language_level=3

import struct

def ungam(infile, outfile):
    with open(infile, "rb") as rom, open(outfile, "wb+") as out:
        # get romsize
        rom.seek(0, 2)
        rom_filesize = rom.tell()
        rom.seek(0)

        # get 8 byte header containing GAM and out_filesize
        head = struct.unpack("<3sxI", rom.read(8))
        gam = head[0]
        out_filesize = head[1]

        # verify it's a GAM
        # print("gam verify:", gamcheck(gam))
        # print("file size: 0x{:02X}".format(out_filesize))

        # get bitmask, cycle through, break when all written
        while True:
            b = bitmask(rom.read(2))
            if cycle(rom, out, rom_filesize, out_filesize, b):
                break

        out.write(bytes(pad_fix(out, out_filesize)))

def gam(infile, outfile):
    with open(infile, "rb") as f, open(outfile, "wb") as g:
        file = f.read()
        size = len(file)
        g.write(b"GAM\0")
        g.write(struct.pack(r"<I", size))

        read = 0
        bitmask = []
        while read < size:
            if len(bitmask) == 0:
                bitmask_pos = g.tell()
                g.write(b"\0\0")

            i = max(0, read - 0xff)
            best_pos, best_length = find(file, i, read, size)

            if best_pos != -1:
                copy = struct.pack(r"<BB", read - best_pos, best_length)
                # print("C:", read, copy)
                g.write(copy)
                read += best_length
                bitmask.append(True)
            else:
                write = file[read:read + 1]
                # print("W:", read, write)
                g.write(write)
                read += 1
                bitmask.append(False)

            if len(bitmask) == 16 or read >= size:
                g.seek(bitmask_pos, 0)
                b = 0
                while bitmask:
                    b *= 2
                    b += bitmask.pop()
                # print("B:", b, struct.pack(r"<H", b))
                g.write(struct.pack(r"<H", b))
                g.seek(0, 2)
                bitmask = []

cdef find(unsigned char file[], int i, int read, int size):
    cdef int pos = -1
    cdef int best_pos = -1
    cdef unsigned char length = 0
    cdef unsigned char best_length = 1

    while i < read:
        if i + best_length >= read:
            break

        if file[i] == file[read]:
            length = 1
            pos = i

            while i + length < read and read + length < size and file[i + length] == file[read + length]:
                length += 1

            if length > best_length:
                best_length = length
                best_pos = pos

            i += length
        else:
            i += 1

    return best_pos, best_length

def gamcheck(gam):
    if gam.decode("utf-8") != "GAM":
        return False
    return True

def bitmask(bytes_in):
    mask = format(int.from_bytes(bytes_in, byteorder='little'), '016b')
    # print()
    # print("bitmask:", mask[::-1])
    inlist = list(mask)
    return list(map(lambda x: bool(int(x)), inlist))

def cycle(rom, out, rom_filesize, out_filesize, list_in):
    for i in range(0, len(list_in)):
        if list_in.pop():
            lz = struct.unpack("<BB", rom.read(2))
            # print("  LZ at {:02X} = {:02X},{:02X}".format(rom.tell() - 2, lz[0], lz[1]))
            out.seek(-lz[0], 1)
            # print("  now at {:X} and gonna read {:X}".format(out.tell(), lz[1]))
            buf = out.read(lz[1])
            p_buf = str.join(" ", [f"{int(b):02x}" for b in buf])
            # print(f"copying: {p_buf}")
            out.seek(0, 2)
            out.write(buf)
        else:
            buf = rom.read(1)
            p_buf = str.join(" ", [f"{int(b):02x}" for b in buf])
            # print(f"writing: {p_buf}")
            out.write(buf)

        if out.tell() == out_filesize or rom.tell() == rom_filesize:
            # print("HALT")
            return True
        else:
            # print("only written {:02X} / {:02X}. ROM at {:02X}".format(out.tell(), out_filesize, rom.tell()))
            return False

def pad_fix(out, out_filesize, miss):
    miss = out_filesize - out.tell()
    # print("{:02X} bytes missing.".format(miss))
    if miss < 0:
        # print("Negative pad amount. Erasing {:02X} bytes".format(miss))
        out.seek(out_filesize)
        out.truncate()
        miss = 0
    return miss
