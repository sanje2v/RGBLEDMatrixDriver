TOTAL_PRIMARY_COLORS = 3    # Red, Green and Blue
TOTAL_RGBP_BYTES = TOTAL_PRIMARY_COLORS + 1
ROW_COLOR_ON_BYTE = 0xFF    # Turn all LEDs of a color in a row
ROW_COLOR_OFF_BYTE = 0x00   # Turn off LEDs of a color in a row

# REF: https://chrisalbon.com/python/data_wrangling/break_list_into_chunks_of_equal_size/
def chunks(l, chunk_size):   # NOTE: 'chunk_size' is number of items per chuck
    # For item i in a range that is a length of l,
    for i in range(0, len(l), chunk_size):
        # Create an index range for l of chuck_size items:
        yield l[i:i+chunk_size]


def spinWait(times):
    i = 0
    while(i < times):
        i += 1


def assignDict(src_dict, dest_dict):
    for key in dest_dict.keys():
        dest_dict[key] = src_dict[key]


def toSecs(msecs):
    return msecs / 1000.0