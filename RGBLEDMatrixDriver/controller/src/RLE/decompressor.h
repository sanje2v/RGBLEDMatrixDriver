#ifndef DECOMPRESSOR_H
#define DECOMPRESSOR_H

#include <Arduino.h>


// A variant of RLE for compressing 32-bits
// to 5-bits for color + 3-bits for no. of repeats
// for each color channel
class Decompressor
{
private:
    static const uint8_t BUFFER_SIZE = 3;

    uint8_t m_buffer[Decompressor::BUFFER_SIZE];
    uint8_t m_nextBufferWriteIndex;
    bool m_doSoftReset;
    
public:
    Decompressor();
    uint16_t feed(uint8_t data,
                  uint8_t *pFramesBuffer,
                  uint16_t currentWriteBytePos,
                  uint16_t totalFramesBufferSize);
    bool gotSoftResetSequence();
    void reset();
};

#endif