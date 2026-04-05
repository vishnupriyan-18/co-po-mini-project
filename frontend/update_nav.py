import glob
import os

files = glob.glob('*.html')
nav_link = '<span>📝</span><span>Marks Entry</span></a>\n                <a href="attainment.html" class="nav-item"><span>🎯</span><span>Attainment</span></a>'
search_str = '<span>📝</span><span>Marks Entry</span></a>'

for f in files:
    if f != 'attainment.html':
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Only replace if not already present
        if 'attainment.html' not in content:
            content = content.replace(search_str, nav_link)
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
                
print("Updated HTML files.")
