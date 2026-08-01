import sys
import argparse
import pygame

from binary_house.core.door import ToggleDigit
from binary_house.world.world import generate_world
from binary_house.game.state import GameState
from binary_house.game.player import MoveAction
from binary_house.ui.renderer import Renderer
from binary_house.ui.tutorial import TutorialState

def main():
    parser = argparse.ArgumentParser(description="The House That Remembers: 2-adic ultrametric stealth puzzle prototype")
    parser.add_argument("--depth", type=int, default=4, help="Address bit depth: 4 (16 rooms, M1 tutorial), 6 (64 rooms), 8 (256 rooms)")
    parser.add_argument("--seed", type=int, default=42, help="World generation seed")
    parser.add_argument("--no-caretaker", action="store_true", help="Disable enemy for learning mode")
    parser.add_argument("--debug", action="store_true", help="Start directly in F2 Mathematical Debug View")
    parser.add_argument("--tutorial", action="store_true", help="Enable step-by-step onboarding sequence")
    args = parser.parse_args()

    pygame.init()
    surface = pygame.display.set_mode((1084, 648))
    pygame.display.set_caption("The House That Remembers (The Binary House)")
    clock = pygame.time.Clock()

    def reset_game() -> GameState:
        world = generate_world(depth=args.depth, seed=args.seed)
        enable_caretaker = not args.no_caretaker and (args.depth > 4)
        return GameState.create(world=world, enable_caretaker=enable_caretaker)

    state = reset_game()
    view_mode = "debug" if args.debug else "diegetic"
    renderer = Renderer(surface, view_mode=view_mode)
    tutorial = TutorialState() if args.tutorial else None

    running = True
    hovered_digit = None

    print(f"Started The House That Remembers ({1<<args.depth} rooms).")
    print("Controls: Click on a door, or press 0-7 keys. F1 = Archivist View | F2 = Math Debug View | R = Restart")

    while running:
        dt_ms = clock.tick(30)
        renderer.update_transition(dt_ms)
        
        door_rects, overlay_buttons = renderer.render(state, hovered_digit=hovered_digit)

        # Check mouse hover on door rects
        mouse_pos = pygame.mouse.get_pos()
        hovered_digit = None
        for rect, digit_idx in door_rects:
            if rect.collidepoint(mouse_pos):
                hovered_digit = digit_idx
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 1. Check overlay buttons first
                clicked_overlay = False
                for btn_rect, btn_action in overlay_buttons:
                    if btn_rect.collidepoint(event.pos):
                        if btn_action == "restart":
                            state = reset_game()
                            if tutorial:
                                tutorial = TutorialState()
                        clicked_overlay = True
                        break

                if not clicked_overlay and state.phase in ("explore", "detected"):
                    for rect, digit_idx in door_rects:
                        if rect.collidepoint(event.pos):
                            door = ToggleDigit(digit_idx)
                            from_addr = state.player_address
                            to_addr = door.apply(from_addr)
                            
                            renderer.start_transition(from_addr, to_addr, digit_idx)
                            
                            turn_event = state.step(MoveAction(door))
                            if tutorial:
                                tutorial.advance(turn_event, state)
                            break

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state = reset_game()
                    if tutorial:
                        tutorial = TutorialState()
                elif event.key == pygame.K_F1:
                    renderer.toggle_archivist()
                elif event.key == pygame.K_F2:
                    renderer.toggle_debug()
                elif (pygame.K_0 <= event.key <= pygame.K_7) and state.phase in ("explore", "detected"):
                    digit_idx = event.key - pygame.K_0
                    if digit_idx < args.depth:
                        door = ToggleDigit(digit_idx)
                        from_addr = state.player_address
                        to_addr = door.apply(from_addr)
                        
                        renderer.start_transition(from_addr, to_addr, digit_idx)
                        
                        turn_event = state.step(MoveAction(door))
                        if tutorial:
                            tutorial.advance(turn_event, state)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
