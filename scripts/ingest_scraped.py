"""Ingest scraped GoDaddy conversations into lead_pipeline.db"""
import json
import sqlite3
import os
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lead_pipeline.db")
STATUS_MAP = {0: "open", 1: "pending", 7: "spam", 8: "resolved"}

CONVERSATIONS = json.loads(r'''[{"id":822998992,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"Kschiltroth@gmail.com","message_count":1,"created_at":"2026-03-20T03:32:12.332Z","updated_at":"2026-03-20T03:32:12.488Z"},{"id":821940207,"subject":"What types of addiction treatment programs do you offer?","status":1,"display_name":"Guest User (1773888174)","email":"","message_count":2,"created_at":"2026-03-19T02:42:54.355Z","updated_at":"2026-03-20T01:20:18.818Z"},{"id":821463658,"subject":"What types of addiction treatment programs do you offer?","status":1,"display_name":"Guest User (1773853840)","email":"","message_count":2,"created_at":"2026-03-18T17:10:41.021Z","updated_at":"2026-03-18T17:12:37.114Z"},{"id":821335026,"subject":"What types of addiction treatment programs do you offer?","status":1,"display_name":"","email":"","message_count":2,"created_at":"2026-03-18T15:31:15.386Z","updated_at":"2026-03-18T17:06:52.039Z"},{"id":820946129,"subject":"What types of addiction treatment programs do you offer?","status":1,"display_name":"","email":"","message_count":2,"created_at":"2026-03-18T05:10:45.440Z","updated_at":"2026-03-18T05:27:06.508Z"},{"id":820884799,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-18T02:17:19.173Z","updated_at":"2026-03-18T17:07:40.252Z"},{"id":820694905,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"","message_count":1,"created_at":"2026-03-17T21:28:22.442Z","updated_at":"2026-03-17T21:28:22.626Z"},{"id":819856839,"subject":"How can I get started with your 28-Day Boot Camp?","status":1,"display_name":"","email":"","message_count":4,"created_at":"2026-03-17T04:18:04.915Z","updated_at":"2026-03-17T04:44:50.719Z"},{"id":819852109,"subject":"Can you explain how your small group format enhances the recovery experience?","status":1,"display_name":"","email":"","message_count":4,"created_at":"2026-03-17T04:03:48.749Z","updated_at":"2026-03-17T04:46:34.709Z"},{"id":819570930,"subject":"What types of addiction treatment programs do you offer?","status":1,"display_name":"","email":"","message_count":4,"created_at":"2026-03-16T20:47:55.352Z","updated_at":"2026-03-16T22:54:53.273Z"},{"id":818028911,"subject":"How can I get started with your 28-Day Boot Camp?","status":1,"display_name":"Al","email":"","message_count":4,"created_at":"2026-03-14T23:22:51.562Z","updated_at":"2026-03-16T21:56:57.792Z"},{"id":818025449,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-14T23:13:42.688Z","updated_at":"2026-03-14T23:20:10.450Z"},{"id":816322829,"subject":"What types of addiction treatment programs do you offer?","status":1,"display_name":"Allison","email":"","message_count":4,"created_at":"2026-03-12T21:06:18.968Z","updated_at":"2026-03-16T22:00:45.493Z"},{"id":815382964,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-12T00:13:35.626Z","updated_at":"2026-03-12T00:20:10.942Z"},{"id":814992505,"subject":"What types of addiction treatment programs do you offer?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-03-11T17:22:25.528Z","updated_at":"2026-03-11T17:30:13.871Z"},{"id":814749462,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-11T14:17:06.416Z","updated_at":"2026-03-11T14:25:11.155Z"},{"id":813661852,"subject":"How can I get started with your 28-Day Boot Camp?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-03-10T13:50:29.323Z","updated_at":"2026-03-10T14:00:28.137Z"},{"id":812408261,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-09T07:54:26.349Z","updated_at":"2026-03-09T08:00:08.521Z"},{"id":811609112,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"","message_count":1,"created_at":"2026-03-07T21:28:45.197Z","updated_at":"2026-03-07T21:28:45.298Z"},{"id":811513371,"subject":"I am wanting to know if you have a residential alcohol use disorder treatment program?","status":0,"display_name":"","email":"","message_count":5,"created_at":"2026-03-07T18:36:47.744Z","updated_at":"2026-03-07T18:43:09.178Z"},{"id":810161760,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"","message_count":1,"created_at":"2026-03-06T02:11:41.020Z","updated_at":"2026-03-06T02:11:41.148Z"},{"id":810022824,"subject":"How can I get started with your 28-Day Boot Camp?","status":0,"display_name":"","email":"","message_count":3,"created_at":"2026-03-05T22:33:18.871Z","updated_at":"2026-03-05T22:34:10.653Z"},{"id":809801402,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"","message_count":1,"created_at":"2026-03-05T18:52:42.359Z","updated_at":"2026-03-05T18:52:42.496Z"},{"id":809484294,"subject":"What types of addiction treatment programs do you offer?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-03-05T14:33:46.103Z","updated_at":"2026-03-05T14:40:11.867Z"},{"id":807114579,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-03T03:11:53.315Z","updated_at":"2026-03-03T03:20:19.425Z"},{"id":806990125,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-02T23:41:51.067Z","updated_at":"2026-03-02T23:50:30.769Z"},{"id":806841551,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"","message_count":1,"created_at":"2026-03-02T20:54:03.190Z","updated_at":"2026-03-02T20:54:03.357Z"},{"id":806178605,"subject":"How can I get started with your 28-Day Boot Camp?","status":0,"display_name":"","email":"","message_count":3,"created_at":"2026-03-02T08:39:41.918Z","updated_at":"2026-03-02T08:40:21.240Z"},{"id":805879966,"subject":"How can I get started with your 28-Day Boot Camp?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-03-01T20:34:38.409Z","updated_at":"2026-03-01T20:40:10.402Z"},{"id":805535524,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":7,"created_at":"2026-03-01T07:39:27.382Z","updated_at":"2026-03-01T07:40:50.383Z"},{"id":805462066,"subject":"What types of addiction treatment programs do you offer?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-03-01T02:47:44.335Z","updated_at":"2026-03-01T02:55:09.014Z"},{"id":805448443,"subject":"How can I get started with your 28-Day Boot Camp?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-03-01T02:07:59.794Z","updated_at":"2026-03-01T02:15:09.472Z"},{"id":804946617,"subject":"How can I get started with your 28-Day Boot Camp?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-02-28T09:08:18.156Z","updated_at":"2026-02-28T09:15:07.691Z"},{"id":803933912,"subject":"How can I get started with your 28-Day Boot Camp?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-27T03:58:31.448Z","updated_at":"2026-02-27T04:05:11.894Z"},{"id":803891519,"subject":"Can you explain how your small group format enhances the recovery experience?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-27T02:18:33.787Z","updated_at":"2026-02-27T02:25:09.679Z"},{"id":803444442,"subject":"Mental health in patient","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-26T17:48:15.872Z","updated_at":"2026-02-26T17:55:12.700Z"},{"id":803161387,"subject":"How can I get started with your 28-Day Boot Camp?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-26T14:01:42.957Z","updated_at":"2026-02-26T14:10:10.028Z"},{"id":802943836,"subject":"How can I get started with your 28-Day Boot Camp?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-02-26T06:01:51.166Z","updated_at":"2026-02-26T06:10:07.322Z"},{"id":802940529,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-02-26T05:51:11.538Z","updated_at":"2026-02-26T06:00:08.012Z"},{"id":801865967,"subject":"How can I get started with your 28-Day Boot Camp?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-25T03:36:51.443Z","updated_at":"2026-02-25T03:45:09.906Z"},{"id":801839741,"subject":"Contact Form: Contact Us","status":0,"display_name":"","email":"","message_count":1,"created_at":"2026-02-25T02:39:13.814Z","updated_at":"2026-02-25T02:39:13.946Z"},{"id":801514988,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":1,"created_at":"2026-02-24T19:44:58.605Z","updated_at":"2026-02-24T19:45:00.497Z"},{"id":800754243,"subject":"How can I get started with your 28-Day Boot Camp?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-24T01:38:02.916Z","updated_at":"2026-02-24T01:45:20.194Z"},{"id":800434439,"subject":"What types of addiction treatment programs do you offer?","status":8,"display_name":"","email":"","message_count":5,"created_at":"2026-02-23T19:16:34.605Z","updated_at":"2026-02-23T19:25:33.756Z"},{"id":800396796,"subject":"I want the money you owe me.","status":0,"display_name":"","email":"","message_count":4,"created_at":"2026-02-23T18:45:26.981Z","updated_at":"2026-02-23T18:46:50.782Z"},{"id":799598345,"subject":"What types of addiction treatment programs do you offer?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-22T20:29:53.590Z","updated_at":"2026-02-22T20:35:12.330Z"},{"id":799195393,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-02-22T02:14:54.441Z","updated_at":"2026-02-22T02:20:08.780Z"},{"id":799124156,"subject":"What types of addiction treatment programs do you offer?","status":8,"display_name":"","email":"","message_count":3,"created_at":"2026-02-21T23:13:06.925Z","updated_at":"2026-02-21T23:20:11.394Z"},{"id":798723809,"subject":"I'm trying to quit drinking and need guidance please","status":0,"display_name":"","email":"","message_count":4,"created_at":"2026-02-21T10:54:54.427Z","updated_at":"2026-02-21T10:57:36.485Z"},{"id":798578172,"subject":"What types of addiction treatment programs do you offer?","status":0,"display_name":"","email":"","message_count":2,"created_at":"2026-02-21T02:32:20.195Z","updated_at":"2026-02-21T02:40:42.415Z"}]''')

