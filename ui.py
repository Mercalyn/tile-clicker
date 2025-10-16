import pygame
import math
import random


class BaseUI():
    GOLD_COLOR = (255, 190, 50)
    BOARD_SIZE = ()
    BOARD_SIZE_PIXELS = ()
    MONEYPERSEC_DECAY_RATE = .8 # raise to make money per second decay slower # .8
    
    """Base UI class"""
    def __init__(self, screen, static_mode: bool = True):
        self.screen = screen
        
        # static mode True for StaticUI, False for dynamic
        self.static_mode = static_mode
        
        # font dict
        self.font = {} # keyable dict
        self.font["h5"] = pygame.font.SysFont("georgia", 26) # h2 title
        self.font["h2"] = pygame.font.SysFont("georgia", 32) # h2 title
        self.font["p"] = pygame.font.SysFont("georgia", 22) # p paragraph text
    
    
    def draw_text(self, 
        html_tag_size: str, 
        text: str, 
        color: tuple = (240, 240, 240), 
        coord: tuple = (10, 10),
        alpha: int = 255,
        displayitize: bool = False
    ) -> int:
        """Draw Text on screen. """
        
        # check for displayitize thousands
        if displayitize:
            text = BaseUI.displayitize_thousands(text)
        
        # render
        img = self.font[html_tag_size].render(text, True, color)
        img.set_alpha(alpha)
        self.screen.blit(img, coord)
        return img.get_height()
    
    
    def draw_image(self, icon_location: str, coord: tuple, alpha: int = 255) -> int:
        img = pygame.image.load(icon_location)
        img.set_alpha(alpha)
        self.screen.blit(img, coord)
        return img.get_height()
    
    
    def return_padded_coord(self, padding: tuple) -> tuple:
        """
        Pad the coordinate, x+ goes right, y+ goes down.\n
        Mostly used for StaticUI
        """
        return (self.x + padding[0], self.y + padding[1])
        
    
    @staticmethod
    def displayitize_thousands(amount: float) -> str:
        """
        For values 1k, 1M, or 1B, display the k, M, B and shorten length
        example values:
        640 = 640
        6,400 = 6.4k
        640,000 = 640k
        6,400,000 = 6.4M
        """
        amount = float(amount) # 1399
        length = len(str(amount))
        
        # if multiple digits
        if length > 11:
            # greater than 11
            return f"{math.floor(amount / 1E8) / 10}B"
        elif length > 8:
            # greater than 8
            return f"{math.floor(amount / 1E5) / 10}M"
        elif length > 5:
            # greater than 5
            return f"{math.floor(amount / 1E2) / 10}k"
        else:
            return f"{int(amount)}"
        

class StaticUI(BaseUI):
    """Static Font and Image functions"""
    def __init__(self, screen, start_coord):
        super().__init__(screen, static_mode=True)
        self.x = start_coord[0]
        self.y = start_coord[1] # auto track y pixel so easier to generate lots of text
        
    
    def draw_text(self, html_tag_size: str, text: str, color: tuple = (240, 240, 240), padding: tuple = (10, 10)):
        # send to Font, which will return a height for auto row calcs
        coord = self.return_padded_coord(padding)
        this_element_height = super().draw_text(html_tag_size, text, color, coord)
        
        # calc new row
        self.calc_new_row(this_element_height, padding[1])
    
    
    def add_space(self, space_amount: int):
        """Add extra space"""
        self.y += space_amount
    
    
    def calc_new_row(self, height_element: int, y_padding: int):
        """
        Self-iterate a new y pixel value, this allows for quick font adding.\n
        No need to tediously set each individual font lines
        """
        self.y += height_element + (y_padding * 2)
    
    
    def draw_image(self, icon_location: str, padding: tuple = (10, 10)):
        """Draw Image"""
        coord = self.return_padded_coord(padding)
        this_element_height = super().draw_image(icon_location, coord)
        
        # calc new row
        self.calc_new_row(this_element_height, padding[1])
    
    
    def draw_separator(self, padding: tuple = (20, 5)):
        """Draw a horizontal line"""
        coord_start = self.return_padded_coord(padding)
        coord_end = (coord_start[0] + 350, coord_start[1])
        pygame.draw.line(self.screen, "white", coord_start, coord_end, width=2)
        
        # calc new row
        self.calc_new_row(2, padding[1])


