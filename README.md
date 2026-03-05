# clifc (CLI Footbal Club)

A C++ CLI tool that fetches today's soccer matches for Europe's Top 5 leagues from [football-data.org](https://www.football-data.org/) and displays them in your local timezone, grouped by league.

## Prerequisites

1.  **C++ Compiler**: A C++17 compatible compiler (e.g., `g++`, `clang++`, or MSVC).
2.  **CMake**: Version 3.14 or higher.
3.  **API Key**: Get a free API key from [football-data.org](https://www.football-data.org/).

## Dependencies

The project uses CMake's `FetchContent` to automatically download and link:
*   [cpr](https://github.com/libcpr/cpr) (C++ Requests for HTTP)
*   [nlohmann/json](https://github.com/nlohmann/json) (JSON Parsing for C++)

## Building the Project

1.  **Clone or create the directory structure**:
    Ensure `CMakeLists.txt` and `src/main.cpp` are in the project folder.

2.  **Generate the Build System**:
    ```bash
    mkdir build && cd build
    cmake ..
    ```

3.  **Compile the Code**:
    ```bash
    cmake --build .
    ```

## Running the Application

1.  **Set your API Key** as an environment variable:
    *   **Linux/macOS**:
        ```bash
        export FOOTBALL_API_KEY="your_api_key_here"
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        $env:FOOTBALL_API_KEY="your_api_key_here"
        ```

2.  **Execute the CLI**:
    ```bash
    ./clifc  # On Linux/macOS
    .\Debug\clifc.exe # On Windows
    ```

## Sample Output

```
⚽ Today's Top 5 League Matches ⚽
=================================

🏆 Premier League
-----------------------
[15:00] Arsenal FC vs Chelsea FC
[17:30] Manchester City FC vs Liverpool FC

🏆 La Liga
-----------------------
[20:00] Real Madrid CF vs FC Barcelona
```
