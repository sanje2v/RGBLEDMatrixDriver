#ifndef DECOMPRESSOR_H
#define DECOMPRESSOR_H

// A variant of RLE for compressing 32-bits
// to 28-bits color + 6-bit no. of repeats
class Decompressor
{
private:
    const uint8_t BUFFER_SIZE = 3;

    uint8_t m_Buffer[BUFFER_SIZE];
    uint8_t m_NextBufferWriteIndex;
    
public:
    Decompressor();
    void feed();
};

#endif