class DynamicUI(BaseUI):
    """UI that moves or updates"""
    def __init__(self, screen):
        super().__init__(screen)
        self.inner_attr = {}
        
    
    def set_inner_attr(self, var_name: str, value: any):
        """Absolute value set or create new dynamic internal variable"""
        self.inner_attr[var_name] = str(value)
        
        
    def change_inner_attr(self, var_name: str, delta_val: int | float):
        """Increment or decrement"""
        delta_val = float(delta_val)
        self.inner_attr[var_name] = str(float(self.inner_attr[var_name]) + delta_val)
        
    
    def get_inner_attr(self, var_name: str) -> any:
        return str(self.inner_attr[var_name])
    
    
    def draw_visible_box(self, ul_corner: tuple, br_corner: tuple, color: tuple = (255, 0, 0)):
        """
        Draw a box somewhere.
        \nUL = upper left, BR = bottom right
        """
        box = pygame.Surface((br_corner[0] - ul_corner[0], br_corner[1] - ul_corner[1]))
        box.fill(color)
        self.screen.blit(box, (ul_corner))
        

class Button(DynamicUI):
    def __init__(self, 
            screen, 
            cost: int, 
            icon_location: str, 
            machine_location: str, 
            label: str, 
            coord: tuple,
            profit: int = None,
            is_upgrade: bool = False,
            upgrade_max_stages: int = 2,
            upgrade_key: str = "",
            increase: int = 0
        ):
        super().__init__(screen)
        
        # coord system
        self.ulx = coord[0] # upper left x
        self.uly = coord[1] # upper left y
        self.brx = coord[0] + 380 # bottom right x
        self.bry = coord[1] + 35 # bottom right y
        self.cost = cost
        self.icon_location = icon_location
        self.machine_location = machine_location
        self.profit = profit
        self.label = label
        self.is_upgrade = is_upgrade
        self.upgrade_stage = 1
        self.upgrade_max_stages =  upgrade_max_stages
        self.upgrade_key = upgrade_key
        self.status = False
        self.increase = increase
        self.draw_button()


    def draw_button(self):
        # set bg color depending on active state or not
        color = ()
        if self.status:
            # active
            color = (150, 30, 30)
        else:
            # inactive
            color = (40, 40, 40)
        
        self.draw_visible_box(ul_corner=(self.ulx, self.uly), br_corner=(self.brx, self.bry), color=color)
        self.draw_image("img/icon_tilecoin_sm.png", coord=(self.ulx + 2, self.uly + 4))
        self.draw_text("p", str(self.cost), coord=(self.ulx + 30, self.uly + 2), color=BaseUI.GOLD_COLOR, displayitize=True)
        self.draw_image(self.icon_location, coord=(self.ulx + 104, self.uly + 5))
        self.draw_text("p", self.label, coord=(self.ulx + 134, self.uly + 4))
    
    
    def set_status(self, active: bool):
        """Set this buttons status"""
        self.status = active
        
        # also redraw button
        self.draw_button()
    
    
    def click_within_bounds(self, click_coord: tuple) -> bool:
        """Set self.status accordingly for a click"""
        side_side = click_coord[0] > self.ulx and click_coord[0] < self.brx
        up_down = click_coord[1] > self.uly and click_coord[1] < self.bry
        
        # inner_bool will be true if clicked on this button
        inner_bool = all([side_side, up_down])
        
        if inner_bool:
            # this button was clicked on
            if not self.status:
                # prev state was inactive, activate it
                self.set_status(True)
            else:
                # prev state was active, so inactive it
                self.set_status(False)
                
        else:
            # this button was not clicked on
            self.set_status(False)
            
        return self.status
    
    
    def double_cost(self):
        """Modify cost of a button"""
        if self.is_upgrade:
            
            # still has upgrades to go
            if self.upgrade_stage < self.upgrade_max_stages:
                self.upgrade_stage += 1
                self.cost *= 3
            
            # is at last stage
            elif self.upgrade_stage == self.upgrade_max_stages:
                self.upgrade_stage += 1
                
                # inactivate button
                self.cost = 0
                self.label = f"MAX == x{2 ** self.upgrade_max_stages}"
            
            else:
                self.upgrade_stage += 1 # need for tile logic


