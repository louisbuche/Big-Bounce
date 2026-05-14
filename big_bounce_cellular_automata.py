import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

# --- Parameters ---
GRID_SIZE = 100
COOLING_RATE = 0.5
EXPANSION_PROB = 0.8
MAX_HEAT = 7500
MIN_LIMIT = 15
grid = np.zeros((GRID_SIZE, GRID_SIZE))

# Initial State
center = GRID_SIZE // 2
grid[center-1:center+2, center-1:center+2] = MAX_HEAT

class Universe:
    def __init__(self):
        self.phase = "EXPAND" # "EXPAND" or "CRUNCH"
        self.center_heat = MAX_HEAT
        self.scale_factor = 1
        self.num_cells2 = np.count_nonzero(grid)
        self.cooling_rate = COOLING_RATE
        self.expansion_prob = EXPANSION_PROB

    def update(self, grid):
        new_grid = grid.copy()

        # Phase Switching Logic
        if self.expansion_prob == 0:
            self.phase = "CRUNCH"
            self.expansion_prob = EXPANSION_PROB
            for k in range(GRID_SIZE):
                new_grid[k, 0] = 0
                new_grid[k, GRID_SIZE-1] = 0
                new_grid[0, k] = 0
                new_grid[GRID_SIZE-1, k] = 0
                grid[:] = new_grid[:]
            self.num_cells2 = np.count_nonzero(grid)

        if self.phase == "CRUNCH" and self.center_heat >= MAX_HEAT and self.num_cells2 == 1:
            # The "Bounce": Reset to Bang
            self.phase = "EXPAND"
            new_grid[center-1:center+2, center-1:center+2] = MAX_HEAT
            grid[:] = new_grid[:]
            self.num_cells2 = np.count_nonzero(grid)
            return new_grid

        # Physics Rules
        self.num_cells1 = self.num_cells2
        for y in range(1, GRID_SIZE - 1):
            for x in range(1, GRID_SIZE - 1):
                heat = grid[y, x]

                if self.phase == "EXPAND":
                    # Expansion rule : 0 is an absence of any voxel, 10 a voxel in an absolute 0 state
                    if heat >=10:
                        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                            if np.random.random() < EXPANSION_PROB:
                                if new_grid[y+dy, x+dx] == 0:
                                    new_grid[y+dy, x+dx] = max(10, heat - 50)
                                    self.num_cells2 += 1

                    # Heat transfer between existing voxels
                    if heat >= 10:
                        new_grid[y, x] = new_grid[y, x] + 0.0001*(4*(grid[y+1,x]+grid[y-1,x]+grid[y,x+1]+grid[y,x-1]) + grid[y+1,x+1]+grid[y+1,x-1]+grid[y-1,x-1]+grid[y-1,x+1])

                    # Cooling rule due to expansion
                    if heat > 0:
                        new_grid[y, x] = max(10, new_grid[y, x]*self.cooling_rate)

                    # Thermal noise
                    if new_grid[y,x] >= 10 and new_grid[y,x] <= 15:
                        new_grid[y,x] = 10 + 5*np.random.random()

                else:
                    if heat > 0:
                        # Movement toward center
                        vy = 1 if y < center else -1 if y > center else 0
                        vx = 1 if x < center else -1 if x > center else 0
                        # Gravity makes voxels drift toward center : space collapses
                        if grid[y+vy, x+vx] == 0 and y+vy != center and x+vx != center:
                            new_grid[y,x] = 0

                        elif (x != center) and (y != center):
                            if np.random.random() < 0.4:
                                new_grid[y+vy, x+vx] = max(new_grid[y+vy, x+vx], heat + 50)
                                if grid[y-vy, x-vx] == 0:
                                    new_grid[y, x] = 0
                        elif (x == center) and (y == center):
                            new_grid[y+vy, x+vx] = max(new_grid[y+vy, x+vx], heat + 1*10**(GRID_SIZE-2))
                        else:
                            new_grid[y+vy, x+vx] = min(new_grid[y+vy, x+vx], heat + 50)
                            if grid[y-vy, x-vx] == 0:
                                new_grid[y, x] = 0

        if self.phase == "EXPAND":
            # Update scale factor and cooling rate
            self.scale_factor = np.sqrt(self.num_cells2 / self.num_cells1)
            self.cooling_rate = 1/(self.scale_factor**2)
            if self.center_heat <= MIN_LIMIT:
                # expansion decelerates
                self.expansion_prob = max(0, self.expansion_prob - 0.01)
            else:
                # expansion accelerates
                self.expansion_prob = min(1, self.expansion_prob + 0.01)

        if self.phase == "CRUNCH":
            self.num_cells2 = np.count_nonzero(new_grid)


        self.center_heat = new_grid[center, center]
        grid[:] = new_grid[:]
        return new_grid



# --- Configuration de la page ---
st.set_page_config(page_title="Simulation Big Bounce", layout="centered")
st.title("Automate Cellulaire : Big Bounce")


# --- Initialisation de l'état ---
if 'grid' not in st.session_state:
    st.session_state.grid = np.zeros((GRID_SIZE, GRID_SIZE))
    center = GRID_SIZE // 2
    st.session_state.grid[center-1:center+2, center-1:center+2] = MAX_HEAT

# --- Interface de contrôle ---
col1, col2 = st.columns(2)
start_button = col1.button("Démarrer / Reprendre")
stop_button = col2.button("Pause")

# Placeholder pour l'image
frame_text = st.empty()
image_placeholder = st.empty()

if start_button:
    u = Universe()
    current_grid = st.session_state.grid

    while True:
        # 1. Calculer l'étape suivante
        current_grid = u.update(current_grid)
        st.session_state.grid = current_grid

        # 2. Créer la figure Matplotlib
        fig, ax = plt.subplots(figsize=(6,6))
        ax.imshow(current_grid, cmap='inferno', vmin=0, vmax=MAX_HEAT)
        ax.axis('off')

        # 3. Afficher dans Streamlit
        image_placeholder.pyplot(fig)
        plt.close(fig) # Important pour éviter les fuites de mémoire

        time.sleep(0.01) # Petit délai pour laisser le navigateur respirer