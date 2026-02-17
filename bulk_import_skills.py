#!/usr/bin/env python3
"""
Bulk import OpenClaw skills into Cheese Brain.

Reads all installed skills from /opt/homebrew/lib/node_modules/openclaw/skills/
and creates tool entities for each.
"""

import os
import re
from pathlib import Path
from cheese_brain import CheeseBrain
from cheese_brain.models import Entity, EntityCategory

SKILLS_DIR = Path("/opt/homebrew/lib/node_modules/openclaw/skills")

def extract_description(skill_path):
    """Extract description from SKILL.md file."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return "No description available"
    
    try:
        content = skill_md.read_text()
        # Try to extract first meaningful line after frontmatter/title
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        for line in lines:
            if not line.startswith('#') and not line.startswith('---') and len(line) > 10:
                # Clean up markdown formatting
                line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)  # Remove bold
                line = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', line)  # Remove links
                return line[:500]  # Limit to 500 chars
        return lines[0] if lines else "No description available"
    except Exception:
        return "No description available"

def infer_tags(skill_name, description):
    """Infer tags from skill name and description."""
    tags = ["openclaw-skill"]
    
    desc_lower = f"{skill_name} {description}".lower()
    
    # Category tags
    if any(word in desc_lower for word in ['cli', 'command', 'terminal']):
        tags.append('cli')
    if any(word in desc_lower for word in ['api', 'rest', 'http']):
        tags.append('api')
    if any(word in desc_lower for word in ['notes', 'obsidian', 'bear', 'notion']):
        tags.append('notes')
    if any(word in desc_lower for word in ['music', 'spotify', 'audio']):
        tags.append('audio')
    if any(word in desc_lower for word in ['chat', 'message', 'slack', 'discord', 'telegram']):
        tags.append('messaging')
    if any(word in desc_lower for word in ['code', 'git', 'github', 'programming']):
        tags.append('development')
    if any(word in desc_lower for word in ['tts', 'voice', 'speech']):
        tags.append('voice')
    if any(word in desc_lower for word in ['video', 'frame', 'ffmpeg']):
        tags.append('video')
    if any(word in desc_lower for word in ['weather', 'forecast']):
        tags.append('weather')
    if any(word in desc_lower for word in ['search', 'web', 'browser']):
        tags.append('web')
    
    return tags

def main():
    """Import all OpenClaw skills."""
    brain = CheeseBrain()
    
    print("🧀 Bulk Import: OpenClaw Skills\n")
    print("=" * 70)
    
    if not SKILLS_DIR.exists():
        print(f"❌ Skills directory not found: {SKILLS_DIR}")
        return
    
    # Get all skill directories
    skills = [d for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    skills.sort()
    
    print(f"Found {len(skills)} skills to import\n")
    
    imported = 0
    skipped = 0
    
    for skill_path in skills:
        skill_name = skill_path.name
        
        # Check if already exists
        existing = brain.search(skill_name, category="tool", limit=1)
        if existing and existing[0].title.lower() == skill_name.lower():
            print(f"⏭️  {skill_name:<30} (already exists)")
            skipped += 1
            continue
        
        # Extract info
        description = extract_description(skill_path)
        tags = infer_tags(skill_name, description)
        
        # Create entity
        try:
            entity = Entity(
                category=EntityCategory.TOOL,
                title=f"OpenClaw Skill: {skill_name}",
                data={
                    "type": "openclaw_skill",
                    "skill_name": skill_name,
                    "path": str(skill_path),
                    "description": description,
                    "skill_md": str(skill_path / "SKILL.md") if (skill_path / "SKILL.md").exists() else None
                },
                tags=tags
            )
            entity_id = brain.add_entity(entity)
            print(f"✅ {skill_name:<30} ({len(tags)} tags)")
            imported += 1
        except Exception as e:
            print(f"❌ {skill_name:<30} Error: {e}")
    
    brain.close()
    
    print("\n" + "=" * 70)
    print(f"\n✅ Import complete:")
    print(f"   Imported: {imported}")
    print(f"   Skipped:  {skipped}")
    print(f"   Total:    {imported + skipped}")

if __name__ == "__main__":
    main()
