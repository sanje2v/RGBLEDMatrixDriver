#ifndef DECOMPRESSOR_H
#define DECOMPRESSOR_H

#include <Arduino.h>

// A variant of RLE for compressing 32-bits
// to 28-bits color + 6-bit no. of repeats
class Decompressor
{
private:
    static const uint8_t BUFFER_SIZE = 3;

    uint8_t m_Buffer[Decompressor::BUFFER_SIZE];
    uint8_t m_NextBufferWriteIndex;
    
public:
    Decompressor();
    uint16_t feed(uint8_t dataByte,
                  uint8_t *pFramesBuffer,
                  uint16_t currentWritePos,
                  uint16_t totalFramesBufferSize);
};

#endif
