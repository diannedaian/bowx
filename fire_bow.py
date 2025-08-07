import time
import csv
import serial
import serial.tools.list_ports
from pynput.mouse import Controller, Button
import pygame
import threading
import sys

# Initialize pygame
pygame.init()

arduino = True
mouse = Controller()

# === PARAMETERS ===
SERIAL_PORT = '/dev/cu.usbserial-110'
BAUD_RATE = 115200
TRIGGER_THRESHOLD = 4000
DEBOUNCE_TIME = 0.2

last_trigger_time = 0
is_mouse_pressed = False
current_value = 0
bow_status = "idle"  # idle, pulled_back, released

# === PYGAME WINDOW SETUP ===
WIDTH, HEIGHT = 300, 200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bow Status")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Fonts
font_large = pygame.font.Font(None, 32)
font_small = pygame.font.Font(None, 24)

def draw_mouse_icon(surface, x, y, right_clicked=False):
    """Draw a simple mouse icon"""
    # Mouse body
    pygame.draw.ellipse(surface, GRAY, (x, y, 80, 120))
    pygame.draw.ellipse(surface, BLACK, (x, y, 80, 120), 3)

    # Mouse buttons
    # Left button
    pygame.draw.arc(surface, BLACK, (x+5, y+5, 30, 40), 0, 3.14, 3)

    # Right button - highlight if clicked
    button_color = RED if right_clicked else BLACK
    pygame.draw.arc(surface, button_color, (x+45, y+5, 30, 40), 0, 3.14, 3)
    if right_clicked:
        pygame.draw.arc(surface, button_color, (x+47, y+7, 26, 36), 0, 3.14, 5)

    # Scroll wheel
    pygame.draw.ellipse(surface, BLACK, (x+35, y+20, 10, 25))

def draw_status():
    """Draw the current bow status"""
    screen.fill(WHITE)

    # Status text
    if bow_status == "idle":
        status_text = "IDLE"
        status_color = GRAY
    elif bow_status == "pulled_back":
        status_text = "BOW PULLED BACK"
        status_color = BLUE
    elif bow_status == "released":
        status_text = "BOW RELEASED"
        status_color = GREEN

    # Draw status text
    text_surface = font_large.render(status_text, True, status_color)
    text_rect = text_surface.get_rect(center=(WIDTH//2, 30))
    screen.blit(text_surface, text_rect)

    # Draw current value
    value_text = f"Value: {current_value:.0f}"
    value_surface = font_small.render(value_text, True, BLACK)
    value_rect = value_surface.get_rect(center=(WIDTH//2, 60))
    screen.blit(value_surface, value_rect)

    # Draw mouse icon
    draw_mouse_icon(screen, WIDTH//2 - 40, 90, is_mouse_pressed)

    # Draw right click indicator
    if is_mouse_pressed:
        click_text = "RIGHT CLICK ACTIVE"
        click_surface = font_small.render(click_text, True, RED)
        click_rect = click_surface.get_rect(center=(WIDTH//2, 170))
        screen.blit(click_surface, click_rect)

    pygame.display.flip()

def run_serial_loop():
    global last_trigger_time, is_mouse_pressed, current_value, bow_status

    if arduino:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print("Found port:", port.device)

        try:
            f = open("data.csv", "w", newline='')
            writer = csv.writer(f)

            serialCom = serial.Serial(SERIAL_PORT, BAUD_RATE)
            serialCom.dtr = False
            time.sleep(1)
            serialCom.reset_input_buffer()
            serialCom.dtr = True

            print("Waiting for data from ESP32...")

            while True:
                try:
                    line = serialCom.readline().decode('utf-8').strip()
                    if line == "":
                        continue

                    parts = line.split(',')
                    values = [float(p) for p in parts]
                    writer.writerow(values)
                    f.flush()

                    if len(values) >= 3:
                        val = max(values[0], values[1], values[2])
                        current_value = val
                        current_time = time.time()

                        # Update bow status based on value
                        if val > TRIGGER_THRESHOLD * 0.8:
                            bow_status = "pulled_back"
                        else:
                            bow_status = "idle"

                        # PRESS right mouse if above threshold
                        if val > TRIGGER_THRESHOLD and not is_mouse_pressed:
                            print(f"🏹 Firing bow! value={val}")
                            mouse.press(Button.right)  # RIGHT MOUSE BUTTON
                            is_mouse_pressed = True
                            bow_status = "released"
                            last_trigger_time = current_time

                        # RELEASE right mouse if below threshold
                        elif val <= TRIGGER_THRESHOLD and is_mouse_pressed:
                            print(f"📤 Releasing bow! value={val}")
                            mouse.release(Button.right)  # RIGHT MOUSE BUTTON
                            is_mouse_pressed = False
                            bow_status = "idle"

                except Exception as e:
                    print("Serial error:", e)
                    continue

        except Exception as e:
            print("Setup error:", e)

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # Start serial thread
    serial_thread = threading.Thread(target=run_serial_loop, daemon=True)
    serial_thread.start()

    # Main pygame loop
    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            draw_status()
            clock.tick(30)  # 30 FPS

    except KeyboardInterrupt:
        print("\nShutting down...")

    finally:
        if is_mouse_pressed:
            mouse.release(Button.right)
        pygame.quit()
        sys.exit()
