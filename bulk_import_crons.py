#!/usr/bin/env python3
"""
Bulk import OpenClaw cron jobs into Cheese Brain.

Reads cron configuration and creates workflow entities for each job.
"""

import json
import subprocess
from datetime import datetime
from cheese_brain import CheeseBrain
from cheese_brain.models import Entity, EntityCategory

def get_cron_jobs():
    """Get cron jobs via OpenClaw CLI."""
    try:
        # Try to find openclaw command
        result = subprocess.run(
            ["openclaw", "cron", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        # Try without --format flag
        try:
            result = subprocess.run(
                ["openclaw", "cron", "list"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            print(f"❌ Error fetching cron jobs: {e}")
            return None
    except Exception as e:
        print(f"❌ Error fetching cron jobs: {e}")
        return None

def format_schedule(schedule):
    """Format schedule dict to human-readable string."""
    if schedule['kind'] == 'cron':
        expr = schedule['expr']
        tz = schedule.get('tz', 'UTC')
        return f"Cron: {expr} ({tz})"
    elif schedule['kind'] == 'every':
        ms = schedule['everyMs']
        hours = ms / (1000 * 60 * 60)
        if hours >= 24:
            return f"Every {hours/24:.1f} days"
        elif hours >= 1:
            return f"Every {hours:.1f} hours"
        else:
            return f"Every {ms/1000/60:.0f} minutes"
    elif schedule['kind'] == 'at':
        return f"At: {schedule['at']}"
    else:
        return str(schedule)

def infer_tags(job_name, payload):
    """Infer tags from job name and payload."""
    tags = ["cron", "automation"]
    
    text = f"{job_name} {json.dumps(payload)}".lower()
    
    if 'digest' in text:
        tags.append('digest')
    if 'news' in text or 'alert' in text:
        tags.append('monitoring')
    if 'security' in text or 'audit' in text:
        tags.append('security')
    if 'backup' in text or 'archive' in text:
        tags.append('backup')
    if 'gmail' in text or 'email' in text:
        tags.append('email')
    if 'telegram' in text or 'message' in text:
        tags.append('messaging')
    if 'calendar' in text:
        tags.append('calendar')
    if 'weekly' in text:
        tags.append('weekly')
    if 'daily' in text:
        tags.append('daily')
    
    return tags

def format_next_run(next_run_ms):
    """Format next run timestamp."""
    if not next_run_ms:
        return "Not scheduled"
    dt = datetime.fromtimestamp(next_run_ms / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def main():
    """Import all cron jobs."""
    brain = CheeseBrain()
    
    print("🧀 Bulk Import: OpenClaw Cron Jobs\n")
    print("=" * 70)
    
    data = get_cron_jobs()
    if not data or 'jobs' not in data:
        print("❌ No cron jobs found")
        brain.close()
        return
    
    jobs = data['jobs']
    print(f"Found {len(jobs)} cron jobs to import\n")
    
    imported = 0
    skipped = 0
    
    for job in jobs:
        job_name = job.get('name', 'Unnamed Job')
        job_id = job.get('id')
        
        # Check if already exists
        existing = brain.search(job_name, category="workflow", limit=1)
        if existing and existing[0].title == job_name:
            print(f"⏭️  {job_name:<50} (already exists)")
            skipped += 1
            continue
        
        # Extract info
        schedule = job.get('schedule', {})
        payload = job.get('payload', {})
        state = job.get('state', {})
        enabled = job.get('enabled', False)
        
        tags = infer_tags(job_name, payload)
        if not enabled:
            tags.append('disabled')
        
        # Create entity
        try:
            entity = Entity(
                category=EntityCategory.WORKFLOW,
                title=job_name,
                data={
                    "type": "openclaw_cron",
                    "job_id": job_id,
                    "enabled": enabled,
                    "schedule": format_schedule(schedule),
                    "schedule_raw": schedule,
                    "session_target": job.get('sessionTarget'),
                    "payload_kind": payload.get('kind'),
                    "payload_message": payload.get('message', '')[:200] if payload.get('message') else None,
                    "next_run": format_next_run(state.get('nextRunAtMs')),
                    "last_status": state.get('lastStatus'),
                    "agent_id": job.get('agentId')
                },
                tags=tags
            )
            entity_id = brain.add_entity(entity)
            print(f"✅ {job_name:<50} ({len(tags)} tags)")
            imported += 1
        except Exception as e:
            print(f"❌ {job_name:<50} Error: {e}")
    
    brain.close()
    
    print("\n" + "=" * 70)
    print(f"\n✅ Import complete:")
    print(f"   Imported: {imported}")
    print(f"   Skipped:  {skipped}")
    print(f"   Total:    {imported + skipped}")

if __name__ == "__main__":
    main()
