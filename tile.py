import pygame
import random
import math


class TileFunctions():
    """Base reuseable functions"""
    BOARD_SIZE = ()
    BOARD_SIZE_PIXELS = ()
    
    def __init__(self, surface_image):
        self.color = (0, 0, 0)
        self.image = surface_image
        
    
    def color_clamp(self, val: int | float) -> int:
        """Returns 0-255 clamped value"""
        return int(min(max(val, 0), 255))


    def new_fill_color(self, dr, dg, db):
        """Set a new fill color on a sprite surface by specifying the change in red, green, blue"""
        new_color = (
            self.color_clamp(self.color[0] + dr),
            self.color_clamp(self.color[1] + dg),
            self.color_clamp(self.color[2] + db),
        )
        self.image.fill(new_color)
        self.color = new_color


    def rperc(self, perc_true_chance: float) -> bool:
        """X percent chance to return True"""
        perc_true_chance *= 10000
        return random.randint(0, 10000) < perc_true_chance


class Tile(pygame.sprite.Sprite, TileFunctions):
    """The primary, individual Tile class for world tiles"""
    
    # STATIC VARIABLES
    # percent chance to 
    CHANCE_GRASS_FROM_WATER = .4 # .08
    CHANCE_GREENER_GRASS = .015 # .01
    CHANCE_WATER_EVAP = .02 #.02 # chance per frame per stage of 16
    CHANCE_CHECK_COORD = .01 # .06 # lower = better performance, spot checking
    
    # machine
    CHANCE_CHECK_MACHINE = .2 # .2
    MACHINE_ROTATION_SPEED = (3, 6) # range of random, affects some machines outputs
    MACHINE_TICK_EVERY = 180 # every rotational degree, higher = less frequent
    GRASSHARV_TOTALLY_EAT_GRASS = .1
    CHANCE_HOUSE_TAX = .02
    CHANCE_MARKET_PNL = .02
    dynamic_render = 1 # higher = less refresh rate but better performance
    
    # world upgrades
    multiplier = {
        "market": 1,
        "grass": 1,
        "rent": 1,
        "grassspread": .001,
        "qt": 1,
        "win": 1
    }

    def __init__(self, coord: tuple):
        pygame.sprite.Sprite.__init__(self)
        
        # attr
        self.coord = coord
        self.type = "dirt" # start all tiles with dirt, converts to grass on grass_stage 1
        self.grass_stage = 0 # 4 stages
        self.water_evap = 0 # water tiles start at 16, and disappear back to dirt at 0
        self.water_does_evap = True
        self.machine = None # machine is drawn on top of tile color
        self.machine_img = None
        self.machine_rot_curr = 0 # rotation to animate machines
        self.machine_rot_rate = 0
        self.machine_moneymake = 0 # how much machines make per logic tick
        self.queued_val = 0 # push to queued if this tile's machine should give money
        self.render_stage = self.dynamic_render # every x: render frame
        
        """
        debug::performance tweaking purposes
        self.machine = "house"
        self.machine_img = "img/machine_dirt_excav.png"
        self.machine_moneymake = 1
        self.machine_rot_rate = 5
        """
        
        # pygame surface
        self.image = pygame.Surface((50, 50))
        self.tile_bg = self.image # this is for machine rendering later
        self.rect = self.image.get_rect()
        # 50 for the scale, 25 for offset
        self.rect.center = ((coord[0] * 50) + 25, (coord[1] * 50) + 25)
        TileFunctions.__init__(self, self.image)
        
        # convert to default dirt
        self.convert_to_dirt()


    def update(self):
        """
        Sprite updates that can be easily applied without needing adjacent tiles info\n
        This is a named section from pygame.sprite.Sprite
        """
        
        # ---------------- tiles ----------------
        # if grass that isn't totally grown yet, chance to grow greener and ++ on grass_stage
        if self.type == "grass" and self.grass_stage < 4 and self.rperc(self.CHANCE_GREENER_GRASS):
            self.grass_stage += 1
            self.new_fill_color(-20, self.grass_stage * 2 * random.randint(1, 2), 0)
        
        # water evaporate
        if self.type == "water" and self.water_evap > 0 and self.rperc(self.CHANCE_WATER_EVAP):
            if self.machine != "waterpump" and self.water_does_evap:
                # does not have a water pump and it does evaporate
                self.water_evap -= 1
                self.new_fill_color(2, 2, -6) # go towards dirt color
        
        # on total water evaporation
        if self.type == "water" and self.water_evap == 0:
            self.water_evap = 0
            self.convert_to_dirt() # reset to dirt
        
        # ---------------- machines ----------------
        if self.machine != None and self.machine_img != None:
            self.process_machine_tile()
    
    
    def process_machine_tile(self):
        """Draw a machine on top of a tile"""
        
        # first determine whether to render this tile/machine
        # affects self.image.fill and surf.blit at bottom
        do_render = (self.render_stage == 0)
        if self.render_stage == 0: self.render_stage = self.dynamic_render
        self.render_stage -= 1
        
        # clear tile first
        if do_render:
            self.image.fill(self.color)
        
        # load machine image
        surf = pygame.image.load(self.machine_img) # size 50x50
        
        # rotation math
        surf = pygame.transform.rotate(surf, self.machine_rot_curr)
        x_offset, y_offset = surf.get_size()
        x_offset = (50 - x_offset) / 2
        y_offset = (50 - y_offset) / 2
        self.machine_rot_curr += self.machine_rot_rate
        
        # queue a money make if it should
        # this section is DEPENDENT on machine rotation
        if self.machine_rot_curr % self.MACHINE_TICK_EVERY == 0:
            # dirt
            if self.machine == "dirtexcav":
                self.queued_val = self.machine_moneymake
            
            # grass
            if self.machine == "grassharv" and self.type == "grass" and self.grass_stage > 0:
                self.queued_val = self.machine_moneymake * self.grass_stage * Tile.multiplier["grass"]
                
                # chance to not eat grass_stage
                if self.rperc(.2):
                    self.grass_stage -= 1
                    
                # smallest chance to completely eat grass stage
                if self.rperc(self.GRASSHARV_TOTALLY_EAT_GRASS):
                    self.convert_to_dirt()
                
                self.new_fill_color(0, -2 * random.randint(1, 2), 0)
            
            # reset grass to dirt if it harvests last grass
            if self.machine == "grassharv" and self.grass_stage == 0:
                self.convert_to_dirt()
            
            # water pump refresh water
            if self.machine == "waterpump":
                # cost to run pump
                self.queued_val = self.machine_moneymake
                if self.type != "water":
                    self.convert_to_water()
            
            # quantum pc
            if self.machine == "quantumpc" and self.type == "quantum":
                self.queued_val = self.machine_moneymake * Tile.multiplier["qt"]
        
        
        # queue moneymaking that is NOT DEPENDENT on machine rotation
        if self.machine == "house" and self.rperc(self.CHANCE_HOUSE_TAX):
            # random chance to payout taxes
            self.queued_val = self.machine_moneymake * Tile.multiplier["rent"]
            
        elif self.machine == "market" and self.rperc(self.CHANCE_MARKET_PNL):
            # random profits or loss, but positive average ev
            if self.rperc(.3):
                # 30% losing
                self.queued_val = random.randint(1, 6) * -120 * Tile.multiplier["market"]
            else:
                # 70% winning
                self.queued_val = random.randint(1, 8) * 120 * Tile.multiplier["market"]
        
        # render on top of reset tile
        if do_render:
            self.image.blit(surf, (x_offset, y_offset))


    def convert_to_water(self):
        """Convert this tile to water"""
        self.type = "water"
        self.grass_stage = 0
        self.water_evap = 16
        self.new_fill_color(-255, -255, -255)
        self.new_fill_color(0, 0, 100 + random.randint(1, 6) * 8)


    def convert_to_grass(self):
        """Spawn grass by converting this tile to light grass color"""
        self.type = "grass"
        self.grass_stage = 1
        self.new_fill_color(-20, +10, 0)
    
    
    def convert_to_quantum(self):
        """Spawn quantum tile"""
        self.type = "quantum"
        self.new_fill_color(-256, -256, -256)
        r = (random.randint(-2, 2) * 4) + 230
        b = (random.randint(-2, 2) * 2) + 110
        self.new_fill_color(r, 0, b)
    
    
    def convert_to_pavement(self):
        """Pavement"""
        self.type = "pavement"
        rand = (random.randint(-2, 2) * 9) + 210
        self.new_fill_color(-256, -256, -256)
        self.new_fill_color(rand - 20, rand, rand)
    
    
    def convert_to_dirt(self):
        """Delete a tile back to default dirt"""
        self.type = "dirt"
        self.grass_stage = 0
        self.water_evap = 0
        self.new_fill_color(-256, -256, -256)
        self.new_fill_color(80 + (random.randint(1, 4) * 4), 40 + (random.randint(1, 2) * 2), 22)


