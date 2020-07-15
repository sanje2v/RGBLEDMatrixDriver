from libs.Compressor import Compressor

#data = [8, 16, 32, 8, 16, 32]
data = [8, 16, 32, 32, 16, 8]

compressor = Compressor()
print(compressor.feed(data))