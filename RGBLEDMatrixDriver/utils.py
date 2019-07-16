TOTAL_PRIMARY_COLORS = 3    # Red, Green and Blue

# REF: https://chrisalbon.com/python/data_wrangling/break_list_into_chunks_of_equal_size/
def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]


def spinWait(times):
    i = 0
    while(i < times):
        i += 1


def assignDict(src_dict, dest_dict):
    for key in dest_dict.keys():
        dest_dict[key] = src_dict[key]


def toSecs(msecs):
    return msecs / 1000.0