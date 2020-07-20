class Compressor:
    NUM_COLOR_CHANNELS = 3
    MAX_TIMES = 8     # For 3 bits to represent repeats

    def feed(self, data):
        data_size = len(data)
        assert data_size % self.NUM_COLOR_CHANNELS == 0, \
                "Size of color data frames must be a multiple 3 which is the no. of color channels!"
        
        # We convert to 5-bit color which will also help us to compress better
        data = list(map(lambda x: ((x >> 3) << 3), data))

        compressed_output = []

        read_red_index = 0
        read_green_index = read_red_index + 1
        read_blue_index = read_green_index + 1

        def compressChannel(compressed_output,
                            read_index,
                            data_size,
                            max_times=self.MAX_TIMES,
                            offset=self.NUM_COLOR_CHANNELS):
            if read_index < data_size:
                times = 1
                next_read_index = read_index + offset
                while (next_read_index < data_size and \
                       (times + 1) < max_times and \
                       data[read_index] == data[next_read_index]):
                    times += 1

                    next_read_index = next_read_index + offset

                compressed_output.append(data[read_index] | times)
                read_index = next_read_index
            else:
                compressed_output.append(0x00)

            return read_index

        while (read_red_index < data_size or \
               read_green_index < data_size or \
               read_blue_index < data_size):
            
            read_red_index = compressChannel(compressed_output, read_red_index, data_size)
            read_green_index = compressChannel(compressed_output, read_green_index, data_size)
            read_blue_index = compressChannel(compressed_output, read_blue_index, data_size)

        assert len(compressed_output) % self.NUM_COLOR_CHANNELS == 0, \
                "Compressed data size must have been multiple of 3. Possible error in logic."

        return bytes(compressed_output)
