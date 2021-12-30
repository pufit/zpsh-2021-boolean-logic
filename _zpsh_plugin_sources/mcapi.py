# coding=utf-8
from __future__ import absolute_import, division, unicode_literals, print_function

import jencodings  # noqa
from org.bukkit import Location, Material
from org.bukkit.block import BlockFace

from com.sk89q.worldedit import BlockVector


def convert_to_bv(location):
    return BlockVector(location.x, location.y, location.z)


def set_block(block_type, location, data=None):
    block = location.getBlock()

    block.setType(block_type)
    if data:
        block_state = block.getState()
        block_state.setData(data)
        block_state.update()


def place_door(location, data=None):
    bottom = location.getBlock()
    top = bottom.getRelative(BlockFace.UP)

    bottom.setType(Material.IRON_DOOR)
    top.setType(Material.IRON_DOOR)

    bottom.setData(0)
    top.setData(0x8)


def fill(block_type, x, y, data=None):
    x_size = int(abs(x.x - y.x)) + 1
    y_size = int(abs(x.y - y.y)) + 1
    z_size = int(abs(x.z - y.z)) + 1

    for i in range(x_size):
        for j in range(y_size):
            for k in range(z_size):
                set_block(block_type, Location(x.world, x.x + i, x.y + j, x.z + k), data)
