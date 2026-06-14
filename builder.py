from litemapy import Schematic, Region, BlockState

MATERIALS = {
    "木頭": ("minecraft:oak_planks", "minecraft:oak_log", "minecraft:oak_slab"),
    "石頭": ("minecraft:stone_bricks", "minecraft:stone", "minecraft:stone_brick_slab"),
    "深板岩": ("minecraft:deepslate_bricks", "minecraft:deepslate", "minecraft:deepslate_brick_slab"),
    "沙岩": ("minecraft:sandstone", "minecraft:cut_sandstone", "minecraft:sandstone_slab"),
}

def generate_house(style="木頭", width=10, length=10, height=6, name="我的房子"):
    wall_id, pillar_id, slab_id = MATERIALS.get(style, MATERIALS["木頭"])
    wall    = BlockState(wall_id)
    pillar  = BlockState(pillar_id)
    slab    = BlockState(slab_id, type="bottom")
    glass   = BlockState("minecraft:glass")

    w, h, l = max(6, min(width, 20)), max(4, min(height, 10)), max(6, min(length, 20))
    reg = Region(0, 0, 0, w, h, l)

    # 地板
    for x in range(w):
        for z in range(l):
            reg[x, 0, z] = wall

    # 四面牆
    for y in range(1, h - 1):
        for x in range(w):
            reg[x, y, 0]     = wall
            reg[x, y, l - 1] = wall
        for z in range(l):
            reg[0, y, z]     = wall
            reg[w - 1, y, z] = wall

    # 四角原木
    for y in range(1, h - 1):
        reg[0, y, 0]         = pillar
        reg[w-1, y, 0]       = pillar
        reg[0, y, l-1]       = pillar
        reg[w-1, y, l-1]     = pillar

    # 玻璃窗（前後牆）
    mid_x = w // 2
    for y in range(2, h - 2):
        reg[mid_x - 1, y, 0]     = glass
        reg[mid_x, y, 0]         = glass
        reg[mid_x - 1, y, l - 1] = glass
        reg[mid_x, y, l - 1]     = glass

    # 屋頂
    for x in range(w):
        for z in range(l):
            reg[x, h - 1, z] = slab

    schem = Schematic(name=name, author="MC Builder AI", description=f"{style}風格 {w}x{l}")
    schem.regions["Building"] = reg
    return schem
