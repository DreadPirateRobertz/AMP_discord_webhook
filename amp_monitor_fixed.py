#!/usr/bin/env python3
"""
AMP Free Admission Monitor - Fixed for WSL/SSL Issues
Checks https://ampcode.com/news/amp-free-is-full-for-now every 15 minutes
Sends Discord alert when status changes from FULL to OPEN
"""

import requests
import time
import urllib3
from datetime import datetime
from bs4 import BeautifulSoup
import certifi

# Disable SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WEBSITE_URL = "https://ampcode.com/news/amp-free-is-full-for-now"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1200480366750863430/8q2jsEPIPPwIkUOKxBRT-T-ICL1pLMkgggqqdhm9-BZgI2XdlJtMmJABKbwqYDWzUFvp"
CHECK_INTERVAL = 900  # 15 minutes in seconds

# Try to use certifi certificates, fall back to no verification if needed
USE_SSL_VERIFY = True

def send_discord_alert(message):
    """Send alert to Discord webhook"""
    try:
        data = {
            "content": message,
            "username": "AMP Monitor"
        }
        
        # Try with SSL verification first, then without
        try:
            response = requests.post(DISCORD_WEBHOOK, json=data, verify=certifi.where(), timeout=10)
        except:
            if USE_SSL_VERIFY:
                print("  ⚠️ SSL verification failed, trying without verification...")
            response = requests.post(DISCORD_WEBHOOK, json=data, verify=False, timeout=10)
        
        if response.status_code == 204:
            print(f"✓ Discord alert sent successfully at {datetime.now()}")
            return True
        else:
            print(f"✗ Failed to send Discord alert: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error sending Discord alert: {e}")
        return False

def check_website():
    """Check if website status has changed"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Try with SSL verification first, then without
        try:
            response = requests.get(WEBSITE_URL, headers=headers, verify=certifi.where(), timeout=10)
        except:
            response = requests.get(WEBSITE_URL, headers=headers, verify=False, timeout=10)
        
        response.raise_for_status()
        
        # Parse the page content
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().upper()
        
        # Check for status indicators
        is_full = 'FULL' in page_text
        is_open = any(keyword in page_text for keyword in ['OPEN', 'AVAILABLE', 'ACCEPTING'])
        
        return {
            'success': True,
            'is_full': is_full,
            'is_open': is_open,
            'page_text': page_text[:300]
        }
    except Exception as e:
        print(f"✗ Error checking website: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Main monitoring loop"""
    print("=" * 60)
    print("AMP Free Admission Monitor Started")
    print(f"Website: {WEBSITE_URL}")
    print(f"Check Interval: {CHECK_INTERVAL // 60} minutes")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    # Test the connection first
    print("\nTesting connections...")
    test_result = check_website()
    if test_result['success']:
        print("✓ Website connection successful!")
        current_status = 'FULL' if test_result['is_full'] else 'OPEN'
        print(f"✓ Current status: {current_status}")
    else:
        print(f"✗ Website connection failed: {test_result.get('error')}")
        print("  Will retry every 15 minutes...")
    
    # Send initial test message
    print("\nSending Discord test message...")
    if send_discord_alert("🤖 AMP Monitor is now active! Checking every 15 minutes for admission changes..."):
        print("✓ Discord webhook working!")
    else:
        print("✗ Discord webhook failed. Check your webhook URL.")
    
    print("\n" + "=" * 60)
    print("Monitoring started. Press Ctrl+C to stop.")
    print("=" * 60)
    
    previous_status = None
    check_count = 0
    
    while True:
        check_count += 1
        print(f"\n[Check #{check_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        result = check_website()
        
        if result['success']:
            current_status = 'FULL' if result['is_full'] else 'OPEN'
            print(f"  Status: {current_status}")
            
            # Check if status changed from FULL to OPEN
            if previous_status == 'FULL' and not result['is_full']:
                alert_message = (
                    f"🚨 **ALERT! AMP FREE IS NOW OPEN!** 🚨\n\n"
                    f"The admission status has changed from FULL to OPEN!\n"
                    f"Check it out now: {WEBSITE_URL}\n\n"
                    f"Time detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_discord_alert(alert_message)
                print("  🎉 STATUS CHANGED TO OPEN! Alert sent!")
            
            # Also alert if it goes back to FULL (for monitoring purposes)
            elif previous_status == 'OPEN' and result['is_full']:
                alert_message = (
                    f"⚠️ AMP Free has returned to FULL status.\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                send_discord_alert(alert_message)
                print("  ℹ️ Status changed back to FULL")
            
            previous_status = current_status
        else:
            print(f"  Failed to check website: {result.get('error')}")
        
        next_check = datetime.fromtimestamp(time.time() + CHECK_INTERVAL)
        print(f"  Next check in {CHECK_INTERVAL // 60} minutes at {next_check.strftime('%H:%M:%S')}...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        send_discord_alert("⚠️ AMP Monitor has been stopped manually.")
    except Exception as e:
        error_msg = f"❌ AMP Monitor crashed with error: {str(e)}"
        print(error_msg)
        try:
            send_discord_alert(error_msg)
        except:
            pass
