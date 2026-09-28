# FlyIntel

FlyIntel is an adaptive path planning system for UAVs that focuses on making flight paths more energy efficient.

The idea is to choose a suitable path based not only on distance, but also on factors such as wind conditions, temperature, payload and battery condition. The project combines data analysis and machine learning to study how these factors can affect UAV energy consumption.

## What the project does

- Processes UAV flight and battery data
- Analyzes battery discharge and energy consumption
- Considers environmental conditions such as wind and temperature
- Estimates the energy required for different flight conditions
- Uses machine learning to identify patterns in the collected data
- Provides an energy-aware approach to UAV path planning

## Dataset

The dataset used in the project contains battery discharge and flight-related parameters such as:

- Time
- Cell voltage
- Current
- Charge/discharge energy
- Discharged capacity
- Temperature
- Cycle number
- Number of cells
- Wind speed

Some environmental parameters such as wind speed are also included for studying their effect on UAV energy consumption.

## Project Structure

```text
FlyIntel/
│
├── battery_model/
│   └── Battery model related files
│
├── astar_planner.py
├── check_scaler.py
├── flyintel_dashboard.py
├── inspect_model.py
├── requirements.txt
└── README.md
