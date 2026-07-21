import pandas as pd

def load_excel(file_path: str) -> dict:
    """
    Reads all sheets in an Excel file, converts every row into text,
    prepends the sheet name, and returns the combined text and sheet count.
    """
    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names
    combined_texts = []
    
    for sheet_name in sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name)
        # Convert df to string without index
        df_str = df.to_string(index=False)
        combined_texts.append(f"=== Sheet: {sheet_name} ===\n{df_str}")
        
    combined_sheet_text = "\n\n".join(combined_texts)
    return {
        'text': combined_sheet_text,
        'sheets': len(sheet_names)
    }