class TileManager(Tile):
    """
    The main sprite tracking class that interfaces outside of tile module\n
    Controls sprite updates that require adjacent-tile wizardry
    """
    def __init__(self):
        # LayeredUpdates is a kind of pygame sprite group that allows retrieval of sprite at coord
        self.sprite_tiles = pygame.sprite.LayeredUpdates()
        self.queued_val_arr = [] # list of dict of {coord: (pixel coord), val: int}
        
        # create a list of all coords, makes list comprehension easier for later if needed
        self.list_all_coords = []
        for x in range(0, TileFunctions.BOARD_SIZE[0]):
            for y in range(0, TileFunctions.BOARD_SIZE[1]):
                self.list_all_coords.append((x, y))
        
        # create a grid of Tile objs lining the background
        [self.sprite_tiles.add(Tile(coord)) for coord in self.list_all_coords]
        
        # make water tiles to demonstrate how water and grass work
        for _ in range(4):
            self.create_random_water()


    def frame_update(self, screen: pygame.display):
        """----------------------------- WORLD, TILE UPDATE -----------------------------"""
        # this will call update() on all Tile instances
        # includes self grass grow
        self.sprite_tiles.update()
        
        # draw sprites to screen
        self.sprite_tiles.draw(screen)
    
        # check all water tiles to grow grass adjacent
        self.water_grows_grass()
        
        # check grass tiles to grow grass adjacent
        self.grass_grows_grass()
        
        # check moneymaking queued values
        self.check_moneymaking()
        
        # tiles should not infinitely spread
        assert len(self.sprite_tiles) <= 560
    
    
    def check_moneymaking(self):
        """
        Check all tiles for queued money profits.\n
        It uses CHANCE_CHECK_MACHINE, so won't grab queued profit immediately,\n
        saving on processing.
        """
        check_these = [
            st for st in self.sprite_tiles
            if self.rperc(self.CHANCE_CHECK_MACHINE)
        ]
        
        for st in check_these:
            if st.queued_val != 0:
                # convert to pixel coords
                coord = (
                    st.coord[0] * 50 + 25,
                    st.coord[1] * 50 + 25
                )
                
                # append new to self list
                self.queued_val_arr.append({
                    "coord": coord, 
                    "val": st.queued_val
                })
                
                # this sprite's queued value goes back to 0
                st.queued_val = 0


    def return_sprite_at_coord(self, coord: tuple, coord_mode: bool = True) -> pygame.sprite.Sprite:
        """Get tile sprite object given set of tile coords. Use coord_mode False to use pixel coords"""
        
        # tile coord
        if coord_mode:
            coord = (
                coord[0] * 50 + 25,
                coord[1] * 50 + 25
            )
        
        # clamping coord helps lower out of bounds issues later
        coord = (
            min(max(coord[0], 0), TileFunctions.BOARD_SIZE_PIXELS[0] - 1), # 0 - max x - 1
            min(max(coord[1], 0), TileFunctions.BOARD_SIZE_PIXELS[1] - 1) # 0 - max y - 1
        )
        
        try:
            ret = self.sprite_tiles.get_sprites_at(coord)[0]
        except IndexError:
            # error catch, if notice any weird upper left corner bugs...
            ret = self.sprite_tiles.get_sprites_at((0, 0))[0]
        return ret


    def is_adjacent_to_type(self, this_coord: tuple, check_for_type: str) -> bool:
        """
        For given coord, returns True if it is adjacent to check_for_type
        ex. is_adjacent_to_type((0, 4), "water")
        """
        north = self.return_sprite_at_coord((this_coord[0], this_coord[1] - 1)).type == check_for_type
        south = self.return_sprite_at_coord((this_coord[0], this_coord[1] + 1)).type == check_for_type
        west = self.return_sprite_at_coord((this_coord[0] - 1, this_coord[1])).type == check_for_type
        east = self.return_sprite_at_coord((this_coord[0] + 1, this_coord[1])).type == check_for_type
        
        return any([north, south, west, east])
    
    
    def is_adjacent_to_machine(self, this_coord: tuple, check_for_machine: str) -> bool:
        """
        For given coord, returns True if it is adjacent to check_for_type
        ex. is_adjacent_to_type((0, 4), "water")
        """
        north = self.return_sprite_at_coord((this_coord[0], this_coord[1] - 1)).machine == check_for_machine
        south = self.return_sprite_at_coord((this_coord[0], this_coord[1] + 1)).machine == check_for_machine
        west = self.return_sprite_at_coord((this_coord[0] - 1, this_coord[1])).machine == check_for_machine
        east = self.return_sprite_at_coord((this_coord[0] + 1, this_coord[1])).machine == check_for_machine
        
        return any([north, south, west, east])


    def water_grows_grass(self):
        """Water tiles will occasionally spawn grass on dirt adjacent to them"""
        
        # checking everything is insanely slow, so spot check random pixels
        check_these = [
            st for st in self.sprite_tiles
            if self.rperc(self.CHANCE_CHECK_COORD)
        ]
        
        # obtain a list of water adjacent blocks that are also dirt
        coords_for_water_adj = [
            st.coord 
            for st in check_these 
            if self.is_adjacent_to_type(st.coord, "water") 
            and st.type == "dirt"
        ]
        # everything here is water adjacent and is dirt
        
        # tile will convert to grass if passing individual random check
        [
            self.return_sprite_at_coord(coord).convert_to_grass() 
            for coord in coords_for_water_adj 
            if self.rperc(self.CHANCE_GRASS_FROM_WATER)
        ]


    def grass_grows_grass(self):
        """If unlocked: grass tiles will occasionally spawn grass on dirt adjacent to them"""
        
        # checking everything is insanely slow, so spot check random pixels
        check_these = [
            st for st in self.sprite_tiles
            if self.rperc(self.CHANCE_CHECK_COORD)
        ]

        # obtain a list of water adjacent blocks that are also dirt
        coords_for_water_adj = [
            st.coord 
            for st in check_these
            if self.is_adjacent_to_type(st.coord, "grass") 
            and st.type == "dirt"
        ]
        # everything here is water adjacent and is dirt

        # tile will convert to grass if passing individual random check
        [
            self.return_sprite_at_coord(coord).convert_to_grass() 
            for coord in coords_for_water_adj
            if self.rperc(Tile.multiplier["grassspread"])
        ]


    def create_random_water(self):
        """Will self-create 1 random water tile"""
        # central coord
        central_lake_coord = (
            random.randint(1, TileFunctions.BOARD_SIZE[0] - 2), # max board x - 2
            random.randint(1, TileFunctions.BOARD_SIZE[1] - 2), # max board y - 2
        )

        self.return_sprite_at_coord(central_lake_coord).convert_to_water()
    
    
    def click_event_value(self, pixel_coord: tuple, coins: float, active_button) -> int:
        """Primary Event/Click Logic"""
        this_sprite = self.return_sprite_at_coord(pixel_coord, coord_mode=False)
        val = "Can't Afford!" # default to can't afford cuts down on elses
        is_selling_machine = False
        is_selling_tile = False
        is_buying_machine = False
        is_buying_tile = False
        
        if active_button != None:
            can_buy_this = float(coins) >= active_button.cost
        
        
        # ------------------------------------------------------------------
        # not trying to buy anything, proceed normally with tile click
        if active_button == None:
                
            # dirt
            if this_sprite.type == "dirt":
                val = 1
            
            # dirt
            if this_sprite.type == "pavement":
                val = 7
                
            # water
            elif this_sprite.type == "water":
                val = 0
                
            # grass
            elif this_sprite.type == "grass":
                val = int(this_sprite.grass_stage * 1.5 * Tile.multiplier["grass"]) + 2
                
                # reset grass
                this_sprite.grass_stage = 0
                this_sprite.convert_to_dirt()
            
            # quant tile
            if this_sprite.type == "quantum":
                val = 21000 * Tile.multiplier["qt"]
        
        # ------------------------------------------------------------------
        # sell stuff
        # sell dirtexcav
        elif active_button.label == "Dirt Excavator" and this_sprite.machine == "dirtexcav":
            this_sprite.convert_to_dirt()
            is_selling_machine = True
        
        # sell house
        elif active_button.label == "House" and this_sprite.machine == "house":
            this_sprite.convert_to_dirt()
            is_selling_machine = True
        
        # sell grassharv
        elif active_button.label == "Grass Harvester" and this_sprite.machine == "grassharv":
            this_sprite.convert_to_grass()
            is_selling_machine = True
        
        # sell water pump
        elif active_button.label == "Water Pump" and this_sprite.machine == "waterpump":
            this_sprite.convert_to_water()
            is_selling_machine = True
        
        # sell market
        elif active_button.label == "Market" and this_sprite.machine == "market":
            this_sprite.convert_to_dirt()
            is_selling_machine = True
        
        # sell pavement
        elif active_button.label == "Decorative Pavement" and this_sprite.type == "pavement":
            this_sprite.convert_to_dirt()
            is_selling_tile = True
        
        # sell quantum tile
        elif active_button.label == "Quantum Tile" and this_sprite.type == "quantum":
            this_sprite.convert_to_dirt()
            is_selling_tile = True
        
        # sell quantum pc
        elif active_button.label == "Quantum PC" and this_sprite.machine == "quantumpc":
            if this_sprite.type == "quantum":
                this_sprite.convert_to_quantum()
            else:
                this_sprite.convert_to_dirt()
                
            is_selling_machine = True
        
        
        # ------------------------------------------------------------------
        # trying to buy tiles
        # water
        elif active_button.label == "Water Tile" and can_buy_this:
            # can renew and refresh buy buying another on top of old
            this_sprite.convert_to_water()
            this_sprite.water_evap = 16
            is_buying_tile = True
        
        # pavement
        elif active_button.label == "Decorative Pavement" and can_buy_this:
            this_sprite.convert_to_pavement()
            is_buying_tile = True
        
        # quantum tile
        elif active_button.label == "Quantum Tile" and can_buy_this:
            this_sprite.convert_to_quantum()
            is_buying_tile = True
        
        
        # ------------------------------------------------------------------
        # buy upgrades are located in upgrade_button
        
        
        # ------------------------------------------------------------------
        # v buy machine below this point v
        
        # sprite not machine-empty
        elif this_sprite.machine != None:
            val = "Occupied!"
            
        # buy dirt excav
        elif active_button.label == "Dirt Excavator" and can_buy_this:
            this_sprite.machine = "dirtexcav"
            this_sprite.machine_rot_rate = random.randint(
                self.MACHINE_ROTATION_SPEED[0], 
                self.MACHINE_ROTATION_SPEED[1]
            )
            this_sprite.machine_rot_rate *= (self.rperc(.5) - .5) * 2 # chance to reverse
            is_buying_machine = True
        
        # buy house
        elif active_button.label == "House" and can_buy_this:
            this_sprite.machine = "house"
            this_sprite.machine_rot_rate = 0
            this_sprite.machine_rot_curr = random.randint(0, 3) * 90 # random orthogonal dir
            is_buying_machine = True
        
        # buy grass harvester
        elif active_button.label == "Grass Harvester" and can_buy_this:
            this_sprite.machine = "grassharv"
            this_sprite.machine_rot_rate = random.randint(
                self.MACHINE_ROTATION_SPEED[0], 
                self.MACHINE_ROTATION_SPEED[1]
            )
            this_sprite.machine_rot_rate *= (self.rperc(.5) - .5) * 2 # chance to reverse
            is_buying_machine = True
        
        # buy water pump
        elif active_button.label == "Water Pump" and can_buy_this:
            this_sprite.machine = "waterpump"
            this_sprite.machine_rot_rate = -4
            is_buying_machine = True
            
            # automatically set tile and adjacent tiles to water to save on processing
            x, y = this_sprite.coord
            for y_offset in range(-1, 2):
                for x_offset in range(-1, 2):
                    coord = (x + x_offset, y + y_offset)
                    self.return_sprite_at_coord(coord).convert_to_water()
                    self.return_sprite_at_coord(coord).water_does_evap = False
        
        # buy market
        elif active_button.label == "Market" and can_buy_this:
            this_sprite.machine = "market"
            this_sprite.machine_rot_rate = 0
            this_sprite.machine_rot_curr = random.randint(0, 3) * 90
            is_buying_machine = True
        
        # buy quantum pc
        elif active_button.label == "Quantum PC" and can_buy_this:
            this_sprite.machine = "quantumpc"
            this_sprite.machine_rot_rate = (random.randint(-2, 2) * 8) + 42
            this_sprite.machine_rot_rate *= (self.rperc(.5) - .5) * 2 # chance to reverse
            is_buying_machine = True

        # ------------------------------------------------------------------  
        
        # value, machine, and button cost logic
        # selling
        if is_selling_machine:
            val = math.floor(active_button.cost * .8)
            active_button.cost -= active_button.increase
            this_sprite.machine = None
        elif is_selling_tile:
            val = math.floor(active_button.cost * .8)
            active_button.cost -= active_button.increase
        
        # buying
        elif is_buying_tile:
            val = -active_button.cost
            active_button.cost += active_button.increase
        elif is_buying_machine:
            val = -active_button.cost
            this_sprite.machine_img = active_button.machine_location
            this_sprite.machine_moneymake = active_button.profit
            active_button.cost += active_button.increase
            
        return val
    
    
    def upgrade_button(self, active_button) -> bool:
        if active_button != None:
            
            # check stage
            if active_button.upgrade_stage < active_button.upgrade_max_stages + 2:
                Tile.multiplier[active_button.upgrade_key] *= 2
                
                # check for win condition
                if active_button.upgrade_key == "win":
                    
                    # player has won, do something
                    return True
        
        return False