class FloatingNumber(BaseUI):
    """
    Create RPG-like floating numbers\n
    Also has a simple moving average of coins / sec
    """
    PIXEL_RAISE_PER_FRAME = 5 # def: 5 # pixels that a floating number goes up y dir per frame gen
    
    def __init__(self, screen):
        super().__init__(screen)
        self.list_floaters = [] # array of dict with {val:int, stage:int, x:int, y:int} 
        # stage starts 20, once goes down to 0 it is deleted
        self.decay = 0 # to save on processing emulate a really long array, decays at some % per render
        self.last7 = [0] * 7 # actual sma
        self.decay_frame = 12 # only decays every 12 frames
        
        
    def create_number(self, click_coord: tuple, val: int | float):
        """Create a new floating number"""
        
        # check if x is too far right first
        req_x = (BaseUI.BOARD_SIZE_PIXELS[0] - 50 - (len(str(val)) * 16))
        if click_coord[0] > req_x:
            # it will run into UI menu, so put it left side
            click_coord = (click_coord[0] - (50 + (len(str(val)) * 16)), click_coord[1])
        
        strval = val
        if isinstance(val, float):
            strval = BaseUI.displayitize_thousands(val)
        if isinstance(val, int):
            strval = BaseUI.displayitize_thousands(val)
        if isinstance(val, str):
            val = 0.0
            
        self.list_floaters.append({
            "val": strval,
            "floatval": float(val),
            "stage": 8,
            "x": click_coord[0],
            "y": click_coord[1]
        })
    
    
    def draw_all_floaters(self):
        """Render all of the floating numbers, wherever they are"""
        for index, item in enumerate(self.list_floaters):
            coord_img = (
                item["x"] + 15, # x
                item["y"] - 4 # y
            )
            coord_text = (
                item["x"] + 42, # x
                item["y"] - 14 # y
            )
            
            # draw img and text
            #opa = min(item["stage"] * 40, 255)
            # unfortunately opacity contributes to frame lag, so full opacity always
            opa = 255
            
            
            super().draw_image("img/icon_tilecoin_sm.png", coord_img, alpha=opa)
            super().draw_text("h2", str(item["val"]), BaseUI.GOLD_COLOR, coord_text, alpha=opa)
            
            
            # update its stage and y pos so it floats upwards
            self.list_floaters[index]["stage"] -= 1
            self.list_floaters[index]["y"] -= self.PIXEL_RAISE_PER_FRAME
            
            # check end of stage removal
            if self.list_floaters[index]["stage"] < 0:
                # strange end-of-life flickering if remove too early, hence -20 for stage check
                # fixing the flickering requires more processing power to draw it in a different spot for a few frames
                # and we can't spare power, so, flicker away ?!?
                self.list_floaters.remove(item)
                
                # add it to decay for money per second
                self.decay += item["floatval"]
                
    
    def calc_sma(self) -> int:
        """Add upp all current floaters for money per second, simple moving average"""
        # current decay gets decayed, which helps save on having an array of size 1400 each render
        if self.decay_frame == 0:
            self.decay = round(self.decay * BaseUI.MONEYPERSEC_DECAY_RATE, 2)
            self.decay_frame = 12
        else:
            self.decay_frame -= 1
        
        floater_sum = sum([s["floatval"] for s in self.list_floaters])
        total = floater_sum + self.decay
        
        #print(f"decay {self.decay} -- {floater_sum} -- {total}")
        
        # actual sma stuff
        self.last7.append(total)
        self.last7.pop(0)
        
        # return the money per second
        return round(sum(self.last7) / 7 / 2) # the last / 2 is just a const for rescaling the numbers since they aren't exactly run per second, but simulated from a decay to save on processing


