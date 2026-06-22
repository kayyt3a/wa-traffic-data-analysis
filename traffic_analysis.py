# WA Traffic Data Analysis
# CITS1401 Computational Thinking with Python, University of Western Australia
#
# Reads a CSV of WA traffic data and analyses it for a given Administrative Region.
# OP1 - summary per traffic year (site count, avg, std dev, heaviest site)
# OP2 - sites ranked by traffic volume within each Local Government Area
# OP3 - cosine similarity between weekday vs weekend heavy vehicle percentages
 
 
def read_csv(file_name):
    # Parse the CSV into a list of dicts keyed by lowercased column names
    try:
        with open(file_name, 'r') as f:
            lines = f.readlines()
    except Exception:
        return []
 
    if not lines:
        return []
 
    # First line is the header row; lowercase so field lookups are case-insensitive
    headers = [h.strip().lower() for h in lines[0].split(',')]
 
    rows = []
    for line in lines[1:]:
        line = line.strip()
        if not line:  # skip blank lines
            continue
        values = line.split(',')
        if len(values) < len(headers):  # malformed row - not enough columns
            continue
        # Zip each header with its value to build a dict for this row
        row = {headers[i]: values[i].strip() for i in range(len(headers))}
        rows.append(row)
 
    return rows
 
 
def is_valid_float(value):
    # Returns True if value can be converted to a float (including negatives)
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False
 
 
def is_non_negative_float(value):
    # Returns True only if value is a float >= 0 (traffic counts can't be negative)
    try:
        return float(value) >= 0
    except (ValueError, TypeError):
        return False
 
 
def validate_and_filter(rows, ra_name):
    # Coordinates/IDs - valid floats; traffic fields - non-negative; text fields - non-empty.
    # Rows sharing a SITE_NO are all discarded as duplicates.
    any_float_fields = ['x', 'y', 'lg_no', 'ra_no', 'objectid']
    non_neg_fields = [
        'mon_sun', 'mon_fri', 'sat_sun',
        'pct_heavy_mon_sun', 'pct_heavy_mon_fri', 'pct_heavy_sat_sun'
    ]
    string_fields = [
        'site_no', 'road_name', 'location_desc', 'traffic_year',
        'network_performance_site', 'lg_name', 'ra_name', 'globalid'
    ]
 
    # Count occurrences of each SITE_NO so we can identify duplicates
    site_no_counts = {}
    for row in rows:
        sn = row.get('site_no', '').strip().lower()
        if sn:
            site_no_counts[sn] = site_no_counts.get(sn, 0) + 1
    # Any SITE_NO appearing more than once means all rows with that ID are invalid
    duplicate_site_nos = {sn for sn, cnt in site_no_counts.items() if cnt > 1}
 
    ra_lower = ra_name.strip().lower()
    region_rows = []
 
    for row in rows:
        sn = row.get('site_no', '').strip().lower()
        # Discard the row if its SITE_NO is a known duplicate
        if sn in duplicate_site_nos:
            continue
 
        valid = True
        # Coordinates can be negative, so just check they parse as floats
        for field in any_float_fields:
            if not row.get(field, '').strip() or not is_valid_float(row[field]):
                valid = False
                break
        if not valid:
            continue
 
        # Traffic volumes and percentages must be zero or positive
        for field in non_neg_fields:
            if not row.get(field, '').strip() or not is_non_negative_float(row[field]):
                valid = False
                break
        if not valid:
            continue
 
        # Text fields must exist and not be blank
        for field in string_fields:
            if not row.get(field, '').strip():
                valid = False
                break
        if not valid:
            continue
 
        # Only keep rows that belong to the target region
        if row['ra_name'].strip().lower() == ra_lower:
            region_rows.append(row)
 
    return region_rows
 
 
