# Coaching Hours Tracker

Automatically log tennis-coaching hours by detecting when you arrive at and
leave the court, then ask Claude "how many hours did I do?" for any biweekly
period.

## How it works

```
Android phone (geofence at the court)
        |  arrive  -> HTTP GET  ...?event=arrive
        |  leave   -> HTTP GET  ...?event=leave
        v
Make webhook  ->  Make scenario "Tennis Hours Logger"
        v
Make Data Store "Tennis Session Log"  (one row per arrive/leave, with a timestamp)
        v
Claude reads the log, pairs arrive->leave per day, sums the hours
```

Google Maps Timeline no longer has a public API (Google moved that data
on-device in late 2024), so instead of reading Timeline we capture the same
"where was I / for how long" signal directly from the phone's geofence.

## Backend (already built in Make)

All of this lives in the Make account `mihirpatel1023@gmail.com`
(org "My Organization", team "My Team", id `2358345`):

| Component        | Name                    | ID         |
|------------------|-------------------------|------------|
| Webhook          | Tennis Geofence Webhook | `2454714`  |
| Scenario         | Tennis Hours Logger     | `5389488`  |
| Data Store       | Tennis Session Log      | `108407`   |
| Data Structure   | Tennis Session Log Structure | `401001` |

**Webhook URL** (the phone calls this):

```
https://hook.us2.make.com/k27f0ni7723panrdxph33vnbxyjmctqt
```

- Arrive:  `https://hook.us2.make.com/k27f0ni7723panrdxph33vnbxyjmctqt?event=arrive`
- Leave:   `https://hook.us2.make.com/k27f0ni7723panrdxph33vnbxyjmctqt?event=leave`

Each call appends a row `{ event, time }` to the data store, where `time` is
the moment Make received the request (timezone America/Toronto).

## Android setup (one-time, ~5 minutes)

Use **MacroDroid** (free) or **Tasker**. MacroDroid steps:

1. Install MacroDroid from the Play Store, grant location permission
   ("Allow all the time" — required for geofencing in the background).
2. Create Macro #1 — **Arrive**:
   - Trigger: *Geofence Trigger* -> add a zone centered on the tennis court,
     radius ~150 m -> Entry.
   - Action: *HTTP Request (GET)* ->
     `https://hook.us2.make.com/k27f0ni7723panrdxph33vnbxyjmctqt?event=arrive`
3. Create Macro #2 — **Leave**: same geofence zone, **Exit** trigger ->
   GET `...?event=leave`.
4. Save both. Test by driving to the court (or temporarily set the zone over
   your current location to confirm a row appears in the data store).

## Asking for your hours

Ask Claude, e.g. "how many coaching hours did I do in the last two weeks?"
Claude reads data store `108407`, then for the requested window:

1. Sort rows by time.
2. Pair each `arrive` with the next `leave` on the same day.
3. Sum the durations and report the total (with a short per-day breakdown).
4. Flag any unpaired `arrive`/`leave` (e.g. a missed geofence) so you can
   correct it manually.

### Expected schedule (sanity check baseline)

- Weekday evenings: ~6:00pm-8:00pm (2 h)
- Weekends: ~10:00am-2:00pm (4 h)

If the geofence ever misses an event, these are the fallback numbers to use.
