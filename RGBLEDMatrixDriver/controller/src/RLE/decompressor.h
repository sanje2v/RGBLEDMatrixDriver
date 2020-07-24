#ifndef DECOMPRESSOR_H
#define DECOMPRESSOR_H

#include <Arduino.h>


// A variant of RLE for compressing 24-bits
// to 5-bits for color + 3-bits for no. of times
// for each color channel
class Decompressor
{
private:
    static const uint8_t BUFFER_SIZE = 3;

    uint8_t m_buffer[Decompressor::BUFFER_SIZE];
    uint8_t m_nextBufferWriteIndex;
#ifdef DEBUG
    uint16_t m_totalBytesDecompressed;
#endif

    static uint8_t addDithering(uint8_t dataByte, int8_t amount);
    
public:
    Decompressor();
    void feed(uint8_t data,
              uint8_t *pFramesBuffer,
              uint16_t *pCurrentWriteBytePos_Red,
              uint16_t *pCurrentWriteBytePos_Green,
              uint16_t *pCurrentWriteBytePos_Blue,
              uint16_t totalFramesBufferSize);
#ifdef DEBUG
    uint16_t getTotalBytesDecompressed();
    void resetTotalBytesDecompressed();
#endif
    void reset();
};

#endif