def compute_op1(region_rows):
    # Per year: site count, mean MON_SUN, sample std dev, site with highest heavy vehicle %.
    # Ties on heavy vehicle % broken by alphabetically earliest GlobalID.
    if not region_rows:
        return {}
 
    # Bucket rows by traffic year
    year_groups = {}
    for row in region_rows:
        year = row['traffic_year'].strip()
        year_groups.setdefault(year, []).append(row)
 
    op1 = {}
    for year, rows in year_groups.items():
        n = len(rows)
        mon_sun_values = [float(r['mon_sun']) for r in rows]
        avg = sum(mon_sun_values) / n
        # Sample std dev divides by N-1; a single site has no spread so std dev is 0
        std = (sum((x - avg) ** 2 for x in mon_sun_values) / (n - 1)) ** 0.5 if n > 1 else 0.0
 
        # Track the site with the highest heavy vehicle percentage as we scan
        max_pct, max_site_no, max_global_id = None, None, None
        for row in rows:
            pct = float(row['pct_heavy_mon_sun'])
            gid = row['globalid'].strip().lower()
            sn = row['site_no'].strip()
            # Update if this site has a higher %, or equal % but earlier GlobalID
            if max_pct is None or pct > max_pct or (pct == max_pct and gid < max_global_id):
                max_pct, max_site_no, max_global_id = pct, sn, gid
 
        op1[year] = [n, round(avg, 4), round(std, 4), max_site_no]
 
    return op1
 
 
def compute_op2(region_rows):
    # Sites grouped by LGA (min 3 sites), ranked by MON_SUN descending.
    # Ties broken by alphabetically earliest GlobalID.
    if not region_rows:
        return {}
 
    # Bucket rows by LGA name
    lga_groups = {}
    for row in region_rows:
        lg = row['lg_name'].strip().lower()
        lga_groups.setdefault(lg, []).append(row)
 
    op2 = {}
    for lg_key, sites in lga_groups.items():
        # LGAs with fewer than 3 sites are excluded entirely
        if len(sites) < 3:
            continue
        # Sort by MON_SUN descending; negate it so sorted() (ascending) gives highest first
        sorted_sites = sorted(
            sites,
            key=lambda r: (-float(r['mon_sun']), r['globalid'].strip().lower())
        )
        # Assign rank based on position in the sorted list, starting at 1
        inner = {}
        for rank, row in enumerate(sorted_sites, start=1):
            sn = row['site_no'].strip()
            inner[sn] = [round(float(row['mon_sun']), 4), round(float(row['pct_heavy_mon_sun']), 4), rank]
        op2[lg_key] = inner
 
    return op2
 
 
def cosine_similarity(vec_a, vec_b):
    # Dot product: sum of element-wise products
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    # Magnitude: square root of sum of squares for each vector
    mag_a = sum(a ** 2 for a in vec_a) ** 0.5
    mag_b = sum(b ** 2 for b in vec_b) ** 0.5
    # Guard against division by zero if either vector is all zeros
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
 
 
def compute_op3(region_rows):
    # Per year (ascending): avg weekday and weekend heavy vehicle %, then their cosine similarity.
    if not region_rows:
        return []
 
    # Bucket rows by traffic year
    year_groups = {}
    for row in region_rows:
        year = row['traffic_year'].strip()
        year_groups.setdefault(year, []).append(row)
 
    # Sort years chronologically so the output lists are in ascending order
    sorted_years = sorted(year_groups.keys())
    weekday_avgs, weekend_avgs = [], []
 
    for year in sorted_years:
        rows = year_groups[year]
        # Collect all weekday and weekend percentages for this year, then average them
        wd_vals = [float(r['pct_heavy_mon_fri']) for r in rows]
        we_vals = [float(r['pct_heavy_sat_sun']) for r in rows]
        weekday_avgs.append(sum(wd_vals) / len(wd_vals))
        weekend_avgs.append(sum(we_vals) / len(we_vals))
 
    # Each list is now one entry per year; compare their direction with cosine similarity
    cos_sim = cosine_similarity(weekday_avgs, weekend_avgs)
    return [
        [round(v, 4) for v in weekday_avgs],
        [round(v, 4) for v in weekend_avgs],
        round(cos_sim, 4)
    ]
 
 
def main(file_name, ra_name):
    empty = ({}, {}, [])
 
    # Both inputs must be non-empty strings before we proceed
    if not isinstance(file_name, str) or not isinstance(ra_name, str):
        return empty
    if not file_name.strip() or not ra_name.strip():
        return empty
 
    rows = read_csv(file_name)
    if not rows:  # unreadable or empty file
        return empty
 
    # Clean the data and narrow it down to the target region
    region_rows = validate_and_filter(rows, ra_name)
    return compute_op1(region_rows), compute_op2(region_rows), compute_op3(region_rows)
