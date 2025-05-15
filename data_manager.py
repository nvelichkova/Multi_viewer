import os
import re
import numpy as np
import pandas as pd

class DataManager:
    """Manages loading and processing of data files."""
    
    def __init__(self):
        self.loaded_files = {}  # Dictionary to store loaded files {file_path: {metadata}}
        self.sampling_freq = 5.0  # Default sampling frequency in Hz
    
    def load_file(self, file_path, sampling_freq=None):
        """Load data from Excel or CSV file."""
        try:
            # Use the current sampling frequency if not specified
            if sampling_freq is None:
                sampling_freq = self.sampling_freq
            
            # Load the file based on extension
            if file_path.lower().endswith('.xlsx') or file_path.lower().endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                raise ValueError("Unsupported file format. Please use Excel or CSV files.")
            
            # Get file info for display
            file_name = os.path.basename(file_path)
            file_info = self.parse_filename(file_name)
            
            # Analyze columns to find segment/side information
            segments = self.identify_segments(df)
            
            # Store the dataframe with metadata
            self.loaded_files[file_path] = {
                'df': df.copy(),
                'name': file_name,
                'info': file_info,
                'sampling_freq': sampling_freq,
                'original': df.copy(),  # Keep an original copy for reference
                'segments': segments
            }
            
            print(f"Loaded file: {file_name}")
            print(f"Found segments: {segments}")
            
            return file_path
        
        except Exception as e:
            raise ValueError(f"Error loading file: {str(e)}")
    
    def identify_segments(self, df):
        """Identify segment names, types, and sides from column names."""
        segments = {
            'all': [],
            'left': [],
            'right': []
        }
        
        # Common pattern for trace columns: Mean(SEGMENT_TYPE)(l/r)
        # e.g., Mean(a1l) for left side of segment a1
        # e.g., Mean(t2r) for right side of segment t2
        
        for col in df.columns:
            # Skip non-signal columns like 'Time'
            if isinstance(col, str) and 'Time' in col:
                continue
                
            # Check if column is a string
            if not isinstance(col, str):
                continue
                
            # Look for pattern Mean(XYl) or Mean(XYr) where XY is segment name
            match = re.search(r'Mean\((.*?)([lr])\)', col)
            if match:
                segment = match.group(1)  # e.g., 'a1', 't2'
                side = match.group(2)     # 'l' or 'r'
                
                # Add to appropriate lists
                segments['all'].append(col)
                if side == 'l':
                    segments['left'].append(col)
                else:
                    segments['right'].append(col)
            else:
                # Look for other common patterns in your data
                # If none of the patterns match but it's a data column, add it to all
                if 'Time' not in col and not col.startswith('Unnamed:'):
                    segments['all'].append(col)
        
        # Sort segments for consistent ordering
        segments['all'].sort()
        segments['left'].sort()
        segments['right'].sort()
        
        # Print segments found for debugging
        print(f"Identified segments: {segments}")
        
        return segments
    
    def parse_filename(self, filename):
        """
        Parse useful information from filename.
        Example: RP3_May_14_n5_soma.xlsx -> {'sample': 'RP3_May_14_n5', 'region': 'soma'}
        """
        # Remove file extension
        base_name = os.path.splitext(filename)[0]
        
        # Try to identify common patterns like sample_region
        parts = base_name.split('_')
        
        # Check if the last part indicates a region (soma, axon, etc.)
        common_regions = ['soma', 'axon', 'axons', 'dendrite', 'dendrites', 'dend', 'spine', 'spines', 'mix']
        region = None
        
        for r in common_regions:
            if parts[-1].lower() == r:
                region = parts[-1].lower()
                sample = '_'.join(parts[:-1])
                break
        
        # If no region found, use the whole filename as sample name
        if region is None:
            sample = base_name
        
        return {
            'sample': sample,
            'region': region
        }
    
    def get_file_display_name(self, file_path):
        """Get a display name for the file in the list."""
        if file_path in self.loaded_files:
            file_info = self.loaded_files[file_path]['info']
            file_name = self.loaded_files[file_path]['name']
            
            if file_info['region']:
                return f"{file_info['sample']} - {file_info['region']}"
            else:
                return file_name
        
        return os.path.basename(file_path)
    
    def get_samples(self):
        """Get unique sample names from loaded files."""
        samples = set()
        for file_path in self.loaded_files:
            sample = self.loaded_files[file_path]['info']['sample']
            samples.add(sample)
        return sorted(list(samples))
    
    def get_files_by_sample(self, sample):
        """Get all files for a given sample."""
        return [
            file_path for file_path in self.loaded_files
            if self.loaded_files[file_path]['info']['sample'] == sample
        ]
    
    def get_segment_names(self, file_paths):
        """Extract unique segment names from the given files."""
        segments = set()
        
        pattern = r'Mean\((.*?)([lr])\)'
        
        for file_path in file_paths:
            if file_path in self.loaded_files:
                file_data = self.loaded_files[file_path]
                df = file_data['df']
                
                for col in df.columns:
                    if isinstance(col, str):
                        match = re.search(pattern, col)
                        if match:
                            segment_name = match.group(1)  # e.g., 'a1', 't2'
                            segments.add(segment_name)
        
        # Print found segments for debugging
        print(f"Found {len(segments)} segments across selected files: {sorted(list(segments))}")
        
        return sorted(list(segments))
    
    def get_columns_for_segment(self, file_path, segment_name, side=None):
        """Get column names for a specific segment and optionally side."""
        if file_path not in self.loaded_files:
            return []
            
        df = self.loaded_files[file_path]['df']
        columns = []
        
        pattern = r'Mean\((.*?)([lr])\)'
        
        for col in df.columns:
            if isinstance(col, str):
                match = re.search(pattern, col)
                if match:
                    col_segment = match.group(1)
                    col_side = match.group(2)
                    
                    if col_segment == segment_name:
                        if side is None or col_side == side:
                            columns.append(col)
        
        return columns
    
    def get_all_segments(self, file_paths):
        """
        Get all segments data from the given files.
        Returns a dictionary mapping segment names to traces information.
        """
        # Dictionary to hold segment information
        all_segments = {}
        
        # Regex pattern for extracting segment name and side
        pattern = r'Mean\((.*?)([lr])\)'
        
        # Process each file
        for file_path in file_paths:
            if file_path not in self.loaded_files:
                continue
                
            file_data = self.loaded_files[file_path]
            df = file_data['df']
            
            # Process each column in the dataframe
            for col in df.columns:
                if not isinstance(col, str):
                    continue
                    
                match = re.search(pattern, col)
                if not match:
                    continue
                    
                segment_name = match.group(1)  # e.g., 'a1', 't2'
                side = match.group(2)          # 'l' or 'r'
                
                # Initialize this segment if not already in the dictionary
                if segment_name not in all_segments:
                    all_segments[segment_name] = {
                        'left': [],
                        'right': []
                    }
                
                # Add this trace to the appropriate side
                side_key = 'left' if side == 'l' else 'right'
                all_segments[segment_name][side_key].append({
                    'file_path': file_path,
                    'column': col
                })
        
        return all_segments
    
    def normalize_by_mean(self, df):
        """Normalize all signal columns by their mean values."""
        normalized_df = df.copy()
        numeric_columns = normalized_df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if isinstance(col, str) and 'Time' not in col:  # Skip time column if present
                mean_value = df[col].mean()
                if mean_value != 0:
                    normalized_df[col] = (df[col] / mean_value) * 100
                else:
                    print(f"Warning: {col} has zero mean, skipping normalization")
        
        return normalized_df
    
    def normalize_baseline(self, df, baseline_start, baseline_duration, sampling_freq):
        """Apply ΔF/F₀ normalization using specified baseline period."""
        normalized_df = df.copy()
        
        # Convert time to indices
        start_idx = int(baseline_start * sampling_freq)
        end_idx = int((baseline_start + baseline_duration) * sampling_freq)
        
        # Ensure indices are valid
        start_idx = max(0, start_idx)
        end_idx = min(len(df), end_idx)
        
        if start_idx >= end_idx:
            print(f"Warning: Invalid baseline period ({start_idx}:{end_idx}), using first 10% of data")
            start_idx = 0
            end_idx = max(1, int(len(df) * 0.1))
        
        numeric_columns = normalized_df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if isinstance(col, str) and 'Time' not in col:  # Skip time column if present
                # Calculate F₀ as mean of baseline period
                f0 = df[col][start_idx:end_idx].mean()
                
                if f0 != 0:
                    # Calculate ΔF/F₀ as percentage
                    normalized_df[col] = ((df[col] - f0) / f0) * 100
                else:
                    print(f"Warning: Zero baseline for {col}, skipping normalization")
        
        return normalized_df