MESSAGES = [
    {"conversation_id": 822998992, "messages": [{"sender_name": "", "sender_email": "Kschiltroth@gmail.com"}]},
    {"conversation_id": 818028911, "messages": [{"sender_name": "Al", "sender_email": "", "body": "Talk to a human"}]},
    {"conversation_id": 816322829, "messages": [{"sender_name": "Allison", "sender_email": "", "body": "Talk to a human"}]},
    {"conversation_id": 811513371, "messages": [{"sender_name": "", "sender_email": "", "body": "Talk to a human"}]},
    {"conversation_id": 820884799, "messages": [{"sender_name": "", "sender_email": "", "body": "consultation booked for Thursday"}]},
    {"conversation_id": 810022824, "messages": [{"sender_name": "", "sender_email": "", "body": "Talk to a human"}]},
]

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check existing external_ids
    try:
        cur.execute("SELECT external_id FROM leads WHERE external_id IS NOT NULL")
        existing = {row["external_id"] for row in cur.fetchall()}
    except:
        existing = set()

    msgs_by_id = {e["conversation_id"]: e["messages"] for e in MESSAGES}
    
    seen_ids = set()
    ingested = 0
    updated = 0

    for conv in CONVERSATIONS:
        cid = conv["id"]
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        
        ext_id = f"gd-{cid}"
        status_code = conv.get("status", 0)
        gd_status = STATUS_MAP.get(status_code, "open")

        # Map status
        if gd_status == "resolved":
            status = "closed"
        elif gd_status == "pending":
            status = "contacted"
        elif gd_status == "spam":
            status = "closed"
        else:
            status = "new"

        # Check for "talk to a human"
        msgs = msgs_by_id.get(cid, [])
        needs_human = False
        for m in msgs:
            if "talk to a human" in (m.get("body", "") or "").lower():
                needs_human = True
                status = "hot"
                break

        # Extract identity
        name = conv.get("display_name", "")
        email = conv.get("email", "")
        if not name or "Guest User" in name:
            for m in msgs:
                sn = m.get("sender_name", "")
                if sn and "Guest" not in sn and "Trifecta" not in sn:
                    name = sn
                    break
        if not name or "Guest User" in name:
            name = ""

        for m in msgs:
            se = m.get("sender_email", "")
            if se and "trifecta" not in se.lower():
                email = se
                break

        subject = conv.get("subject", "")
        # Determine program interest from subject
        prog = ""
        if "28-day" in subject.lower() or "boot camp" in subject.lower():
            prog = "28-Day Boot Camp"
        elif "14-day" in subject.lower() or "executive reset" in subject.lower():
            prog = "14-Day Executive Reset"
        elif "inpatient" in subject.lower() or "residential" in subject.lower():
            prog = "Inpatient"
        elif "virtual" in subject.lower():
            prog = "Virtual"

        if ext_id in existing:
            cur.execute("UPDATE leads SET status=?, updated_at=?, initial_question=? WHERE external_id=?",
                       (status, conv.get("updated_at", ""), subject, ext_id))
            updated += 1
        else:
            lead_id = str(uuid.uuid4())[:8]
            cur.execute("""INSERT INTO leads (id, external_id, external_contact_key, name, email, phone, source, status, initial_question, program_interest, created_at, updated_at)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (lead_id, ext_id, f"gd-contact-{cid}", name, email, "",
                        "godaddy_chat", status, subject, prog,
                        conv.get("created_at", ""), conv.get("updated_at", "")))
            ingested += 1

    conn.commit()
    cur.execute("SELECT status, COUNT(*) as cnt FROM leads GROUP BY status")
    by_status = {row["status"]: row["cnt"] for row in cur.fetchall()}
    cur.execute("SELECT COUNT(*) as cnt FROM leads")
    total = cur.fetchone()["cnt"]
    conn.close()
    
    print(json.dumps({"ingested": ingested, "updated": updated, "total": total, "by_status": by_status}, indent=2))

if __name__ == "__main__":
    main()
