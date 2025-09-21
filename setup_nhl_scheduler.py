#!/usr/bin/env python3
"""
NHL Data Fetcher - Scheduler Setup
This script provides multiple options for scheduling the NHL data fetcher.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_cron_job():
    """Set up a cron job to run the NHL fetcher daily"""
    project_dir = Path(__file__).parent.absolute()
    python_path = shutil.which('python3') or '/usr/bin/python3'
    manage_py = project_dir / 'manage.py'
    log_dir = project_dir / 'logs'
    log_file = log_dir / 'nhl_fetch.log'
    
    # Create logs directory
    log_dir.mkdir(exist_ok=True)
    
    # Cron job command (runs at 9 AM daily)
    cron_command = f"0 9 * * * cd {project_dir} && {python_path} {manage_py} fetch_nhl_scores >> {log_file} 2>&1"
    
    print("Setting up cron job...")
    print(f"Command: {cron_command}")
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        # Check if job already exists
        if 'fetch_nhl_scores' in current_crontab:
            print("NHL fetcher cron job already exists. Updating...")
            # Remove existing job
            lines = [line for line in current_crontab.split('\n') if 'fetch_nhl_scores' not in line]
            new_crontab = '\n'.join(lines).strip()
        else:
            print("Adding new NHL fetcher cron job...")
            new_crontab = current_crontab.strip()
        
        # Add new job
        if new_crontab:
            new_crontab += '\n'
        new_crontab += cron_command + '\n'
        
        # Install new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Cron job setup successful!")
            print(f"   Runs daily at 9:00 AM")
            print(f"   Logs: {log_file}")
            return True
        else:
            print("❌ Failed to install cron job")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {e}")
        return False

def setup_systemd_timer():
    """Set up systemd timer for the NHL fetcher"""
    project_dir = Path(__file__).parent.absolute()
    service_file = project_dir / 'nhl-fetcher.service'
    timer_file = project_dir / 'nhl-fetcher.timer'
    
    if not service_file.exists() or not timer_file.exists():
        print("❌ Systemd service/timer files not found")
        return False
    
    try:
        print("Setting up systemd timer...")
        
        # Copy service files to systemd directory
        subprocess.run(['sudo', 'cp', str(service_file), '/etc/systemd/system/'], check=True)
        subprocess.run(['sudo', 'cp', str(timer_file), '/etc/systemd/system/'], check=True)
        
        # Reload systemd and enable timer
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        subprocess.run(['sudo', 'systemctl', 'enable', 'nhl-fetcher.timer'], check=True)
        subprocess.run(['sudo', 'systemctl', 'start', 'nhl-fetcher.timer'], check=True)
        
        print("✅ Systemd timer setup successful!")
        print("   Use 'sudo systemctl status nhl-fetcher.timer' to check status")
        print("   Use 'sudo journalctl -u nhl-fetcher.service' to view logs")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error setting up systemd timer: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def manual_test():
    """Run a manual test of the NHL fetcher"""
    project_dir = Path(__file__).parent.absolute()
    python_path = shutil.which('python3') or '/usr/bin/python3'
    manage_py = project_dir / 'manage.py'
    
    print("Running manual test...")
    try:
        result = subprocess.run([
            python_path, str(manage_py), 'fetch_nhl_scores', '--date=2025-09-21'
        ], cwd=project_dir, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Manual test successful!")
            return True
        else:
            print(f"❌ Manual test failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running manual test: {e}")
        return False

def main():
    print("NHL Data Fetcher - Scheduler Setup")
    print("=" * 40)
    print()
    
    if len(sys.argv) > 1:
        method = sys.argv[1].lower()
    else:
        print("Available scheduling methods:")
        print("1. cron     - Use cron jobs (recommended for most systems)")
        print("2. systemd  - Use systemd timers (requires sudo)")
        print("3. test     - Run manual test")
        print()
        method = input("Choose method (1-3 or cron/systemd/test): ").strip().lower()
    
    if method in ['1', 'cron']:
        setup_cron_job()
    elif method in ['2', 'systemd']:
        setup_systemd_timer()
    elif method in ['3', 'test']:
        manual_test()
    else:
        print("Invalid option. Use 'cron', 'systemd', or 'test'")
        sys.exit(1)

if __name__ == '__main__':
    main()