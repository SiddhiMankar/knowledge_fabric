import os
import fitz
import pandas as pd
from PIL import Image, ImageDraw
import docx

os.makedirs("demo_docs", exist_ok=True)

# 1. pump_manual.pdf
print("Generating pump_manual.pdf...")
doc = fitz.open()
page = doc.new_page()
# Let's insert content to test text extraction and page counting
page.insert_text((50, 50), "Centrifugal pump P-101 is designed for continuous operation. Seal leakage may occur if flushing pressure drops below 2 bar...")
page.insert_text((50, 200), "This is page 1 content.")
page2 = doc.new_page()
page2.insert_text((50, 50), "This is page 2 content. Maintenance should be done every 6 months.")
doc.save("demo_docs/pump_manual.pdf")
doc.close()

# 2. maintenance_history.xlsx
print("Generating maintenance_history.xlsx...")
data_maint = {
    "Asset": ["P-101", "P-102"],
    "Date": ["2026-01-12", "2026-02-15"],
    "Issue": ["Bearing vibration", "Coupling wear"]
}
data_insp = {
    "Asset": ["P-101", "P-102"],
    "Inspector": ["Rahul", "Sarah"],
    "Status": ["OK", "Needs repair"]
}
df_maint = pd.DataFrame(data_maint)
df_insp = pd.DataFrame(data_insp)

with pd.ExcelWriter("demo_docs/maintenance_history.xlsx") as writer:
    df_maint.to_excel(writer, sheet_name="Maintenance", index=False)
    df_insp.to_excel(writer, sheet_name="Inspection", index=False)

# 3. inspection_report.jpg
print("Generating inspection_report.jpg...")
img = Image.new('RGB', (800, 400), color=(255, 255, 255))
d = ImageDraw.Draw(img)
text_lines = [
    "Drawing title: Pump Arrangement",
    "Tag: P-101",
    "Motor: M-101",
    "Flow direction: INLET -> OUTLET"
]
for i, line in enumerate(text_lines):
    d.text((20, 20 + i*40), line, fill=(0, 0, 0))
img.save("demo_docs/inspection_report.jpg")

# 4. failure_log.txt
print("Generating failure_log.txt...")
with open("demo_docs/failure_log.txt", "w", encoding="utf-8") as f:
    f.write("Log Entry: 2026-07-21 14:00:00\nSystem shutdown initiated due to overpressure on line L-102.\nOperator: John Doe\nStatus: Resolved.")

# 5. shutdown_procedure.docx
print("Generating shutdown_procedure.docx...")
doc_word = docx.Document()
doc_word.add_heading("Emergency Shutdown Procedure", 0)
doc_word.add_paragraph("1. Cut power to motor M-101.")
doc_word.add_paragraph("2. Close inlet valve V-101.")
doc_word.add_paragraph("3. Verify pressure gauge PG-101 reads zero.")
doc_word.save("demo_docs/shutdown_procedure.docx")

print("All sample files generated successfully!")
