# Convert deltavision files to png automatically
Author: Naly Torres

# Description
Repository to automatically download and convert deltavision files to png. This repository uses PySMB to access and transfer data between the Network-attached storage (NAS) and a local server (your computer). Microscope images (.dv) are then saved as png individually and as a pdf report with their README file.

# Code Architecture
<img width="883" alt="Screen Shot 2024-01-24 at 3 29 38 PM" src="https://github.com/TorresNaly/dv2png/assets/85882411/21142b9e-1d09-4506-9d6a-551ad2a71132">

# Installation
> [!TIP]
> Install [Anaconda](https://www.anaconda.com/) before installing this repository and all its dependencies.

* Create conda environment
```
conda create --name dv2png_env
```
* Activate conda environment
```
conda activate dv2png_env
```
* Intall packages
```
conda install pip
```
```
pip install big-fish
```
```
pip install jupyter lab
```
```
pip install pysmb
```
```
pip install fpdf
```
* Clone git repository. Make sure that you cd into the directory where you want to download these.
```
git clone --depth 1 https://github.com/TorresNaly/dv2png.git
```
#### Last edited March 31st, 2024. 



