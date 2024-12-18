import pandas as pd
import os
from datetime import datetime
import base64
from io import BytesIO

def save_generation_log(prompt, image, group_members):
    """Save the generation details to a CSV file"""
    # Convert image to base64 string
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Prepare the data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        'timestamp': [timestamp],
        'group_members': [group_members],
        'prompt': [prompt],
        'image': [img_str]
    }
    
    # Create or append to CSV
    df = pd.DataFrame(data)
    csv_path = 'generations.csv'
    
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, index=False) 