# run with pytest
import pygame

# run a game frame
pygame.init()
screen = pygame.display.set_mode((400, 400)) 

BOARD_SIZE = (24, 16) # originally 28, 20
BOARD_SIZE_PIXELS = (BOARD_SIZE[0] * 50, BOARD_SIZE[1] * 50)

from ui import *
from tile import *
TileFunctions.BOARD_SIZE = BOARD_SIZE
TileFunctions.BOARD_SIZE_PIXELS = BOARD_SIZE_PIXELS
BaseUI.BOARD_SIZE = BOARD_SIZE
BaseUI.BOARD_SIZE_PIXELS = BOARD_SIZE_PIXELS

# ------------------- ui -------------------
def test_floating_number():
    fn = FloatingNumber(screen)
    fn.create_number((1, 1), 128)
    fn.create_number((1, 1), 4128)
    assert len(fn.list_floaters) == 2
    for _ in range(30):
        fn.draw_all_floaters()
    assert len(fn.list_floaters) == 0

def test_ui_mgr():
    um = UIManager(screen)
    assert type(um.coins) == DynamicUI

def test_pause():
    pm = PauseMenu(screen)
    assert type(pm.surf) == pygame.surface.Surface

def test_base_ui():
    assert BaseUI.GOLD_COLOR == (255, 190, 50)
    bu = BaseUI(screen, False)
    assert bu.static_mode == False
    assert bu.displayitize_thousands(6400000000) == "6.4B"
    assert bu.displayitize_thousands(6400000) == "6.4M"
    assert bu.displayitize_thousands(6400) == "6.4k"
    assert bu.displayitize_thousands(64) == "64"
    
# ------------------- tile -------------------
def test_tile():
    ti = Tile((0,0))
    assert ti.type == "dirt"

def test_tile_mgr():
    tm = TileManager()
    for _ in range(30):
        tm.frame_update(screen)
        assert len(tm.sprite_tiles) <= 560

def tile_funcs():
    surf = pygame.surface.Surface((0, 0))
    tf = TileFunctions(surf)
    assert tf.image == surf