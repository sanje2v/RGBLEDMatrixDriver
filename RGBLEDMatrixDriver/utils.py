TOTAL_PRIMARY_COLORS = 3    # Red, Green and Blue


# REF: https://chrisalbon.com/python/data_wrangling/break_list_into_chunks_of_equal_size/
def chunks(l, chunk_size):   # NOTE: 'chunk_size' is number of items per chuck
    # For item i in a range that is a length of l,
    for i in range(0, len(l), chunk_size):
        # Create an index range for l of chuck_size items:
        yield l[i:i+chunk_size]

def assignDict(src_dict, dest_dict):
    for key in dest_dict.keys():
        dest_dict[key] = src_dict[key]

def toSecs(msecs):
    return msecs / 1000.0

def makeResetCommand(interval_enum):
    interval = interval_enum.value
    assert interval > 0 and interval < 8, "ERROR: Unsupported interval: {}".format(interval)

    return int.to_bytes((interval << 3), length=1, byteorder='big')