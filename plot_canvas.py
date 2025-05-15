import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import re
from scipy.ndimage import gaussian_filter1d

class PlotCanvas(QWidget):
    """Widget for plotting time series data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.figure = plt.figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Initialize with empty plot
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Signal')
        self.canvas.draw()
        
        # Store current plot state
        self.current_dfs = {}  # {file_path: df}
        self.current_view = 'overlay'  # 'overlay' or 'stacked'
        self.current_normalization = 'none'  # 'none', 'mean', or 'baseline'
        self.baseline_start = 0
        self.baseline_duration = 10
        
        # Define color schemes for left and right sides
        self.left_colors = {
            'soma': 'red',            # pure red for soma
            'axon': 'darkred',        # dark red for axons
            'axons': 'darkred',       # dark red for axons
            'dend': 'indianred',      # indian red for dendrites
            'dendrite': 'indianred',  # indian red for dendrites
            'dendrites': 'indianred', # indian red for dendrites
            'mix': 'firebrick',       # firebrick for mix
            'default': 'red'          # pure red for unknown type
        }
        
        self.right_colors = {
            'soma': 'blue',           # pure blue for soma
            'axon': 'darkblue',       # dark blue for axons
            'axons': 'darkblue',      # dark blue for axons
            'dend': 'royalblue',      # royal blue for dendrites
            'dendrite': 'royalblue',  # royal blue for dendrites
            'dendrites': 'royalblue', # royal blue for dendrites
            'mix': 'steelblue',       # steel blue for mix
            'default': 'blue'         # pure blue for unknown type
        }
        
        # Define line styles for different regions
        self.region_styles = {
            'soma': '-',      # solid line for soma
            'axon': '-',     # solid line for axon
            'axons': '-',    # solid line for axons
            'dend': '-',      # solid line for dendrite
            'dendrite': '-',  # solid line for dendrite
            'dendrites': '-', # solid line for dendrites
            'mix': '-',      # solid line for mix
            'default': '-'    # solid line for default
        }
    
    def update_plot(self, plot_data, normalization='none', view_mode='overlay', 
                   baseline_start=0, baseline_duration=10, sampling_freq=5.0,
                   show_mean=False, show_delta=False, delta_segments=None):
        """
        Update the plot with the given data.
        
        Args:
            plot_data: Dictionary of segments with traces to plot
            normalization: Normalization method ('none', 'mean', 'baseline')
            view_mode: Plot view mode ('overlay' or 'stacked')
            baseline_start: Start time for baseline normalization (seconds)
            baseline_duration: Duration of baseline period (seconds)
            sampling_freq: Sampling frequency in Hz
            show_mean: Whether to show mean traces for each segment
            show_delta: Whether to show delta between segments
            delta_segments: List of segments to calculate delta for
        """
        try:
            # Debug info
            print(f"Update plot called with {len(plot_data)} segments")
            for segment, data in plot_data.items():
                print(f"  Segment {segment}: {len(data['traces'])} traces")
                
            # Clear existing figure to start fresh
            self.figure.clear()
            
            if not plot_data:
                self.ax = self.figure.add_subplot(111)
                self.ax.set_title('No data selected')
                self.canvas.draw()
                return
            
            # Update current state
            self.current_dfs = plot_data
            self.current_view = view_mode
            self.current_normalization = normalization
            self.baseline_start = baseline_start
            self.baseline_duration = baseline_duration
            
            # Track max time for x-axis
            max_time = 0
            min_time = float('inf')
            
            if view_mode.lower() == 'overlay':
                # Create a single subplot for overlay view
                self.ax = self.figure.add_subplot(111)
                
                for segment_name, segment_data in plot_data.items():
                    traces = segment_data['traces']
                    
                    for trace in traces:
                        file_path = trace.get('file_path')
                        column = trace.get('column')
                        region = trace.get('region', '')
                        df = trace.get('df')
                        
                        # Skip if no data
                        if df is None or column not in df.columns:
                            print(f"Skipping trace: file_path={file_path}, column={column} - not in DataFrame")
                            continue
                        
                        # Process data
                        processed_df = self._process_dataframe(df, normalization, baseline_start, baseline_duration, sampling_freq)
                        
                        # Get time values
                        x = self._get_time_values(processed_df, sampling_freq)
                        if len(x) > 0:
                            if max(x) > max_time:
                                max_time = max(x)
                            if min(x) < min_time:
                                min_time = min(x)
                        
                        # Determine side (left or right)
                        side = None
                        match = re.search(r'Mean\((.*?)([lr])\)', column)
                        if match:
                            side = match.group(2)
                            side_info = " (L)" if side == 'l' else " (R)"
                        else:
                            side_info = ""
                        
                        # Choose color based on side and region
                        color = None
                        if side == 'l':  # Left side - red colors
                            # Find color for this region
                            for reg_key, col_value in self.left_colors.items():
                                if region and reg_key in region.lower():
                                    color = col_value
                                    break
                            if color is None:
                                color = self.left_colors['default']
                        elif side == 'r':  # Right side - blue colors
                            # Find color for this region
                            for reg_key, col_value in self.right_colors.items():
                                if region and reg_key in region.lower():
                                    color = col_value
                                    break
                            if color is None:
                                color = self.right_colors['default']
                        else:  # No clear side - use green
                            color = 'green'
                        
                        # Get line style based on region
                        linestyle = None
                        for reg_key, style in self.region_styles.items():
                            if region and reg_key in region.lower():
                                linestyle = style
                                break
                        if linestyle is None:
                            linestyle = self.region_styles['default']
                        
                        # Create a descriptive label
                        sample_name = os.path.basename(file_path).split('_')[0:3]
                        sample_name = '_'.join(sample_name)
                        region_info = f" ({region})" if region else ""
                        label = f"{segment_name}{side_info}{region_info} - {sample_name}"
                        
                        # Plot with the determined style
                        self.ax.plot(x, processed_df[column], 
                                    label=label, 
                                    color=color,
                                    linestyle=linestyle,
                                    linewidth=1.5)
                
                # Configure axis for overlay mode
                if normalization == 'mean':
                    self.ax.set_ylabel('Signal (% of mean)')
                elif normalization == 'baseline':
                    self.ax.set_ylabel('ΔF/F₀ (%)')
                else:
                    self.ax.set_ylabel('Signal')
                
                # Add legend with smaller font
                self.ax.legend(fontsize=8, loc='upper right')
                
            else:  # stacked view
                # Sort segments by type (t segments first, then a segments)
                segment_names = list(plot_data.keys())
                segment_names.sort(key=lambda s: (s[0] != 't', s))  # t segments first, then alphabetically
                
                # Count total valid segments
                valid_segments = []
                for segment_name in segment_names:
                    if segment_name in plot_data and plot_data[segment_name]['traces']:
                        valid_segments.append(segment_name)
                
                if not valid_segments:
                    self.ax = self.figure.add_subplot(111)
                    self.ax.set_title('No valid segments selected')
                    self.canvas.draw()
                    return
                
                # Create one subplot per segment
                axes = []
                for i, segment_name in enumerate(valid_segments):
                    ax = self.figure.add_subplot(len(valid_segments), 1, i+1)
                    axes.append(ax)
                    
                    traces = plot_data[segment_name]['traces']
                    
                    # Group traces by region for better organization within each segment
                    region_traces = {}
                    
                    for trace in traces:
                        region = trace.get('region', 'unknown')
                        if region not in region_traces:
                            region_traces[region] = {'left': [], 'right': []}
                        
                        # Determine side and add to appropriate list
                        match = re.search(r'Mean\((.*?)([lr])\)', trace.get('column', ''))
                        if match and match.group(2) == 'l':
                            region_traces[region]['left'].append(trace)
                        elif match and match.group(2) == 'r':
                            region_traces[region]['right'].append(trace)
                    
                    # Sort regions to ensure consistent order (soma, axon, dend, mix)
                    region_order = ['soma', 'axon', 'axons', 'dend', 'dendrite', 'dendrites', 'mix', 'unknown']
                    sorted_regions = sorted(region_traces.keys(), 
                                          key=lambda r: next((i for i, reg in enumerate(region_order) if reg in r.lower()), len(region_order)))
                    
                    # Vertical offset between regions within the same segment
                    region_offset = 20  # Base offset between regions
                    total_offset = 0
                    
                    # Process and plot traces for each region
                    for region in sorted_regions:
                        left_traces = region_traces[region]['left']
                        right_traces = region_traces[region]['right']
                        
                        # Skip if no traces for this region
                        if not left_traces and not right_traces:
                            continue
                        
                        # Keep track of plotted data for region labeling
                        has_plotted_data = False
                        has_time_values = False
                        
                        # Plot left and right traces for this region with current offset
                        for traces, side, color_map in [
                            (left_traces, 'l', self.left_colors),
                            (right_traces, 'r', self.right_colors)
                        ]:
                            for trace in traces:
                                file_path = trace.get('file_path')
                                column = trace.get('column')
                                df = trace.get('df')
                                
                                if df is None or column not in df.columns:
                                    print(f"Skipping trace in stacked view: file_path={file_path}, column={column} - not in DataFrame")
                                    continue
                                
                                # Process data
                                processed_df = self._process_dataframe(df, normalization, baseline_start, baseline_duration, sampling_freq)
                                
                                # Get time values
                                x = self._get_time_values(processed_df, sampling_freq)
                                if len(x) > 0:
                                    has_time_values = True
                                    if max(x) > max_time:
                                        max_time = max(x)
                                    if min(x) < min_time:
                                        min_time = min(x)
                                else:
                                    continue
                                
                                # Get color for this trace
                                color = color_map.get(region, color_map['default'])
                                
                                # Plot the trace with offset
                                if column in processed_df.columns:
                                    y_values = processed_df[column].values + total_offset
                                    ax.plot(x, y_values, color=color, linewidth=1.0)
                                    has_plotted_data = True
                        
                        # Add region label if there are traces to display
                        if has_plotted_data and has_time_values:
                            # Position label at the start of the region's traces
                            ax.text(-0.01, total_offset, region, 
                                   fontsize=8, ha='right', va='center', color='black',
                                   transform=ax.get_yaxis_transform())  # Use axis coordinates for x
                        
                        # Increment offset for next region
                        total_offset += region_offset
                    
                    # Add segment label on the left
                    ax.text(-0.01, 0.5, segment_name, transform=ax.transAxes,
                           fontsize=12, va='center', ha='right', fontweight='bold')
                    
                    # Clean up this subplot
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    # Only show x-axis on bottom subplot
                    ax.spines['bottom'].set_visible(i == len(valid_segments) - 1)
                    
                    # Remove ticks
                    ax.tick_params(axis='y', which='both', left=False, labelleft=False)
                    
                    # Add grid lines
                    ax.grid(True, axis='both', linestyle='--', alpha=0.2)
                    
                    # Only show x-ticks on bottom subplot
                    if i < len(valid_segments) - 1:
                        ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
                
                # Add common y-axis label
                if normalization == 'mean':
                    self.figure.text(0.02, 0.5, 'Signal (% of mean)', va='center', rotation='vertical')
                elif normalization == 'baseline':
                    self.figure.text(0.02, 0.5, 'ΔF/F₀ (%)', va='center', rotation='vertical')
                else:
                    self.figure.text(0.02, 0.5, 'Signal', va='center', rotation='vertical')
                
                # Add x-axis label to bottom subplot
                if axes:
                    axes[-1].set_xlabel('Time (s)')
            
            # Configure x-axis (add some margin)
            if min_time < float('inf') and max_time > 0:
                x_range = max_time - min_time
                
                # Apply limits to all axes
                if view_mode.lower() == 'overlay':
                    self.ax.set_xlim(min_time, max_time + x_range * 0.1)
                else:
                    for ax in axes:
                        ax.set_xlim(min_time, max_time + x_range * 0.1)
            
            # Adjust spacing between subplots
            if view_mode.lower() == 'stacked':
                plt.subplots_adjust(left=0.1, right=0.98, top=0.95, bottom=0.1, hspace=0.0)
            else:
                plt.tight_layout()
            
            # Show plot
            self.canvas.draw()
            
        except Exception as e:
            import traceback
            print(f"Error in update_plot: {str(e)}")
            traceback.print_exc()
            
            # Create a fallback simple plot 
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_title(f"Error plotting: {str(e)}")
            self.canvas.draw()
    
    def _get_time_values(self, df, sampling_freq):
        """Get time values from DataFrame or generate based on sampling frequency."""
        try:
            if df is None:
                return np.array([])
                
            if 'Time' in df.columns:
                return df['Time'].values
            else:
                # Generate time values based on length and sampling frequency
                return np.arange(len(df)) / sampling_freq
        except Exception as e:
            print(f"Error in _get_time_values: {str(e)}")
            return np.array([])
    
    def _process_dataframe(self, df, normalization, baseline_start, baseline_duration, sampling_freq):
        """Process the dataframe according to normalization settings."""
        try:
            if df is None:
                return None
                
            if normalization == 'none':
                return df
            elif normalization == 'mean':
                return self.parent.data_manager.normalize_by_mean(df)
            elif normalization == 'baseline':
                return self.parent.data_manager.normalize_baseline(df, baseline_start, baseline_duration, sampling_freq)
            return df
        except Exception as e:
            print(f"Error in _process_dataframe: {str(e)}")
            return df
    
    def apply_gaussian_filter(self, sigma_percent):
        """Apply gaussian filter to all traces in the current plot."""
        if not self.current_dfs:
            return
        
        try:
            filtered_dfs = {}
            
            for segment_name, segment_data in self.current_dfs.items():
                filtered_traces = []
                
                for trace in segment_data.get('traces', []):
                    file_path = trace.get('file_path')
                    column = trace.get('column')
                    region = trace.get('region')
                    df = trace.get('df')
                    
                    if df is None or column not in df.columns:
                        continue
                    
                    # Calculate sigma in data points
                    data_length = len(df)
                    sigma = (sigma_percent / 100) * data_length
                    
                    # Make a copy to avoid modifying the original
                    df_copy = df.copy()
                    
                    # Apply filter to this column
                    if column in df_copy.columns:
                        df_copy[column] = gaussian_filter1d(df_copy[column].values, sigma)
                    
                    # Add filtered trace
                    filtered_traces.append({
                        'file_path': file_path,
                        'column': column,
                        'region': region,
                        'df': df_copy
                    })
                
                # Add to filtered data
                if filtered_traces:
                    filtered_dfs[segment_name] = {'traces': filtered_traces}
            
            # Update plot with filtered data
            self.update_plot(
                filtered_dfs, 
                self.current_normalization,
                self.current_view,
                self.baseline_start,
                self.baseline_duration,
                self.parent.data_manager.sampling_freq
            )
        except Exception as e:
            print(f"Error in apply_gaussian_filter: {str(e)}")
    
    def reset_filters(self):
        """Reset all filters to show original data."""
        if not self.current_dfs:
            return
        
        try:
            original_dfs = {}
            
            for segment_name, segment_data in self.current_dfs.items():
                original_traces = []
                
                for trace in segment_data.get('traces', []):
                    file_path = trace.get('file_path')
                    column = trace.get('column')
                    region = trace.get('region')
                    
                    # Get original data from data manager
                    if file_path in self.parent.data_manager.loaded_files:
                        original_df = self.parent.data_manager.loaded_files[file_path]['original'].copy()
                        
                        # Add original trace
                        original_traces.append({
                            'file_path': file_path,
                            'column': column,
                            'region': region,
                            'df': original_df
                        })
                
                # Add to original data
                if original_traces:
                    original_dfs[segment_name] = {'traces': original_traces}
            
            # Update plot with original data
            self.update_plot(
                original_dfs, 
                self.current_normalization,
                self.current_view,
                self.baseline_start,
                self.baseline_duration,
                self.parent.data_manager.sampling_freq
            )
        except Exception as e:
            print(f"Error in reset_filters: {str(e)}")
    
    def save_figure(self, filename):
        """Save the current figure to a file."""
        try:
            self.figure.savefig(filename, format='pdf', dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"Error saving figure: {str(e)}")
            return False