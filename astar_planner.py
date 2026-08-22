from queue import PriorityQueue

# ==========================================================
# FlyIntel A* Emergency Route Planner
# ==========================================================

# Grid Size

GRID_SIZE = 20

# No-Fly Zones / Obstacles

obstacles = {
    (5, 5), (5, 6), (5, 7),
    (6, 7), (7, 7),

    (10, 10), (10, 11), (10, 12),
    (11, 10), (12, 10),

    (15, 15), (15, 16), (16, 15)
}


# ==========================================================
# Heuristic Function (Manhattan Distance)
# ==========================================================

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ==========================================================
# Get Valid Neighbours
# ==========================================================

def get_neighbors(node):

    x, y = node

    neighbors = [
        (x + 1, y),   # Down
        (x - 1, y),   # Up
        (x, y + 1),   # Right
        (x, y - 1)    # Left
    ]

    valid_neighbors = []

    for nx, ny in neighbors:

        # Check grid boundaries

        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:

            # Ignore obstacles

            if (nx, ny) not in obstacles:
                valid_neighbors.append((nx, ny))

    return valid_neighbors


# ==========================================================
# A* Search Algorithm
# ==========================================================

def astar(start, goal):

    open_set = PriorityQueue()
    open_set.put((0, start))

    came_from = {}

    g_score = {start: 0}

    while not open_set.empty():

        current = open_set.get()[1]

        # Goal Reached

        if current == goal:

            path = []

            while current in came_from:
                path.append(current)
                current = came_from[current]

            path.append(start)
            path.reverse()

            return path

        # Explore Neighbours

        for neighbor in get_neighbors(current):

            tentative_g = g_score[current] + 1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:

                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                f_score = tentative_g + heuristic(neighbor, goal)

                open_set.put((f_score, neighbor))

    # No route found

    return None


# ==========================================================
# Local Test
# ==========================================================

if __name__ == "__main__":

    start = (2, 3)
    goal = (18, 18)

    path = astar(start, goal)

    print("\nEmergency Route:\n")

    if path:
        print(path)
    else:
        print("No route found.")