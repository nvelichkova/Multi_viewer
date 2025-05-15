import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QComboBox, QCheckBox,
    QDoubleSpinBox, QListWidget, QAbstractItemView, QGroupBox, 
    QSplitter, QMessageBox, QRadioButton, QButtonGroup, QGridLayout
)
from PyQt5.QtCore import Qt

# Import our custom modules
from data_manager import DataManager
from plot_canvas import PlotCanvas

class MultiTraceVisualizer(QMainWindow):
    """Main window for the multi-trace visualizer application."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Trace Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # Create left panel for controls
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        
        # Create right panel for plot
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        
        # Add panels to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([400, 800])  # Initial sizes
        
        # Set up controls
        self._setup_controls()
        
        # Create plot canvas
        self.plot_canvas = PlotCanvas(self)
        self.right_layout.addWidget(self.plot_canvas)
        
        # Store segment selection state
        self.selected_segments = {}  # {segment_name: {'left': bool, 'right': bool}}
    
    def _setup_controls(self):
        """Set up control widgets in the left panel."""
        # File Management Group
        file_group = QGroupBox("File Management")
        file_layout = QVBoxLayout()
        
        # Load file button
        self.load_btn = QPushButton("Load Excel/CSV Files")
        self.load_btn.clicked.connect(self.load_files)
        file_layout.addWidget(self.load_btn)
        
        # Sampling frequency controls
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Sampling Rate:"))
        self.freq_input = QDoubleSpinBox()
        self.freq_input.setRange(0.1, 1000)
        self.freq_input.setDecimals(1)
        self.freq_input.setValue(5.0)  # Default 5 Hz
        self.freq_input.setSuffix(" Hz")
        self.freq_input.valueChanged.connect(self.on_sampling_freq_changed)
        freq_layout.addWidget(self.freq_input)
        file_layout.addLayout(freq_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.itemSelectionChanged.connect(self.update_segment_list)
        file_layout.addWidget(QLabel("Loaded Files:"))
        file_layout.addWidget(self.file_list)
        
        file_group.setLayout(file_layout)
        self.left_layout.addWidget(file_group)
        
        # Sample Selection Group
        sample_group = QGroupBox("Sample Selection")
        sample_layout = QVBoxLayout()
        
        # Replace sample dropdown with a sample list widget for multiple selection
        sample_layout.addWidget(QLabel("Select Samples:"))
        self.sample_list = QListWidget()
        self.sample_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.sample_list.itemSelectionChanged.connect(self.on_samples_selected)
        sample_layout.addWidget(self.sample_list)
        
        # Auto-select files checkbox
        self.auto_select_cb = QCheckBox("Auto-select files for selected samples")
        self.auto_select_cb.setChecked(True)
        self.auto_select_cb.stateChanged.connect(self.on_auto_select_changed)
        sample_layout.addWidget(self.auto_select_cb)
        
        sample_group.setLayout(sample_layout)
        self.left_layout.addWidget(sample_group)
        
        # Segment Selection Group
        segment_group = QGroupBox("Segment Selection")
        segment_layout = QVBoxLayout()
        
        # Segment list
        segment_layout.addWidget(QLabel("Available Segments:"))
        self.segment_list = QListWidget()
        self.segment_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.segment_list.itemSelectionChanged.connect(self.on_segments_selected)
        segment_layout.addWidget(self.segment_list)
        
        # Side selection
        side_layout = QHBoxLayout()
        side_layout.addWidget(QLabel("Show:"))
        
        # Create checkbox group for better UI
        self.side_both_cb = QCheckBox("Both Sides")
        self.side_left_cb = QCheckBox("Left Side")
        self.side_right_cb = QCheckBox("Right Side")
        
        self.side_both_cb.setChecked(True)
        self.side_left_cb.setChecked(False)
        self.side_right_cb.setChecked(False)
        
        # Connect side selection signals
        self.side_both_cb.stateChanged.connect(self.on_side_selection_changed)
        self.side_left_cb.stateChanged.connect(self.on_side_selection_changed)
        self.side_right_cb.stateChanged.connect(self.on_side_selection_changed)
        
        side_layout.addWidget(self.side_both_cb)
        side_layout.addWidget(self.side_left_cb)
        side_layout.addWidget(self.side_right_cb)
        
        segment_layout.addLayout(side_layout)
        
        # Calculate mean & delta checkbox
        calculation_layout = QHBoxLayout()
        self.show_mean_cb = QCheckBox("Show Mean")
        self.show_delta_cb = QCheckBox("Show Delta")
        
        self.show_mean_cb.stateChanged.connect(self.update_visualization)
        self.show_delta_cb.stateChanged.connect(self.update_visualization)
        
        calculation_layout.addWidget(self.show_mean_cb)
        calculation_layout.addWidget(self.show_delta_cb)
        
        segment_layout.addLayout(calculation_layout)
        
        segment_group.setLayout(segment_layout)
        self.left_layout.addWidget(segment_group)
        
        # Visualization Options Group
        vis_group = QGroupBox("Visualization Options")
        vis_layout = QVBoxLayout()
        
        # View mode
        view_layout = QHBoxLayout()
        view_layout.addWidget(QLabel("View Mode:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Overlay", "Stacked"])
        self.view_combo.currentIndexChanged.connect(self.update_visualization)
        view_layout.addWidget(self.view_combo)
        vis_layout.addLayout(view_layout)
        
        # Normalization
        norm_layout = QHBoxLayout()
        norm_layout.addWidget(QLabel("Normalization:"))
        self.norm_combo = QComboBox()
        self.norm_combo.addItems(["None", "Mean", "ΔF/F₀ (Baseline)"])
        self.norm_combo.currentIndexChanged.connect(self.on_normalization_changed)
        norm_layout.addWidget(self.norm_combo)
        vis_layout.addLayout(norm_layout)
        
        # Baseline parameters
        baseline_layout = QHBoxLayout()
        baseline_layout.addWidget(QLabel("Baseline:"))
        
        self.baseline_start = QDoubleSpinBox()
        self.baseline_start.setRange(0, 1000)
        self.baseline_start.setValue(0)
        self.baseline_start.setSuffix(" s")
        self.baseline_start.valueChanged.connect(self.update_visualization)
        baseline_layout.addWidget(QLabel("Start:"))
        baseline_layout.addWidget(self.baseline_start)
        
        self.baseline_duration = QDoubleSpinBox()
        self.baseline_duration.setRange(0.1, 1000)
        self.baseline_duration.setValue(10)
        self.baseline_duration.setSuffix(" s")
        self.baseline_duration.valueChanged.connect(self.update_visualization)
        baseline_layout.addWidget(QLabel("Duration:"))
        baseline_layout.addWidget(self.baseline_duration)
        
        vis_layout.addLayout(baseline_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Gaussian Filter:"))
        
        self.filter_sigma = QDoubleSpinBox()
        self.filter_sigma.setRange(0, 100)
        self.filter_sigma.setSingleStep(0.01)
        self.filter_sigma.setValue(0)
        self.filter_sigma.setSuffix(" %")
        filter_layout.addWidget(self.filter_sigma)
        
        self.apply_filter_btn = QPushButton("Apply")
        self.apply_filter_btn.clicked.connect(self.on_apply_filter)
        filter_layout.addWidget(self.apply_filter_btn)
        
        self.reset_filter_btn = QPushButton("Reset")
        self.reset_filter_btn.clicked.connect(self.on_reset_filter)
        filter_layout.addWidget(self.reset_filter_btn)
        
        vis_layout.addLayout(filter_layout)
        
        # Export
        self.export_btn = QPushButton("Export as PDF")
        self.export_btn.clicked.connect(self.export_figure)
        vis_layout.addWidget(self.export_btn)
        
        vis_group.setLayout(vis_layout)
        self.left_layout.addWidget(vis_group)
        
        # Add stretch to push everything to the top
        self.left_layout.addStretch()
        
        # Initialize UI state
        self.update_baseline_visibility()
    
    def load_files(self):
        """Open file dialog to load Excel/CSV files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Data Files",
            "",
            "Excel/CSV Files (*.xlsx *.xls *.csv);;All Files (*)"
        )
        
        if file_paths:
            try:
                # Get current sampling frequency
                sampling_freq = self.freq_input.value()
                
                # Load each file
                for file_path in file_paths:
                    self.data_manager.load_file(file_path, sampling_freq)
                
                # Update file list
                self.update_file_list()
                
                # Update sample list
                self.update_sample_list()
                
                # Try to auto-select files if samples are selected
                if self.auto_select_cb.isChecked() and self.sample_list.count() > 0:
                    self.on_samples_selected()
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load files: {str(e)}")
                
                # Print detailed error for debugging
                import traceback
                traceback.print_exc()
    
    def update_file_list(self):
        """Update the file list widget with loaded files."""
        self.file_list.clear()
        
        for file_path in self.data_manager.loaded_files:
            display_name = self.data_manager.get_file_display_name(file_path)
            item = self.file_list.addItem(display_name)
            self.file_list.item(self.file_list.count()-1).setData(Qt.UserRole, file_path)
    
    def update_sample_list(self):
        """Update the sample selection list."""
        self.sample_list.clear()
        samples = self.data_manager.get_samples()
        
        if samples:
            # Add each sample to the list
            for sample in samples:
                self.sample_list.addItem(sample)
    
    def update_segment_list(self):
        """Update the segment list with available segments from selected files."""
        # Get selected files
        selected_files = []
        for item in self.file_list.selectedItems():
            file_path = item.data(Qt.UserRole)
            selected_files.append(file_path)
        
        if not selected_files:
            self.segment_list.clear()
            return
        
        # Get segments from selected files
        segments = self.data_manager.get_segment_names(selected_files)
        
        # Store current selections
        current_selections = []
        for i in range(self.segment_list.count()):
            item = self.segment_list.item(i)
            if item.isSelected():
                current_selections.append(item.text())
        
        # Update segment list
        self.segment_list.clear()
        if segments:
            self.segment_list.addItems(segments)
            
            # Restore previous selections if possible
            for i in range(self.segment_list.count()):
                item = self.segment_list.item(i)
                if item.text() in current_selections:
                    item.setSelected(True)
        
        # Update visualization
        self.on_segments_selected()
    
    def on_samples_selected(self):
        """Handle sample selection from the list."""
        if not self.auto_select_cb.isChecked():
            return
        
        # Get all selected samples
        selected_samples = []
        for item in self.sample_list.selectedItems():
            selected_samples.append(item.text())
        
        if not selected_samples:
            return
        
        # Get all files for selected samples
        selected_files = []
        for sample in selected_samples:
            sample_files = self.data_manager.get_files_by_sample(sample)
            selected_files.extend(sample_files)
        
        # Clear current file selection
        self.file_list.clearSelection()
        
        # Select all files for all selected samples
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.data(Qt.UserRole)
            
            if file_path in selected_files:
                item.setSelected(True)
    
    def on_segments_selected(self):
        """Handle segment selection changes."""
        self.update_visualization()
    
    def on_side_selection_changed(self):
        """Handle changes to side selection checkboxes."""
        # If "Both Sides" is checked, uncheck individual sides
        if self.side_both_cb.isChecked():
            self.side_left_cb.setChecked(False)
            self.side_right_cb.setChecked(False)
        
        # If neither is checked, default to "Both Sides"
        if not self.side_both_cb.isChecked() and not self.side_left_cb.isChecked() and not self.side_right_cb.isChecked():
            self.side_both_cb.setChecked(True)
        
        self.update_visualization()
    
    def on_auto_select_changed(self, state):
        """Handle changes to the auto-select checkbox."""
        if state == Qt.Checked:
            self.on_samples_selected()
    
    def on_normalization_changed(self):
        """Handle normalization method changes."""
        self.update_baseline_visibility()
        self.update_visualization()
    
    def update_baseline_visibility(self):
        """Update visibility of baseline controls based on normalization method."""
        norm_method = self.norm_combo.currentText()
        baseline_visible = "Baseline" in norm_method
        
        self.baseline_start.setEnabled(baseline_visible)
        self.baseline_duration.setEnabled(baseline_visible)
    
    def on_sampling_freq_changed(self, value):
        """Handle sampling frequency changes."""
        self.data_manager.sampling_freq = value
        self.update_visualization()
    
    def on_apply_filter(self):
        """Apply gaussian filter to current visualization."""
        sigma = self.filter_sigma.value()
        if hasattr(self.plot_canvas, 'apply_gaussian_filter'):
            self.plot_canvas.apply_gaussian_filter(sigma)
    
    def on_reset_filter(self):
        """Reset all filters."""
        self.filter_sigma.setValue(0)
        if hasattr(self.plot_canvas, 'reset_filters'):
            self.plot_canvas.reset_filters()
    
    def get_selected_segments_and_sides(self):
        """Get the currently selected segments and sides."""
        selected_segments = []
        for item in self.segment_list.selectedItems():
            selected_segments.append(item.text())
        
        # Determine which sides to show
        show_left = self.side_left_cb.isChecked() or self.side_both_cb.isChecked()
        show_right = self.side_right_cb.isChecked() or self.side_both_cb.isChecked()
        
        print(f"Selected segments: {selected_segments}")
        print(f"Show left: {show_left}, Show right: {show_right}")
        
        return selected_segments, show_left, show_right
    
    def get_plot_data_for_segments(self, selected_segments, show_left, show_right):
        """Prepare plot data for the selected segments and sides."""
        # Get selected files
        selected_files = []
        for item in self.file_list.selectedItems():
            file_path = item.data(Qt.UserRole)
            selected_files.append(file_path)
        
        if not selected_files:
            print("No files selected")
            return {}
        
        # Get all segments data
        all_segments = self.data_manager.get_all_segments(selected_files)
        
        # Prepare plot data
        plot_data = {}
        
        for segment_name in selected_segments:
            if segment_name in all_segments:
                segment_data = all_segments[segment_name]
                traces = []
                
                # Add left side traces if selected
                if show_left and 'left' in segment_data:
                    for trace_info in segment_data['left']:
                        file_path = trace_info['file_path']
                        column = trace_info['column']
                        
                        if file_path in self.data_manager.loaded_files:
                            df = self.data_manager.loaded_files[file_path]['df']
                            region = self.data_manager.loaded_files[file_path]['info'].get('region', '')
                            
                            # Make sure column exists in df
                            if column in df.columns:
                                traces.append({
                                    'file_path': file_path,
                                    'column': column,
                                    'df': df,
                                    'region': region
                                })
                
                # Add right side traces if selected
                if show_right and 'right' in segment_data:
                    for trace_info in segment_data['right']:
                        file_path = trace_info['file_path']
                        column = trace_info['column']
                        
                        if file_path in self.data_manager.loaded_files:
                            df = self.data_manager.loaded_files[file_path]['df']
                            region = self.data_manager.loaded_files[file_path]['info'].get('region', '')
                            
                            # Make sure column exists in df
                            if column in df.columns:
                                traces.append({
                                    'file_path': file_path,
                                    'column': column,
                                    'df': df,
                                    'region': region
                                })
                
                if traces:  # Only add segment if it has traces to plot
                    plot_data[segment_name] = {
                        'traces': traces
                    }
                    print(f"Added {len(traces)} traces for segment {segment_name}")
        
        return plot_data
    
    def update_visualization(self):
        """Update the plot based on current selections and settings."""
        # Get selected segments and sides
        selected_segments, show_left, show_right = self.get_selected_segments_and_sides()
        
        if not selected_segments:
            # Clear plot if no segments selected
            if hasattr(self.plot_canvas, 'update_plot'):
                self.plot_canvas.update_plot({})
            return
        
        # Get plot data
        plot_data = self.get_plot_data_for_segments(selected_segments, show_left, show_right)
        
        if not plot_data:
            print("No plot data available")
            # Clear plot if no data
            if hasattr(self.plot_canvas, 'update_plot'):
                self.plot_canvas.update_plot({})
            return
        
        # Get current settings
        norm_method = self.norm_combo.currentText().lower()
        view_mode = self.view_combo.currentText().lower()
        baseline_start = self.baseline_start.value()
        baseline_duration = self.baseline_duration.value()
        show_mean = self.show_mean_cb.isChecked()
        show_delta = self.show_delta_cb.isChecked()
        
        # Normalize method mapping
        norm_mapping = {
            'none': 'none',
            'mean': 'mean',
            'δf/f₀ (baseline)': 'baseline'
        }
        
        # Update plot
        if hasattr(self.plot_canvas, 'update_plot'):
            self.plot_canvas.update_plot(
                plot_data,
                norm_mapping.get(norm_method, 'none'),
                view_mode,
                baseline_start,
                baseline_duration,
                self.data_manager.sampling_freq,
                show_mean=show_mean,
                show_delta=show_delta,
                delta_segments=selected_segments[:2] if show_delta and len(selected_segments) >= 2 else None
            )
    
    def export_figure(self):
        """Export the current figure as a PDF."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Figure",
            "",
            "PDF Files (*.pdf);;All Files (*)",
            options=options
        )
        
        if file_name:
            if not file_name.lower().endswith('.pdf'):
                file_name += '.pdf'
            
            success = self.plot_canvas.save_figure(file_name)
            
            if success:
                QMessageBox.information(self, "Success", f"Figure saved to {file_name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save figure")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultiTraceVisualizer()
    window.show()
    sys.exit(app.exec_())