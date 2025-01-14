## 0.5.10 (2025-01-14)

### Fix

- fix type declaration at (a)safe_cast

## 0.5.9 (2025-01-09)

### Fix

- fixed imports to import from their modern location and avoid deprecation warnings

## 0.5.8 (2025-01-08)

### Fix

- created carrymap/carrystarmap and asyncio counterparts

## 0.5.7 (2024-11-05)

### Fix

- **strings/casting**: created string functions sentence/question/exclamation and decorator call_once

## 0.5.6 (2024-10-13)

### Fix

- add namespace and remove redundant code
- added asafe_generator decorator to use aclosing and avoid resource leakage on pypy and using object.__setattr__ at lazymethod to avoid conflicts with gyver.attrs

## 0.5.5 (2024-09-26)

### Fix

- added asafe_cast to all

## 0.5.4 (2024-09-26)

### Fix

- added asafe_cast

## 0.5.3 (2024-09-16)

### Fix

- removed print from code

## 0.5.2 (2024-09-13)

### Fix

- **strings**: added convert function

## 0.5.1 (2024-09-12)

### Fix

- now lazymethod supports N args instead of only self

## 0.5.0 (2024-09-11)

### Feat

- **enums**: added enums package to have strenum boilerplate code and added maybe_next and maybe_anext functions

## 0.4.0 (2024-09-05)

### Feat

- **asynciter**: added amap, afilter, aall, aany and agetn_and_exhaust functions

## 0.3.1 (2024-07-18)

### Fix

- updated overload for as async correctly identify function signatures

## 0.3.0 (2024-07-10)

## 0.2.0 (2024-06-30)

### Feat

- created miscellaneous implementations for day-to-day work
