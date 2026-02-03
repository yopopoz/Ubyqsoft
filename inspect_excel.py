
import pandas as pd
import json
import sys

# Set pandas display options to ensure no truncation
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)

try:
    df = pd.read_excel(r"c:\Users\pc\Desktop\BBOX L\Extrac MF - 25LAN034 BBOX - 27012026 rev INTER part.xlsx")
    
    # Get columns
    columns = df.columns.tolist()
    print("---COLUMNS---")
    print(json.dumps(columns, indent=2))
    print("---END COLUMNS---")
    
    print("---FIRST ROWS---")
    if not df.empty:
        # Convert Timestamp to string and handle NaN
        rows = df.iloc[0:2].where(pd.notnull(df.iloc[0:2]), None).to_dict(orient='records')
        print(json.dumps(rows, indent=2, default=str))
    print("---END FIRST ROWS---")
    
except Exception as e:
    print(f"Error: {e}")
