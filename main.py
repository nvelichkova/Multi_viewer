#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main script to run the improved Multi-Trace Visualizer application.

This is a simplified and more user-friendly version of the original network
visualization GUI, focused specifically on visualizing and comparing calcium 
imaging traces from different regions (soma, axons, etc.) of the same sample.

Features:
- Load multiple Excel/CSV files with activity measurements
- Auto-detect segments and sides from column names
- Select multiple segments to visualize together
- Compare same segments from different recordings (e.g., soma vs axon)
- Multiple visualization options (overlay, stacked, normalization)
- Calculate mean traces and delta between segments
- Consistent color coding for better visualization
- Export visualizations as PDFs

Usage:
    python main.py
"""


"""
Debug version of the Multi-Trace Visualizer with extra logging for troubleshooting.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from multi_trace_visualizer import MultiTraceVisualizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multi_trace_vis.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("MultiTraceVis")

if __name__ == "__main__":
    logger.info("Starting Multi-Trace Visualizer...")
    
    # Create application
    app = QApplication(sys.argv)
    
    try:
        # Create and show main window
        logger.info("Creating main window...")
        window = MultiTraceVisualizer()
        window.show()
        
        logger.info("Application started successfully.")
        
        # Start event loop
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}", exc_info=True)
        raise