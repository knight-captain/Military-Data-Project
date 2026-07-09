HEADER_WEIGHT = 0.40
PARENT_WEIGHT = 0.10
CAT_WEIGHT = 0.40
RAW_COL_WEIGHT = 0.10 # Higher = countries clump to themselves more since tables within the same country were likely written by the same author. Keep low!

def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)

def calc_diff(fpA, fpB, h_w = HEADER_WEIGHT, p_w = PARENT_WEIGHT, c_w = CAT_WEIGHT, rc_w = RAW_COL_WEIGHT):
    sim_h = jaccard(fpA["headers"], fpB["headers"])
    sim_p = jaccard(fpA["parents"], fpB["parents"])
    sim_c = jaccard(fpA["cats"],    fpB["cats"])
    sim_r = jaccard(fpA["cols"],    fpB["cols"])

    return (h_w * sim_h +
            p_w * sim_p +
            c_w * sim_c +
            rc_w * sim_r)