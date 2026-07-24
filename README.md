*This project has been created as part of the 42 curriculum by tiana-an*

# Fly-in

> "Drones are interesting"

## Description:

Fly-in simulates the coordinated movement of multiple drones through interconnected zones. The objective is to compute efficient routes that minimize the number of simulation turns while enforcing movement rules: drones can only travel through directly connected zones, every move must satisfy the simulation constraints, and the routing algorithm must coordinate all drones to avoid conflicts and deliver each one to its destination as efficiently as possible.

Working on this project helped me become familiar with Pygame, improve my problem-solving skills, and learn how to coordinate multiple entities simultaneously using efficient pathfinding algorithms.

### How it works?

---
- Map parsing:

    The program reads the map file, validates its content, and builds the simulation data by creating all zones, connections, and configuration
    settings (number of drones, start zone, destination, capacities, and zone types).

---

- Path planning:

    A space-time pathfinding algorithm computes a route for each drone. It uses a global reservation system to prevent conflicts by considering both the map layout and the simulation turn at every movement. Drones can wait, take alternative routes, or handle restricted zones according to the project rules while minimizing the total number of turns.

---

- Simulation:

    Once every path is calculated, the simulator executes the planned movements turn by turn and generates the required output logs, describing each drone's position or transit at every simulation step.

---

- Visualization:

    Pygame animates the simulation by loading the map, automatically fitting it to the window, and replaying the generated logs. Drones move smoothly between zones, including intermediate transitions through restricted areas, while the interface updates in real time and allows basic camera controls.

---

- input example (map_file):

```
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

- Output example:

```bash
D1-corridorA D2-hub-roof1
D1-tunnelB D2-roof1 D3-corridorA D4-hub-roof1
D1-goal D2-roof2 D3-tunnelB D4-roof1 D5-corridorA
D2-goal D3-goal D4-roof2 D5-tunnelB
D4-goal D5-goal

Total turns: 5
```
Each movement follow the format: `D<ID>-<zone>`, or `D<ID>-<connection>` in case of drones still in flight toward restricted zones


## Instructions:

### Makefile

Makefile automates project setup, execution, debugging, cleanup, and code quality checks (Flake8 and MyPy), with an optional strict linting target.

```bash
make install       # Install project dependencies
make run           # Run the main program
make visual        # Run the program's visual (visual output only)
make text_output   # Run the program's simulation (text output only)
make debug         # Run the program with Python debugger (pdb)
make clean         # Remove temporary files and caches
make lint          # Run Flake8 and MyPy with required checking flags
make lint-strict   # Run Flake8 and MyPy in strict mode
```

You can also run the program directly using:

```bash
uv run main.py config.txt # example as <config_file>
```

And you can specify the mode:

```bash
uv run main.py config.txt visual
```

Replace `config.txt` with another configuration file if desired.

## Resources:

Helpful resources used while implementing algorithms:

* [BFS](https://www.geeksforgeeks.org/dsa/breadth-first-search-or-bfs-for-a-graph/)

* [pygame](https://www.youtube.com/watch?v=8J8wWxbAdFg&list=PLMS9Cy4Enq5KsM7GJ4LHnlBQKTQBV8kaR)

> ***AI usage***

AI tools helped me solve specific bugs, better understand some algorithms, and learn more about Pygame concepts during the development process. They were used as a support tool for debugging, research, and improving my technical understanding, but all solutions were analyzed, understood, and implemented by me.

## Algorithm choice:

Breadth-First Search (BFS) was chosen as the core pathfinding algorithm because it explores states in increasing order of time steps. Therefore, the first valid path found corresponds to the minimum number of simulation turns under the given constraints.

To handle the temporal and resource constraints of the project, the algorithm was extended into a space-time BFS. Instead of exploring only spatial positions, the search operates on a state space where each state represents a complete drone situation: `(zone, turn, visited_zones)`. This allows the algorithm to consider not only possible movements between zones, but also waiting actions, zone capacities, link capacities, restricted zones, and previously visited areas.

A global reservation system manages the occupation of zones and connections over time, preventing conflicts between drones. Paths are planned sequentially: after finding a valid path for a drone, its reservations are added to the system before computing the next drone's route. This produces coordinated, collision-free paths while minimizing the total number of simulation turns.