class BuyButtons(Button):
    """Return list of all Buy Buttons in the Shop"""
    def __new__(cls, screen) -> list:
        """
        Adding a buy button? places to consider:
        1 here in BuyButton to make the button
        
        if machine or tile button:
        2 in TileManager.click_event_value (2 if sellable, 1 if not) actually places or sells the tile
        1 in Tile.process_machine_tile for functionality / moneymaking
        
        if upgrade button:
        add relevant upgrade info to button while making it
        """
        
        cls.arr = []
        
        # height of button is determined first by its y offset, then its scale
        y_offset_shop = 158
        y_offset_upgrades = 200
        y_scale = 40
        x_absolute = BaseUI.BOARD_SIZE_PIXELS[0] + 10
        
        # water tile
        cls.arr.append(Button(screen, 
            cost=17, 
            icon_location="img/icon_blue.png",
            machine_location=None,
            label="Water Tile", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            increase = 0
        ))
        
        # pavement
        cls.arr.append(Button(screen, 
            cost=23, 
            icon_location="img/icon_pavement.png",
            machine_location=None,
            label="Decorative Pavement", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            increase = 0
        ))
        
        # dirt excav
        cls.arr.append(Button(screen, 
            cost=32, 
            icon_location="img/icon_dirt_excav.png", 
            machine_location="img/machine_dirt_excav.png", 
            label="Dirt Excavator", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            profit=1,
            increase = 2
        ))
        
        # house
        cls.arr.append(Button(screen,
            cost=500, 
            icon_location="img/icon_house.png", 
            machine_location="img/machine_house.png", 
            label="House", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            profit=8,
            increase = 24
        ))
        
        # grass harv
        cls.arr.append(Button(screen,
            cost=2100, 
            icon_location="img/icon_grass_excav.png", 
            machine_location="img/machine_grass_excav.png", 
            label="Grass Harvester", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            profit=12,
            increase = 400
        ))
        
        # water pump
        cls.arr.append(Button(screen,
            cost=34000, 
            icon_location="img/icon_water_pump.png", 
            machine_location="img/machine_water_pump.png", 
            label="Water Pump", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            profit=-54, # cost to run pump
            increase = 1000
        ))
        
        # market
        cls.arr.append(Button(screen,
            cost=210000, 
            icon_location="img/icon_market.png",
            machine_location="img/machine_market.png",
            label="Market", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            profit=0, # uses a randomly unique mostly positive, sometimes negative function in Tile,
            increase = 10000
        ))
        
        # quant tile
        cls.arr.append(Button(screen,
            cost=1001000, 
            icon_location="img/icon_quantum_tile.png",
            machine_location=None,
            label="Quantum Tile", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            increase = 100000
        ))
        
        # quant pc machine
        cls.arr.append(Button(screen,
            cost=2001000, 
            icon_location="img/icon_quantum_pc.png",
            machine_location="img/machine_quantum_pc.png",
            label="Quantum PC", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_shop),
            profit=20000,
            increase = 240000
        ))
        
        # upgrades
        # grass mult upgrade
        cls.arr.append(Button(screen,
            cost=170, 
            icon_location="img/icon_grass_mult.png", 
            machine_location=None, 
            label="Grass Profit x2", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_upgrades),
            is_upgrade=True,
            upgrade_max_stages=7,
            upgrade_key="grass"
        ))
        
        # rent upgrade
        cls.arr.append(Button(screen,
            cost=500, 
            icon_location="img/icon_house.png", 
            machine_location="img/machine_house.png", 
            label="Rent x2", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_upgrades),
            is_upgrade=True,
            upgrade_max_stages=12,
            upgrade_key="rent"
        ))
        
        # grass spread upgrade
        cls.arr.append(Button(screen,
            cost=2100, 
            icon_location="img/icon_grass_mult.png", 
            machine_location=None, 
            label="Grass Spreads x2", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_upgrades),
            is_upgrade=True,
            upgrade_max_stages=5,
            upgrade_key="grassspread"
        ))
        
        # market mult upgrade
        cls.arr.append(Button(screen,
            cost=17000, 
            icon_location="img/icon_market.png",
            machine_location=None,
            label="Market Mult x2", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_upgrades),
            is_upgrade=True,
            upgrade_max_stages=6,
            upgrade_key="market"
        ))
        
        # quantum mult upgrade
        cls.arr.append(Button(screen,
            cost=1700000, 
            icon_location="img/icon_quantum_pc.png",
            machine_location=None,
            label="Quantum Mult x2", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_upgrades),
            is_upgrade=True,
            upgrade_max_stages=6,
            upgrade_key="qt"
        ))
        
        # win pillar
        cls.arr.append(Button(screen,
            cost=1000000000, 
            icon_location="img/icon_win.png",
            machine_location=None,
            label="WIN", 
            coord=(x_absolute, (len(cls.arr) * y_scale) + y_offset_upgrades),
            is_upgrade=True,
            upgrade_max_stages=1,
            upgrade_key="win"
        ))
        
        # return whole list afterwards
        return cls.arr


class PauseMenu(StaticUI):
    """Instructions Menu"""
    def __init__(self, screen):
        self.screen = screen
        self.surf = pygame.image.load("img/instructions.jpg")
        self.surf.set_alpha(40)
    
    
    def draw_menu(self):
        self.screen.blit(self.surf, (0, 0))


