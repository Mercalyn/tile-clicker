import pygame
import sys
import random
from tile import TileManager, Tile, TileFunctions
from ui import UIManager, FloatingNumber, PauseMenu, WinMenu, BaseUI

def main():
    pygame.init()
    
    # display:: just tiles: 1400x1000 # with sidebar: 1600x1000 # x 0-27, y 0-19
    BOARD_SIZE = (24, 16) # originally 28, 20
    BOARD_SIZE_PIXELS = (BOARD_SIZE[0] * 50, BOARD_SIZE[1] * 50)
    screen = pygame.display.set_mode((BOARD_SIZE_PIXELS[0] + 400, BOARD_SIZE_PIXELS[1])) 
    #screen = pygame.display.set_mode((1800, 1000)) 
    TileFunctions.BOARD_SIZE = BOARD_SIZE
    TileFunctions.BOARD_SIZE_PIXELS = BOARD_SIZE_PIXELS
    BaseUI.BOARD_SIZE = BOARD_SIZE
    BaseUI.BOARD_SIZE_PIXELS = BOARD_SIZE_PIXELS
    
    pygame.display.set_caption("Tile Clicker")
    favicon = pygame.image.load("img/icon_tilecoin_sm.png")
    pygame.display.set_icon(favicon)

    clock = pygame.time.Clock()
    tile_mgr = TileManager()
    ui_mgr = UIManager(screen)
    float_n = FloatingNumber(screen)
    i_menu = PauseMenu(screen)
    w_menu = WinMenu(screen)

    # draw bg once before menu
    tile_mgr.frame_update(screen)

    menu = True
    win_menu = False
    while True:
        """
        ----------------------------- MAIN GAME LOOP -----------------------------\n
        Everything that exists in this section is mainly for interscript 
        communication or player inputs
        """
        # check events first for player input
        for event in pygame.event.get():
            
            # event::click down
            if event.type == pygame.MOUSEBUTTONDOWN:
                
                # LClick
                if pygame.mouse.get_pressed()[0]:
                    click_coord = pygame.mouse.get_pos()
                    value_clicked = 0
                    
                    
                    # UI menu click
                    if click_coord[0] > BOARD_SIZE_PIXELS[0] + 1:
                        
                        # set active button
                        ui_mgr.button_check(click_coord)
                        
                        # if there is an active button
                        if ui_mgr.active_button != None:
                            
                            # if button was upgrade button
                            if ui_mgr.active_button.is_upgrade:
                                
                                # if can purchase
                                old_cost = float(ui_mgr.active_button.cost)
                                if float(ui_mgr.coins.get_inner_attr("coins")) > old_cost:
                                    # deduct cost and double cost of button
                                    ui_mgr.update_coins(-old_cost)
                                    ui_mgr.active_button.double_cost()
                                    
                                    # rpg number
                                    float_n.create_number((1200, 400), -old_cost)
                                    
                                    # send to tile for upgrade and deselect
                                    win_menu = tile_mgr.upgrade_button(ui_mgr.active_button)
                                    ui_mgr.button_check((0, 0))
                                
                                # can't purchase
                                else:
                                    float_n.create_number((1200, 400), "Can't afford")
                                    ui_mgr.button_check((0, 0))
                        
                        
                    # Tile click
                    elif click_coord[0] < BOARD_SIZE_PIXELS[0] - 1:
                        value_clicked = tile_mgr.click_event_value(
                            click_coord, 
                            ui_mgr.coins.get_inner_attr("coins"), 
                            ui_mgr.active_button
                        )
                    
                        # floating rpg number
                        float_n.create_number(click_coord, value_clicked)
                            
                        # is int
                        if isinstance(value_clicked, int):
                            ui_mgr.update_coins(value_clicked)
                            ui_mgr.refresh_button()
                    
                
                # RClick
                elif pygame.mouse.get_pressed()[2]:
                    
                    # deselect
                    ui_mgr.button_check((0, 0))
            
            # event::keyboard
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    
                    # deselect UI buttons
                    ui_mgr.button_check((0, 0))
                    
                    # flip menu bool
                    menu = bool(1 - menu)
                    
                    # if win menu, take down
                    if win_menu:
                        win_menu = False
                        menu = False
                    
            # event::quit
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        

        # calculate machine profits for this frame
        queue = tile_mgr.queued_val_arr
        if queue != []:
            # not empty
            for q in queue:
                float_n.create_number(q["coord"], q["val"])
                ui_mgr.update_coins(q["val"])
                queue.remove(q)


        # frame refresh updates
        if not menu and not win_menu:
            # regular frame updates
            tile_mgr.frame_update(screen)
            float_n.draw_all_floaters()
            
            # update money per second
            sma = float_n.calc_sma()
            ui_mgr.update_mps(sma)
        elif menu:
            # pause menu
            i_menu.draw_menu()
        elif win_menu:
            # win menu
            w_menu.draw_menu()
        
        
        
        # dynamic fps cuts expensive renders in fractions if fps drops too low
        # this doesn't help output render, but it does help player input lag
        curr_fps = clock.get_fps()
        render_every = Tile.dynamic_render # this number should go up for better performance
        if curr_fps < 16.0:
            # too low, render_every goes up
            render_every = min(render_every + 1, 3) # max every 3
        elif curr_fps > 28:
            # maintaining good, render goes down
            render_every = max(render_every - 1, 1) # min every frame
        
        Tile.dynamic_render = render_every
        pygame.display.update()
        
        
        # max fps
        clock.tick(30)

if __name__ == "__main__":
    main()