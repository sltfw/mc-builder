from litemapy import Schematic, Region, BlockState

MATERIALS = {
    "木頭":  { "wall": "minecraft:oak_planks",       "pillar": "minecraft:oak_log",       "slab": "minecraft:oak_slab",         "stairs": "minecraft:oak_stairs",        "chimney": "minecraft:cobblestone" },
    "石頭":  { "wall": "minecraft:stone_bricks",      "pillar": "minecraft:stone",          "slab": "minecraft:stone_brick_slab",  "stairs": "minecraft:stone_brick_stairs","chimney": "minecraft:stone_bricks" },
    "深板岩":{ "wall": "minecraft:deepslate_bricks",  "pillar": "minecraft:deepslate",      "slab": "minecraft:deepslate_brick_slab","stairs":"minecraft:deepslate_brick_stairs","chimney":"minecraft:deepslate_bricks"},
    "沙岩":  { "wall": "minecraft:sandstone",         "pillar": "minecraft:cut_sandstone",  "slab": "minecraft:sandstone_slab",    "stairs": "minecraft:sandstone_stairs",  "chimney": "minecraft:sandstone" },
    "雲杉":  { "wall": "minecraft:spruce_planks",     "pillar": "minecraft:spruce_log",     "slab": "minecraft:spruce_slab",       "stairs": "minecraft:spruce_stairs",     "chimney": "minecraft:cobblestone" },
}

def generate_house(style="木頭", width=10, length=10, height=6, name="我的房子", towers=False):
    mat = MATERIALS.get(style, MATERIALS["木頭"])

    wall      = BlockState(mat["wall"])
    pillar    = BlockState(mat["pillar"])
    slab      = BlockState(mat["slab"], type="bottom")
    stair_e   = BlockState(mat["stairs"], facing="east",  half="bottom", shape="straight")
    stair_w   = BlockState(mat["stairs"], facing="west",  half="bottom", shape="straight")
    chimney_b = BlockState(mat["chimney"])
    glass     = BlockState("minecraft:glass")
    glass_pane= BlockState("minecraft:glass_pane")
    air       = BlockState("minecraft:air")

    w  = max(8, min(int(width),  20))
    h  = max(5, min(int(height), 10))
    l  = max(8, min(int(length), 20))

    OVER   = 1                    # roof overhang
    peak   = w // 2 + 1          # roof rise
    total_h = h + peak + 4       # wall + roof + chimney

    # Region is padded by OVER on x and z to fit overhang
    reg_w = w + 2 * OVER + (4 if towers else 0)
    reg_l = l + 2 * OVER + (4 if towers else 0)
    reg   = Region(0, 0, 0, reg_w, total_h, reg_l)

    # Building origin inside region
    ox = OVER + (2 if towers else 0)
    oz = OVER + (2 if towers else 0)

    # ── FLOOR ──
    for x in range(ox, ox + w):
        for z in range(oz, oz + l):
            reg[x, 0, z] = wall

    # ── WALLS ──
    for y in range(1, h - 1):
        for x in range(ox, ox + w):
            reg[x, y, oz]         = wall
            reg[x, y, oz + l - 1] = wall
        for z in range(oz, oz + l):
            reg[ox, y, z]         = wall
            reg[ox + w - 1, y, z] = wall

    # Corner pillars
    for y in range(1, h - 1):
        reg[ox,         y, oz]         = pillar
        reg[ox + w - 1, y, oz]         = pillar
        reg[ox,         y, oz + l - 1] = pillar
        reg[ox + w - 1, y, oz + l - 1] = pillar

    # ── WINDOWS (glass pane) ──
    mid_x = ox + w // 2
    mid_z = oz + l // 2
    for y in range(2, h - 2):
        # Front & back
        reg[mid_x - 1, y, oz]         = glass_pane
        reg[mid_x,     y, oz]         = glass_pane
        reg[mid_x - 1, y, oz + l - 1] = glass_pane
        reg[mid_x,     y, oz + l - 1] = glass_pane
        # Sides
        reg[ox,         y, mid_z - 1] = glass_pane
        reg[ox,         y, mid_z]     = glass_pane
        reg[ox + w - 1, y, mid_z - 1] = glass_pane
        reg[ox + w - 1, y, mid_z]     = glass_pane

    # Door opening (front wall, ground level)
    door_x = ox + w // 2 - 1
    reg[door_x, 1, oz] = air
    reg[door_x, 2, oz] = air

    # ── GABLED ROOF ──
    wall_top = h - 1

    for step in range(peak):
        y  = wall_top + step
        xl = ox - OVER + step           # left edge (with overhang)
        xr = ox + w - 1 + OVER - step   # right edge

        if xl > xr:
            break

        # Roof spans full length + overhang
        for z in range(oz - OVER, oz + l + OVER):
            if xl == xr:
                reg[xl, y, z] = slab        # ridge
            else:
                reg[xl, y, z] = stair_e
                reg[xr, y, z] = stair_w
                for x in range(xl + 1, xr):
                    reg[x, y, z] = wall     # solid fill inside roof

    # Gable end walls (triangular fill, no overhang in z)
    for step in range(peak - 1):
        y  = wall_top + step
        xl = ox + step
        xr = ox + w - 1 - step
        for x in range(xl, xr + 1):
            if oz - 1 >= 0:
                reg[x, y, oz - 1] = wall
            reg[x, y, oz + l] = wall

    # ── CHIMNEY ──
    cx = ox + w // 4
    cz = oz + l // 2 - 1
    chimney_top = wall_top + peak + 2
    for y in range(wall_top - 1, chimney_top):
        reg[cx,     y, cz]     = chimney_b
        reg[cx + 1, y, cz]     = chimney_b
        reg[cx,     y, cz + 1] = chimney_b
        reg[cx + 1, y, cz + 1] = chimney_b

    # ── TOWERS ──
    if towers:
        tower_h = h + 3
        tower_positions = [
            (OVER, OVER), (OVER, OVER + l + 1),
            (OVER + w + 1, OVER), (OVER + w + 1, OVER + l + 1)
        ]
        for tx, tz in tower_positions:
            for y in range(1, tower_h - 1):
                for dx in range(3):
                    for dz in range(3):
                        if dx == 0 or dx == 2 or dz == 0 or dz == 2:
                            reg[tx + dx, y, tz + dz] = wall
                reg[tx,     y, tz]     = pillar
                reg[tx + 2, y, tz]     = pillar
                reg[tx,     y, tz + 2] = pillar
                reg[tx + 2, y, tz + 2] = pillar
            for dx in range(3):
                for dz in range(3):
                    reg[tx + dx, tower_h - 1, tz + dz] = slab

    schem = Schematic(name=name, author="MC Builder AI", description=f"{style}風格 {w}x{l}")
    schem.regions["Building"] = reg
    return schem
