# Multi-Trace Visualizer

A user-friendly application for visualizing and comparing calcium imaging traces from different regions (soma, axons, etc.) of the same sample. This tool is designed to help neuroscientists and researchers analyze and compare activity measurements across multiple recordings.

## Features
- Load multiple Excel/CSV files with activity measurements
- Auto-detect segments and sides from column names
- Select multiple segments to visualize together
- Compare same segments from different recordings (e.g., soma vs axon)
- Multiple visualization options (overlay, stacked, normalization)
- Calculate mean traces and delta between segments
- Consistent color coding for better visualization
- Export visualizations as PDFs
- Logging for troubleshooting and debugging

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```
2. Install the required dependencies (Python 3.7+ recommended):
   ```bash
   pip install -r requirements.txt
   ```
   
   If you don't have a `requirements.txt`, make sure to install at least:
   - PyQt5
   - pandas
   - matplotlib

## Usage

Run the application with:
```bash
python main.py
```

Follow the on-screen instructions to load your data files and visualize traces.

## Logging

The application logs information and errors to both the console and a file named `multi_trace_vis.log` in the project directory. This can help with troubleshooting if you encounter any issues.

## Exporting Visualizations

You can export your visualizations as PDF files directly from the application interface.

## License

[Add your license here]

---

For questions or support, please contact the project maintainer. 