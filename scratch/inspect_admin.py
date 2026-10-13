import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('frontend/admin.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_sec = False
sec_lines = []
for i, line in enumerate(lines, 1):
    if 'id="secVehicleBookings"' in line:
        in_sec = True
    if in_sec:
        sec_lines.append(f"{i}: {line}")
        if len(sec_lines) > 80:
            break

print("".join(sec_lines))
