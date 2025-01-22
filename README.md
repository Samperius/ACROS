# ACROS
Automated Reaction Optimization Software (ACROS) provides Graphical User Interface for optimization of reaction conditions and controlling an OpenTrons pipetting robot

## Installation
1. Install the latest version of Python
2. Create new virtual environment with command: python -m venv "path to the folder"
3. Activate teh virtual environment with command: source \'path to the folder'\bin\activate
4. install dependencies:
   - pip install openpyxl==3.1.5
   - pip install ax-platform==0.4.3
5. Move to the src_prod folder in terminal and run the program with command: python ui_prod.py
## Usage
1. Specify reaction parameters using 'reaction_parameters_template.xlsx' and current experiments using 'experiment_template.xlsx'
2. Set the file paths to 'settings.xlsx'
3. Launch the Software in terminal using command: python ui.py

