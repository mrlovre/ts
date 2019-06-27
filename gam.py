from argparse import ArgumentParser
from gam_tools import gam

arg_parser = ArgumentParser()
arg_parser.add_argument("infile", help="input file name", type=str)
arg_parser.add_argument("outfile", help="output file name", type=str)
args = arg_parser.parse_args()

infile = args.infile
outfile = args.outfile
# infile = "/windows/PSX/Ore! Tomba (Japan)/iso/area00/a000.ungam"
# outfile = "/windows/PSX/Ore! Tomba (Japan)/iso/test.gam"
gam(infile, outfile)
