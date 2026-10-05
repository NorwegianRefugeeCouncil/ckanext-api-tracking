# Next release

New Features:
- Capture usage in `after_app_request` hook instead of a WSGI middleware
  [#41](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/41)
- Detect what to track by CKAN view function instead of URL regexes
  [#42](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/42)

- New dashboard page "Usage by user" (`/tracking-dashboard/users-usage`) with
  period selector, CSV (`/tracking-csv/usage-by-user.csv`) and API action `usage_by_user`
  [#43](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/43)
- Charts for dashboards [#44](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/44)
- Chart for "Latest API token usage" [#45](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/45)
- Stop using the CKAN core `stats` plugin [#46](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/46)
- Indexes on `tracking_usage` for the dashboard queries [#47](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/47)
- New settings `ckanext.api_tracking.track_ui_users` and `track_ui_anonymous`
  (default true): store web pages visits (no JS required)
  [#49](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/49)

Bug Fixes:
- "Users creating most datasets" was empty when `ckan.auth.public_user_details` was false
- Do not track pages that only looked like a dataset page (e.g. `/dataset/new`)
- Multiple fixes PR [#48](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/48)
  - CSV endpoints return 403 for non-sysadmins instead of an unhandled error
  - Resources CSV no longer crashes when a tracked resource does not exist anymore
  - Latest API token usage no longer crashes for datasets without organization
  - Latest API token usage looks up each user and object once (it was once per row)
  - Remove unused SQL files and helpers

# 0.5.4 2025-09-11

New Features:
- CKAN 2.12 upgrade [#40](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/40)

Bug Fixes:
- Fix inconsistency between API and dashboard for empty token filtering
  [#37](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/37)

# 0.5.3 2025-07-31

Bug Fixes:
- Redefine requests and add more tests [#35](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/35)

# 0.5.2 2025-05-30

New Features:
 - Add internationalization (ES) [#29](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/29)
 - For the token view, display only with token[#32](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/32)

Bug Fixes:
 - Use CKAN default object types [#30](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/30)

# 0.5.1

New features

 - Start tracking user login/logout [#28](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/pull/28).
   Requires to be enabled in the configuration.

# 0.4.6
 - Allow extending base template

# 0.4.5
 - Upgrade to CKAN 2.11

# 0.4.4
 - Split resource and dataset stats
