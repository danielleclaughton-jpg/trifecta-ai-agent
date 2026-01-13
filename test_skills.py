#!/usr/bin/env python
"""Test all Trifecta AI Agent skills"""
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "http://localhost:8000"

def test_skills():
    print("=" * 60)
    print("TRIFECTA AI AGENT - SKILL TESTER")
    print("=" * 60)
    
    # 1. List all skills
    print("\n📚 Loading Skills...")
    r = requests.get(f"{API_BASE}/api/skills", timeout=10)
    if r.status_code != 200:
        print(f"❌ Failed to load skills: {r.status_code}")
        return
    
    data = r.json()
    print(f"✅ {data['count']} skills loaded ({data['total_size']:,} bytes)")
    print("\nAvailable Skills:")
    for s in data['skills']:
        print(f"  • {s['name']}")
        print(f"    Title: {s['title']}")
        print(f"    Keywords: {', '.join(s.get('keywords', [])[:5]) or 'None'}")
        print()

    # 2. Test chat with different skill contexts
    print("=" * 60)
    print("🧪 TESTING SKILLS VIA CHAT")
    print("=" * 60)
    
    test_messages = [
        ("What services does Trifecta offer?", "trifecta-practice-system"),
        ("How does the client intake process work?", "trifecta-lead-intake-workflow"),
        ("Generate a contract for a new client", "trifecta-document-generator"),
        ("Create a session plan for anxiety treatment", "trifecta-tailored-session-builder"),
        ("What marketing strategies work for addiction treatment?", "trifecta-marketing-seo"),
    ]
    
    for i, (msg, expected_skill) in enumerate(test_messages, 1):
        print(f"\n--- Test {i}: {expected_skill} ---")
        print(f"Message: \"{msg}\"")
        
        r = requests.post(
            f"{API_BASE}/api/chat",
            json={"message": msg},
            timeout=60
        )
        
        if r.status_code == 200:
            resp = r.json()
            matched = resp.get('matched_skill', 'None')
            demo = resp.get('demo_mode', False)
            reply = resp.get('reply', '')[:200]
            
            print(f"✅ Status: 200")
            print(f"   Matched Skill: {matched}")
            print(f"   Demo Mode: {demo}")
            print(f"   Reply: {reply}...")
        else:
            print(f"❌ Status: {r.status_code}")
            print(f"   Error: {r.text[:200]}")

    # 3. Test specific skill fetch
    print("\n" + "=" * 60)
    print("📖 FETCHING SPECIFIC SKILL CONTENT")
    print("=" * 60)
    
    skill_name = "trifecta-practice-system"
    r = requests.get(f"{API_BASE}/api/skills/{skill_name}", timeout=10)
    if r.status_code == 200:
        skill = r.json()
        print(f"\n✅ Skill: {skill['name']}")
        print(f"   Title: {skill['title']}")
        print(f"   Size: {skill['size']:,} bytes")
        print(f"   Keywords: {skill.get('keywords', [])}")
        print(f"   Content Preview: {skill['content'][:300]}...")
    else:
        print(f"❌ Failed to fetch skill: {r.status_code}")

    # 4. Test skill reload
    print("\n" + "=" * 60)
    print("🔄 TESTING SKILL RELOAD")
    print("=" * 60)
    
    r = requests.post(f"{API_BASE}/api/skills/reload", timeout=10)
    if r.status_code == 200:
        print(f"✅ Skills reloaded: {r.json()}")
    else:
        print(f"❌ Reload failed: {r.status_code}")

    print("\n" + "=" * 60)
    print("✅ SKILL TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_skills()
