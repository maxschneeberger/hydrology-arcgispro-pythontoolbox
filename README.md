# Hydrology ArcGIS Pro Python Toolbox

This project is an ArcGIS Pro Python Toolbox that automates common hydrological analysis tasks. It leverages the `.pyt` format to offer advanced customization, flexible parameter validation, and seamless integration into ArcGIS Pro.

## Overview

The toolbox is designed to simplify and optimize hydrological processing workflows, which are typically repetitive and complex. Compared to `.atbx` toolboxes or Jupyter workflows within ArcGIS, a `.pyt` file provides a lightweight, script-based solution that remains fully integrated within the ArcGIS Pro environment.

## Features

The toolbox includes two main tools:

### 1. Bulk Hydro Analysis

- Automates the generation of multiple hydrological output rasters from an input DEM.  
- Offers user options to:  
  - Save outputs to a geodatabase or folder.  
  - Automatically add outputs to the current map.  

### 2. Optimized Watershed

- Extends ArcGIS Pro’s Spatial Analyst Watershed Tool.  
- Includes automated DEM preprocessing.  
- Optimizes pour point locations for better watershed delineation.  
- Simplifies the configuration of watershed input parameters.  

## Approach

- Acquired foundational knowledge from ArcGIS Pro Python Toolbox documentation.  
- Focused on hydrological tasks known to involve repetitive processing.  
- Developed in Visual Studio Code using a cloned ArcGIS Pro conda environment.  

## Getting Started

1. Clone the repository or download the toolbox.  
2. Open ArcGIS Pro and add the `.pyt` file as a toolbox.  
3. Follow the metadata instructions within each tool for parameter setup.  

## License
- 📜 MIT License — see [LICENSE](LICENSE)

