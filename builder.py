from litemapy import Schematic, Region, BlockState

MATERIALS = {
    "木頭": ("minecraft:oak_planks", "minecraft:oak_log", "minecraft:oak_slab"),
    "石頭": ("minecraft:stone_bricks", "minecraft:stone", "minecraft:stone_brick_slab"),
    "深板岩": ("minecraft:deepslate_bricks", "minecraft:deepslate", "minecraft:deepslate_brick_slab"),
    "沙岩": ("minecraft:sandstone", "minecraft:cut_sandstone", "minecraft:sandstone_slab"),
    "橡木": ("minecraft:oak_planks", "minecraft:oak_log", "minecraft:oak_slab"),
    "雲杉": ("minecraft:spruce_planks", "minecraft:spruce_log", "minecraft:spruce_slab"),
    "木磚": ("minecraft:oak_planks", "minecraft:oak_log", "minecraft:oak_slab"),
}

def generate_house(style="木頭", width=10, length=10, height=6, name="我的房子", towers=False):
    wall_id, pillar_id, slab_id = MATERIALS.get(style, MATERIALS["木頭"])
    wall   = BlockState(wall_id)
    pillar = BlockState(pillar_id)
    slab   = BlockState(slab_id, type="bottom")
    glass  = BlockState("minecraft:glass")

    w = max(6, min(int(width), 20))
    h = max(4, min(int(height), 10))
    l = max(6, min(int(length), 20))

    # 如果有角塔，擴大空間
    tw = w + 4 if towers else w
    tl = l + 4 if towers else l
    total_h = h + 3 if towers else h

    reg = Region(0, 0, 0, tw, total_h, tl)
    ox = 2 if towers else 0
    oz = 2 if towers else 0

    # 地板
    for x in range(tw):
        for z in range(tl):
            reg[x, 0, z] = wall

    # 主體四面牆
    for y in range(1, h - 1):
        for x in range(ox, ox + w):
            reg[x, y, oz]         = wall
            reg[x, y, oz + l - 1] = wall
        for z in range(oz, oz + l):
            reg[ox, y, z]         = wall
            reg[ox + w - 1, y, z] = wall

    # 四角原木
    for y in range(1, h - 1):
        reg[ox, y, oz]                 = pillar
        reg[ox + w - 1, y, oz]         = pillar
        reg[ox, y, oz + l - 1]         = pillar
        reg[ox + w - 1, y, oz + l - 1] = pillar

    # 玻璃窗
    mid_x = ox + w // 2
    mid_z = oz + l // 2
    for y in range(2, h - 2):
        reg[mid_x - 1, y, oz]         = glass
        reg[mid_x, y, oz]             = glass
        reg[mid_x - 1, y, oz + l - 1] = glass
        reg[mid_x, y, oz + l - 1]     = glass
        reg[ox, y, mid_z - 1]         = glass
        reg[ox, y, mid_z]             = glass
        reg[ox + w - 1, y, mid_z - 1] = glass
        reg[ox + w - 1, y, mid_z]     = glass

    # 屋頂
    for x in range(ox, ox + w):
        for z in range(oz, oz + l):
            reg[x, h - 1, z] = slab

    # 角塔
    if towers:
        tower_positions = [(0, 0), (0, tl - 3), (tw - 3, 0), (tw - 3, tl - 3)]
        for tx, tz in tower_positions:
            for y in range(1, total_h - 1):
                for dx in range(3):
                    for dz in range(3):
                        if dx == 0 or dx == 2 or dz == 0 or dz == 2:
                            reg[tx + dx, y, tz + dz] = wall
                reg[tx, y, tz]         = pillar
                reg[tx + 2, y, tz]     = pillar
                reg[tx, y, tz + 2]     = pillar
                reg[tx + 2, y, tz + 2] = pillar
            for dx in range(3):
                for dz in range(3):
                    reg[tx + dx, total_h - 1, tz + dz] = slab

    schem = Schematic(name=name, author="MC Builder AI", description=f"{style}風格 {w}x{l}")
    schem.regions["Building"] = reg
    return schem
