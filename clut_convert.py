from argparse import ArgumentParser
import struct
import numpy as np

arg_parser = ArgumentParser()
arg_parser.add_argument("infile", help="input file name", type=str)
arg_parser.add_argument("outfile", help="output file name", type=str)
args = arg_parser.parse_args()

with open(args.infile, "rb") as f, open(args.outfile, "wb") as g:
    clut = np.array(list(f.read())).reshape(-1, 2)
    clut = clut[..., 1] * 256 + clut[..., 0]
    clut_rgba = np.stack([(clut & 0x001F),
                          ((clut & 0x03E0) >> 5),
                          ((clut & 0x7C00) >> 10)], axis=-1).astype("uint8") * 8
    clut_rgba = clut_rgba.reshape(-1, 16, 3)

    clut_rgba = np.minimum(clut_rgba, 255)

    for a in clut_rgba.ravel():
        g.write(struct.pack(r"<B", a))
