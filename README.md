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
nb_drones: 2
# nb_drones: 5


start_hub: start 0 0 [color=magenta]
end_hub: goal 6 0 [color=gold zone=restricted color=gold]

hub: priority 1 2 [zone=priority color=green]
hub: not_priority 1 -2 [zone=normal color=grey]

hub: a 3 0 [max_drones=2 color=darkgrey zone=normal]
hub: b 3 1
hub: c 5 1

hub: blocked 5 -1 [zone=blocked color=red]


connection: start-priority
connection: start-not_priority

connection: priority-a [max_link_capacity=2]
connection: not_priority-a [max_link_capacity=2]

connection: a-goal
connection: a-b
connection: a-blocked
connection: blocked-goal [max_link_capacity=2]
connection: b-c
connection: c-goal
```

- Output example:



## Instructions:

### Makefile

Makefile automates project setup, execution, debugging, cleanup, and code quality checks (Flake8 and MyPy), with an optional strict linting target.

```bash
make install       # Install project dependencies
make run           # Run the main program
make debug         # Run the program with Python debugger (pdb)
make clean         # Remove temporary files and caches
make lint          # Run Flake8 and MyPy with required checking flags
make lint-strict   # Run Flake8 and MyPy in strict mode
```

You can also run the program directly using:

```bash
uv run main.py config.txt  # example as <config_file>
```
Replace `config.txt` with another configuration file if desired.

## Resources:

Helpful resources used while implementing algorithms:

* [BFS](https://www.geeksforgeeks.org/dsa/breadth-first-search-or-bfs-for-a-graph/)

* [pygame](https://www.youtube.com/watch?v=8J8wWxbAdFg&list=PLMS9Cy4Enq5KsM7GJ4LHnlBQKTQBV8kaR)

> ***AI usage***

AI tools helped me solve specific bugs, better understand some algorithms, and learn more about Pygame concepts during the development process. They were used as a support tool for debugging, research, and improving my technical understanding, but all solutions were analyzed, understood, and implemented by me.

## Algorithm choice:

Breadth-First Search (BFS) was chosen as the core pathfinding algorithm because it guarantees the shortest path in an unweighted graph. To handle the project constraints, it was extended into a space-time BFS, where each state represents a (zone, turn) pair. This approach allows the algorithm to account for zone capacities, link capacities, waiting actions, and restricted zones while using a global reservation system to avoid conflicts between drones. Paths are computed sequentially, reserving space and time for each drone before planning the next one, ensuring efficient and collision-free routing.
