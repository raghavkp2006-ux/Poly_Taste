import os
import re

files_to_update = [
    'frontend/src/components/dashboard/DashboardHome.tsx',
    'frontend/src/components/dashboard/Sidebar.tsx',
    'frontend/src/components/dashboard/TopBar.tsx',
    'frontend/src/components/dashboard/RecommendationRow.tsx',
    'frontend/src/components/dashboard/ContinueRow.tsx',
    'frontend/src/components/dashboard/ActivityFeed.tsx',
    'frontend/src/components/blocks/hero.tsx',
    'frontend/src/components/interchange/Card.tsx'
]

# Replacement strategies:
# 1. Existing hex Tailwind classes: bg-[#FAFAFA] -> bg-[#FAFAFA] dark:bg-[#0A0A0B]
# 2. Existing hex inline styles: style={{ color: "#18181B" }} -> remove color from style, add text-[#18181B] dark:text-[#FAFAFA] to className

def process_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} (not found)")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # 1. Backgrounds
    content = content.replace('bg-[#FAFAFA]', 'bg-[#FAFAFA] dark:bg-[#0A0A0B] transition-colors duration-150 ease-out')
    content = content.replace('bg-[#FFFFFF]', 'bg-[#FFFFFF] dark:bg-[#18181B] transition-colors duration-150 ease-out')
    
    # 2. Borders
    content = content.replace('border-[#E4E4E7]', 'border-[#E4E4E7] dark:border-[#27272A] transition-colors duration-150 ease-out')
    content = content.replace('borderColor: "rgba(0,0,0,0.06)"', 'borderColor: ""') # Let's handle border manually via tailwind if possible, or just leave it. Actually, wait. It's better to replace inline border colors with tailwind classes.
    
    # 3. Shadows (remove in dark mode)
    # The spec says: remove shadows entirely in dark mode: dark:shadow-none
    content = re.sub(r'(shadow-\[[^\]]+\])', r'\1 dark:shadow-none', content)
    
    # 4. Text colors
    content = content.replace('text-[#18181B]', 'text-[#18181B] dark:text-[#FAFAFA] transition-colors duration-150 ease-out')
    content = content.replace('text-[#71717A]', 'text-[#71717A] dark:text-[#A1A1AA] transition-colors duration-150 ease-out')

    # 5. Accent color
    content = content.replace('text-[#2563EB]', 'text-[#2563EB] dark:text-[#3B82F6]')
    content = content.replace('bg-[#2563EB]', 'bg-[#2563EB] dark:bg-[#3B82F6]')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Processed {filepath}")

for f in files_to_update:
    process_file(f)
