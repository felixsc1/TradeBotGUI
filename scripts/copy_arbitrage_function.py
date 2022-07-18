import shutil
import os

# Select the folder of the statistical arbitrage repository:
repo_folder = "C:/GitRepos/StatisticalArbitrage"

streamlit_folder = "C:/GitRepos/TradeBotGUI"

shutil.copytree(os.path.join(repo_folder, 'Strategy'),
                os.path.join(streamlit_folder, 'scripts', 'Strategy'))
