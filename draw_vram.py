import matplotlib.pyplot as plt
import numpy as np
import os
import struct
from collections import namedtuple

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("area", type=str)
parser.add_argument("section", type=str)
args = parser.parse_args()

area = args.area
section = args.section

# %%
# area = "SYS"
# section = "01"

ldar_version = "LD"

if section is None:
    ldar_dir = f"{ldar_version}{area}/base/"
else:
    ldar_dir = f"{ldar_version}{area}/entry_{section}/"
ldar_file = ldar_dir + f"{ldar_version}{area}.VRAM"
clut_filename = sorted(os.listdir(ldar_dir + "SHARDS/"))[-1]
clut_file = ldar_dir + "SHARDS/" + clut_filename
# spr_file = ldar_dir + "D005.GAM-5.32FF.SPR"
# spr_file = ldar_dir + "../base/A008.GAM-6.39FF.SPR"

if section is None:
    export_folder = f"imgs_{area}_base/"
else:
    export_folder = f"imgs_{area}_{section}/"

try:
    os.mkdir(export_folder)
except FileExistsError:
    pass

# %%
with open(ldar_file, "rb") as file:
    array = np.array(list(file.read()))
    array_clut = array.reshape(-1, 2)
    array_clut = array_clut[..., 1] * 256 + array_clut[..., 0]
    array_clut = array_clut.reshape(512, -1)
    array_clut = np.stack([(array_clut & 0x001F),
                           ((array_clut & 0x03E0) >> 5),
                           ((array_clut & 0x7C00) >> 10)], axis=-1).astype("uint8") * 8
    array = np.stack([array & 0x0F, (array & 0xF0) >> 4], axis=-1).reshape(512, -1)

with open(clut_file, "rb") as file:
    clut = np.array(list(file.read())).reshape(-1, 2)
    clut = clut[..., 1] * 256 + clut[..., 0]
    clut_rgba = np.stack([(clut & 0x001F),
                          ((clut & 0x03E0) >> 5),
                          ((clut & 0x7C00) >> 10)], axis=-1).astype("uint8") * 8
    # clut_rgba = np.concatenate([clut_rgba, [[255]] * len(clut_rgba)], axis=-1)
    clut_rgba = clut_rgba.reshape(-1, 16, 3)
    # clut_rgba[:, 0, 3] = 0

def getClutCoords(num):
    return int((bin(num)[2:].zfill(16))[10:], 2) << 4, int((bin(num)[2:].zfill(16))[1:10], 2)

def getClutAddress(num):
    x, y = getClutCoords(num)
    return x * 2 + y * 0x800

def getClutOffset(num):
    x, y = getClutCoords(num)
    x = x // 16 - 8
    y = y - 480
    return y * 16 + x

SpriteInfo = namedtuple("SpriteInfo", "sX, sY, clut, u0, u1, pg, u2, u3, ww, hh, u4, u5, pX, pY")

# %%
# with open(spr_file, "rb") as file:
#     spr_bytes = file.read()
#     spr = np.array(list(spr_bytes))
#     spr_array = spr.reshape(-1, 2)
#     spr_array = spr_array[..., 1] * 256 + spr_array[..., 0]
#     spr_array = spr_array.reshape(-1, 2)
#     total = spr_array[0, 1]
#     num_sprite_chunks = (len(spr_bytes) - total) // 16
#     spr_array = spr_array[:total // 4]
#     spr_array[:, 1] = (spr_array[:, 1] - total) // 16
#     spr_info = [SpriteInfo(*struct.unpack("<BBHBBHBBBBBBbb",
#                                           spr_bytes[total + i * 16:total + (i + 1) * 16]))
#                 for i in range(num_sprite_chunks)]
#
#     spr_info = [sprite._replace(clut=getClutOffset(sprite.clut)) for sprite in spr_info]

# %%
step_size = 16
for i in range(clut.shape[0] // step_size):
    if i % 16 in []:
        continue

    image = clut_rgba[i][array]

    if (image == 0).all():
        continue

    plt.imsave(export_folder + f"out_{i:03x}.png", image)

    if i >= 10:
        break

exit()

# %%
clut_rgba_export = clut_rgba.reshape(-1, 256, 3)
plt.imsave(export_folder + "clut.png", clut_rgba_export)

# %%
image = np.zeros(array.shape + (3,), dtype="uint8")
x_offset = 1
y_offset = 0

i = 0
for sprite in spr_info:
    sX = sprite.sX + (sprite.pg + x_offset) * 256
    sY = sprite.sY + (sprite.pg + y_offset) * 256
    im_slice = slice(sY, sY + sprite.hh), slice(sX, sX + sprite.ww)
    # image[im_slice] = array_clut[sprite.clut[1], sprite.clut[0]:sprite.clut[0] + 16][array[im_slice]]
    patch = clut_rgba[sprite.clut][array[im_slice]]
    # plt.figure()
    # plt.imshow(patch)
    # plt.show()
    image[im_slice] = patch
    plt.imsave(f"temp_{i:03}.png", image)
    i += 1
    if sprite.pg != 0:
        break

# %%
x_offset = 1
y_offset = 0

for i, (n, offset) in enumerate(spr_array):
    sprites = [spr_info[offset + i] for i in range(n)]
    min_pX, min_pY = np.min([[sprite.pX, sprite.pY] for sprite in sprites], axis=0)
    max_x, max_y = np.max([[sprite.pX + sprite.ww, sprite.pY + sprite.hh] for sprite in sprites], axis=0)
    max_x, max_y = max_x - min_pX, max_y - min_pY
    im_sprite = np.zeros((max_y, max_x, 3), dtype="uint8")
    for sprite in reversed(sprites):
        # import pdb; pdb.set_trace()
        # if sprite.pg != 0:
        #     break
        sX = (sprite.sX + (sprite.pg + x_offset) * 256) % 4096
        sY = (sprite.sY + (sprite.pg // 8 + y_offset) * 256) % 512
        im_slice = slice(sY, sY + sprite.hh), slice(sX, sX + sprite.ww)
        print(i, im_slice)
        patch = clut_rgba[sprite.clut][array[im_slice]]
        spr_slice = (slice(sprite.pY - min_pY, sprite.pY - min_pY + sprite.hh),
                     slice(sprite.pX - min_pX, sprite.pX - min_pX + sprite.ww))
        patch[~patch.any(axis=-1)] = im_sprite[spr_slice][~patch.any(axis=-1)]
        im_sprite[spr_slice] = patch
    else:
        # plt.figure()
        # plt.imshow(im_sprite)
        plt.imsave(f"sprites/spr_{i:03}.png", im_sprite)
        # plt.show()

    continue

# %%
pg_0_sprites = [sprite for sprite in spr_info if sprite.pg == 0]

# %%
us = np.array([[[sprite.sX, sprite.u0, sprite.u2, sprite.u4],
                [sprite.sY, sprite.u1, sprite.u3, sprite.u5]] for sprite in spr_info])
xy = np.array([[sprite.sX, sprite.u2, sprite.sY, sprite.u3] for sprite in spr_info])
dxdy = np.array([[sprite.sX - sprite.u0, sprite.sY - sprite.u1, sprite.pg] for sprite in spr_info])
pgs = np.array([[sprite.pg, sprite.u3] for sprite in spr_info])
