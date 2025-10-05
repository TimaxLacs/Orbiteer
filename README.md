# Orbiteer

A Financial Risk Assessment Tool for Space Missions, developed for the NASA Space Apps Challenge.

Orbiteer provides an interactive visualization for calculating the expected financial loss and estimated insurance premiums for satellite missions. The tool allows users to adjust mission parameters or input real-world satellite data to see how orbital risks translate into financial metrics.

## Project Structure

-   `/visual`: Contains the core of the project — a standalone `index.html` file that includes all the necessary HTML, CSS, and JavaScript for the interactive simulation. No server or build process is required.

## Data & Methodology

The core of our mathematical model is designed to work with real-world orbital data provided by NASA and NORAD in the **TLE (Two-Line Element set)** format.

The simulation includes a JavaScript-based TLE parser that can analyze standard two-line elements for any cataloged space object. When TLE data is provided, the tool automatically extracts key orbital parameters (like inclination and mean motion) and calculates the satellite's altitude to feed into our risk assessment model.

This ensures that our financial calculations are grounded in the principles of celestial mechanics and based on the same data formats used by NASA.

To validate the principles and for further development with other NASA datasets, the following API key can be used: `h7EU48c5uABbPKZz76DVoT0lsbF9PUPEpS1Ocfzl`.

## How to Use

1.  Clone the repository.
2.  Open the file `Orbiteer/visual/index.html` in any modern web browser.
