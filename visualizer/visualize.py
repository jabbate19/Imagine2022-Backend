import pygame
from argparse import ArgumentParser
import os
import json

UPDATE = pygame.USEREVENT + 1

class Visualizer:
    def __init__(self, data: list[tuple]):
        self.data = data
        self.index = 0
    def tick(self) -> tuple:
        dat = self.data[self.index]
        self.index += 1
        return dat

def parse_data(data: dict) -> list[tuple]:
    """
    Parses data into sorted tuple dict
    :data dict read from test data JSON
    -> list of (timestamp, data{})
    """
    return list(sorted([(int(k), v) for k, v in data.items()], key=lambda t: int(t[0])))

def render(item: tuple, esps: dict) -> pygame.Surface:
    """
    Renders frame from item
    :item item from parse_data list
    :esps dict of ESP positions
    -> pygame Surface
    """
    surf: pygame.Surface = pygame.Surface([800, 800])
    surf.fill([255,255,255])
    for e, p in esps.items():
        pygame.draw.circle(surf, [0, 255, 0], p, 8)
        for ue in item[1][e]:
            pygame.draw.circle(surf, [255, 0, 0], ue["pos"], 4)
            pygame.draw.line(surf, [0,0,0], p, ue["pos"], width = 2)
    
    return surf



def visualize(data: list[tuple], esps: dict, fps: int):
    """
    Runs visualization
    :data data from parse_data()
    :esps dict of ESP positions
    :fps frames per second
    """
    display: pygame.Surface = pygame.display.set_mode((800, 800))
    state: Visualizer = Visualizer(data)
    pygame.time.set_timer(UPDATE, int(1000 * (1 / fps)), loops = len(data) - 1)
    running = True
    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
                break
            if e.type == UPDATE:
                display.blit(render(state.tick(), esps), [0,0])
                pygame.display.flip()
    pygame.display.quit()
    pygame.quit()


if __name__ == "__main__":
    # Load preferences & test data path from args
    parser: ArgumentParser = ArgumentParser(prog="ImagineRIT 2022 Data Visualizer", description="Visualizes ImagineRIT 2022 test data")
    parser.add_argument("file", help="Path to JSON test data file")
    parser.add_argument("--fps", help="Animation fps", type=int, default=1)
    args = parser.parse_args()

    # Load test data
    print(f"Loading test data from {args.file}")
    if os.path.exists(args.file):
        with open(args.file, "r") as f:
            data: dict = json.load(f)
    else:
        raise FileNotFoundError(f"Could not locate test data file {args.file}")
    
    print("Sorting data to eliminate dictionary disorder.")
    esps: dict = data["esps"]
    data: list[tuple] = parse_data(data["data"])
    
    print(f"""===
Test Data Parameters:
    Time blocks: {len(data)}
    Time interval: {int(data[1][0]) - int(data[0][0])} seconds
    Estimated simulation time: {len(data) // args.fps} seconds
    Number of ESPs: {len(data[0][1].keys())}
===""")

    input("Begin visualization?")
    visualize(data, esps, args.fps)
