import argparse
import math
import os
import sys
from typing import Dict, List, Optional
import pygame

from simulation.state import PendulumState, wrap_theta, energy
from simulation.integrator import rk4_step
from simulation.predictor import predict_trajectory
from game.level import ChamberLevel, load_chamber
from game.scoring import ScoreTracker
from game.replay import ReplayRecorder
from rendering.physical_view import PhysicalView
from rendering.phase_view import PhaseView
from rendering.ui import UIRenderer
from rendering.audio import AudioSynthesizer


def main():
    parser = argparse.ArgumentParser(description="Momentum Maze: Pendulum Vault")
    parser.add_argument(
        "--chamber",
        type=int,
        default=0,
        help="Chamber number to start (0 to 5)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Start with debug overlays enabled",
    )
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_caption("Momentum Maze: Pendulum Vault")

    WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
    screen = pygame.display.set_caption("Momentum Maze: Pendulum Vault")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # Layout regions
    HEADER_HEIGHT = 40
    STATUS_HEIGHT = 80
    VIEW_HEIGHT = WINDOW_HEIGHT - HEADER_HEIGHT - STATUS_HEIGHT
    VIEW_WIDTH = WINDOW_WIDTH // 2

    rect_physical = pygame.Rect(0, HEADER_HEIGHT, VIEW_WIDTH, VIEW_HEIGHT)
    rect_phase = pygame.Rect(VIEW_WIDTH, HEADER_HEIGHT, VIEW_WIDTH, VIEW_HEIGHT)
    rect_status = pygame.Rect(0, WINDOW_HEIGHT - STATUS_HEIGHT, WINDOW_WIDTH, STATUS_HEIGHT)

    physical_view = PhysicalView(rect_physical)
    phase_view = PhaseView(rect_phase)
    ui_renderer = UIRenderer(rect_status)
    audio = AudioSynthesizer()

    # Chambers list
    levels_dir = os.path.join(os.path.dirname(__file__), "levels")
    chamber_files = [
        os.path.join(levels_dir, f"chamber_0{i}.json") for i in range(6)
    ]

    current_chamber_idx = max(0, min(args.chamber, len(chamber_files) - 1))

    # App state variables
    chamber: ChamberLevel = load_chamber(chamber_files[current_chamber_idx])
    state: PendulumState = chamber.initial_state
    state_history: List[PendulumState] = [state]

    selected_torque: float = 0.0
    active_torque: float = 0.0

    is_executing_pulse: bool = False
    pulse_sim_timer: float = 0.0
    PULSE_DURATION: float = 0.35
    PHYSICS_DT: float = 1.0 / 240.0

    show_vectors: bool = True
    show_debug: bool = args.debug

    score_tracker = ScoreTracker()
    replay_recorder = ReplayRecorder(
        level_id=chamber.id,
        initial_theta=state.theta,
        initial_omega=state.omega,
    )

    running = True

    def reset_current_chamber():
        nonlocal chamber, state, state_history, selected_torque, active_torque
        nonlocal is_executing_pulse, pulse_sim_timer, score_tracker, replay_recorder

        chamber = load_chamber(chamber_files[current_chamber_idx])
        state = chamber.initial_state
        state_history = [state]
        selected_torque = 0.0
        active_torque = 0.0
        is_executing_pulse = False
        pulse_sim_timer = 0.0
        score_tracker.reset()
        replay_recorder = ReplayRecorder(
            level_id=chamber.id,
            initial_theta=state.theta,
            initial_omega=state.omega,
        )

    def generate_predictions() -> Dict[float, List[PendulumState]]:
        torque_options = [-0.35, 0.0, 0.35]
        preds = {}
        for t in torque_options:
            preds[t] = predict_trajectory(
                start_state=state,
                torque=t,
                params=chamber.parameters,
                pulse_duration=PULSE_DURATION,
                tail_duration=1.05,
                dt=PHYSICS_DT,
            )
        return preds

    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

                elif event.key == pygame.K_r:
                    reset_current_chamber()

                elif event.key == pygame.K_TAB:
                    show_vectors = not show_vectors

                elif event.key == pygame.K_F1:
                    show_debug = not show_debug

                # Chamber navigation
                elif event.key in (pygame.K_n, pygame.K_RIGHT) and (
                    chamber.objective_manager.is_completed
                    or not chamber.controls_enabled
                ):
                    if current_chamber_idx < len(chamber_files) - 1:
                        current_chamber_idx += 1
                        reset_current_chamber()

                elif event.key == pygame.K_p and current_chamber_idx > 0:
                    current_chamber_idx -= 1
                    reset_current_chamber()

                # Action Controls
                if chamber.controls_enabled and not is_executing_pulse and not chamber.objective_manager.is_completed and not chamber.objective_manager.is_failed:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        selected_torque = -0.35
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected_torque = 0.0
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        selected_torque = 0.35
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        # Commit selected pulse action
                        is_executing_pulse = True
                        active_torque = selected_torque
                        pulse_sim_timer = 0.0
                        audio.play_torque_pulse(active_torque)
                        score_tracker.record_pulse(active_torque, PULSE_DURATION)
                        replay_recorder.record_pulse(active_torque, score_tracker.elapsed_time)

        # 2. Physics Simulation Update
        if not chamber.objective_manager.is_completed and not chamber.objective_manager.is_failed:
            if chamber.controls_enabled:
                if is_executing_pulse:
                    # Run physics substeps for 1/60th of a second
                    substeps = int((1.0 / 60.0) / PHYSICS_DT)
                    for _ in range(substeps):
                        prev_state = state
                        state = rk4_step(state, active_torque, chamber.parameters, PHYSICS_DT)
                        state_history.append(state)
                        score_tracker.add_time(PHYSICS_DT)

                        pulse_sim_timer += PHYSICS_DT

                        # Detect separatrix crossing (E=2.0)
                        e_prev = energy(prev_state)
                        e_curr = energy(state)
                        if (e_prev < 2.0 <= e_curr) or (e_prev >= 2.0 > e_curr):
                            audio.play_separatrix_cross()

                        was_completed = chamber.objective_manager.is_completed
                        was_failed = chamber.objective_manager.is_failed
                        prev_idx = chamber.objective_manager.active_index

                        # Objective checking
                        chamber.objective_manager.check_step(
                            prev_state,
                            state,
                            score_tracker.total_pulses,
                            chamber.pulse_budget,
                        )

                        if chamber.objective_manager.active_index > prev_idx:
                            audio.play_gate_passed()

                        if not was_completed and chamber.objective_manager.is_completed:
                            audio.play_dock_success()
                        elif not was_failed and chamber.objective_manager.is_failed:
                            audio.play_hazard_failed()

                        if pulse_sim_timer >= PULSE_DURATION:
                            is_executing_pulse = False
                            active_torque = 0.0
                            break
            else:
                # Chamber 0: passive continuous simulation
                substeps = int((1.0 / 60.0) / PHYSICS_DT)
                for _ in range(substeps):
                    prev_state = state
                    state = rk4_step(state, 0.0, chamber.parameters, PHYSICS_DT)
                    state_history.append(state)
                    if len(state_history) > 600:
                        state_history.pop(0)

        # 3. Trajectory Predictions
        predictions = generate_predictions() if chamber.controls_enabled else {}

        # 4. Rendering
        screen.fill((10, 14, 22))

        # Top Header Bar
        header_font = pygame.font.SysFont("Verdana", 15, bold=True)
        header_text = header_font.render(
            f"{chamber.name.upper()}  |  Use [P/N] to Switch Chambers",
            True,
            (200, 220, 255),
        )
        screen.blit(header_text, (20, 10))

        # Draw Physical View
        physical_view.draw_background_and_ticks(screen)
        physical_view.draw_constraints(screen, chamber.constraints)
        physical_view.draw_afterimages(screen, state_history[-25:])
        physical_view.draw_pendulum(screen, state, active_torque if is_executing_pulse else 0.0)

        # Draw Phase View
        phase_view.draw_grid_and_axes(screen)
        if show_vectors:
            phase_view.vector_field.draw_vector_field(
                screen,
                phase_view.rect,
                chamber.parameters,
                torque=selected_torque,
            )
            phase_view.vector_field.draw_contours(screen, phase_view.rect)

        phase_view.draw_constraints(screen, chamber.constraints)
        phase_view.draw_trajectory_trail(screen, state_history[-80:])

        if predictions:
            phase_view.draw_candidate_predictions(screen, predictions, selected_torque)

        phase_view.draw_current_state(screen, state)

        # Draw HUD Status Bar
        ui_renderer.draw_status_bar(
            screen,
            state,
            selected_torque,
            score_tracker.total_pulses,
            chamber.pulse_budget,
            chamber.objective_manager.target_description,
            is_executing_pulse,
        )

        ui_renderer.draw_instructions(screen, WINDOW_WIDTH)

        # Draw Overlay Messages on End Conditions
        if chamber.objective_manager.is_completed:
            ui_renderer.draw_overlay_message(
                screen,
                "CHAMBER CLEARED!",
                f"Pulses: {score_tracker.powered_pulses}  |  Press [N / Right Arrow] for Next Chamber",
                is_success=True,
            )
        elif chamber.objective_manager.is_failed:
            ui_renderer.draw_overlay_message(
                screen,
                "CHAMBER FAILED",
                f"{chamber.objective_manager.status_message}  |  Press [R] to Restart",
                is_success=False,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