class WinMenu(StaticUI):
    """Fancy Win Menu -- Only for Winners!"""
    def __init__(self, screen):
        self.screen = screen
        self.surf = pygame.image.load("img/win.jpg")
        self.surf.set_alpha(100)
        
        self.randomize_fresh()
        self.stage = 10 # once reaches 0 it will re randomize
    
    
    def randomize_fresh(self):
        self.surf.set_alpha(100)
        self.x = random.randint(-200, BaseUI.BOARD_SIZE_PIXELS[0] + 200)
        self.y = random.randint(-200, BaseUI.BOARD_SIZE_PIXELS[1] - 200)
        self.ran_x = random.randint(1, 6) * (random.randint(0, 1) -.5) * 2
        self.ran_y = random.randint(1, 6) * (random.randint(0, 1) -.5) * 2
    
    
    def draw_menu(self):
        if self.stage == 0:
            self.stage = 20
            self.randomize_fresh()
        
        if self.stage == 1:
            self.surf.set_alpha(255)
            
        self.screen.blit(self.surf, (self.x, self.y))
        self.x += self.ran_x
        self.y += self.ran_y
        self.stage -= 1


class UIManager():
    def __init__(self, screen):
        """Setup UI components. Init is drawn behind TileManager"""
        sui = StaticUI(screen, (BaseUI.BOARD_SIZE_PIXELS[0], 0)) # static encompasses all elements
        self.coins = DynamicUI(screen) # dynamic UI elements are individually tracked
        self.mps = DynamicUI(screen) # money per second
        self.buy_buttons_arr = BuyButtons(screen)
        self.mps_frame = 3 # only render money per second every 3 frames for visibility
        
        self.screen = screen
        self.active_button = None
        
        # draw static UI in order as it appears
        sui.draw_image("img/icon_tilecoin.png", padding=(10, 14))
        # ---
        sui.draw_text("p", "<ESC for Instructions>", color=(80,80,80), padding=(80, 0))
        self.mults = DynamicUI(screen)
        sui.draw_separator()
        # ---
        sui.draw_text("h2", "SHOP", color=BaseUI.GOLD_COLOR, padding=(145, 0))
        sui.add_space(365)
        # ---
        sui.draw_text("h2", "UPGRADES", color=BaseUI.GOLD_COLOR, padding=(105, 0))
        
        # dynamic components
        # coin counter
        self.coins.set_inner_attr("coins", 0) # debug::starting cash
        self.coins.draw_text("h2", "0", color=BaseUI.GOLD_COLOR, coord=(BaseUI.BOARD_SIZE_PIXELS[0] + 68, 4))
        # money per second
        self.mps.set_inner_attr("mps", 0)
        self.mps.draw_text("p", f"0 / sec", color="white", coord=(BaseUI.BOARD_SIZE_PIXELS[0] + 68, 42))
    
    
    def update_mps(self, sma: float):
        """Update money per second"""
        if self.mps_frame == 0:
            self.mps.set_inner_attr("mps", sma)
            
            # reset bg and redraw
            sma = BaseUI.displayitize_thousands(sma)
            self.mps.draw_visible_box((BaseUI.BOARD_SIZE_PIXELS[0] + 68, 42), (BaseUI.BOARD_SIZE_PIXELS[0] + 400, 74), color=(0, 0, 0))
            self.mps.draw_text("p", f"{sma} / sec", color="white", coord=(BaseUI.BOARD_SIZE_PIXELS[0] + 68, 42))
            
            self.mps_frame = 3
        else:
            self.mps_frame -= 1
    
    
    def update_coins(self, value_clicked: int):
        """Update Coins"""
        # on click that is a tile delete coins and redraw
        self.coins.change_inner_attr("coins", value_clicked)
        
        # reset coins and redraw
        self.coins.draw_visible_box((BaseUI.BOARD_SIZE_PIXELS[0] + 68, 4), (BaseUI.BOARD_SIZE_PIXELS[0] + 400, 46), color=(0, 0, 0))
        self.coins.draw_text("h2", self.coins.get_inner_attr("coins"), color=BaseUI.GOLD_COLOR, coord=(BaseUI.BOARD_SIZE_PIXELS[0] + 68, 4), displayitize=True)
    
    
    def button_check(self, click_coord: tuple):
        """Check if buttons should be activated or inactivated."""
        self.active_button = None
        
        for buy_button in self.buy_buttons_arr:
            if buy_button.click_within_bounds(click_coord):
                self.active_button = buy_button
    
    
    def refresh_button(self):
        if self.active_button != None:
            self.active_button.draw_button()