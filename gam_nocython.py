import struct

from argparse import ArgumentParser

arg_parser = ArgumentParser()
arg_parser.add_argument("infile", help="input file name", type=str)
arg_parser.add_argument("outfile", help="output file name", type=str)
args = arg_parser.parse_args()

if __name__ == '__main__':
    infile = args.infile
    outfile = args.outfile
    # infile = "/windows/PSX/Ore! Tomba (Japan)/iso/area00/a000.ungam"
    # outfile = "/windows/PSX/Ore! Tomba (Japan)/iso/test.gam"
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
            pos = None
            best_pos = None
            length = 0
            best_length = 1

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

            if best_pos is not None:
                copy = struct.pack(r"<BB", read - best_pos, best_length)
                print("C:", read, copy)
                g.write(copy)
                read += best_length
                bitmask.append(True)
            else:
                write = file[read:read + 1]
                print("W:", read, write)
                g.write(write)
                read += 1
                bitmask.append(False)

            if len(bitmask) == 16 or read >= size:
                g.seek(bitmask_pos, 0)
                b = 0
                while bitmask:
                    b *= 2
                    b += bitmask.pop()
                print("B:", b, struct.pack(r"<H", b))
                g.write(struct.pack(r"<H", b))
                g.seek(0, 2)
                bitmask = []
