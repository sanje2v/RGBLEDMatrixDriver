#include "decompressor.h"


Decompressor::Decompressor()
    : m_nextBufferWriteIndex(0), m_doSoftReset(false) {}

uint16_t Decompressor::feed(uint8_t data,
                            uint8_t *pFramesBuffer,
                            uint16_t currentWriteBytePos,
                            uint16_t totalFramesBufferSize)
{
    // Write dataByte to buffer and increment buffer write pos for next write
    this->m_Buffer[this->m_nextBufferWriteIndex] = data;
    this->m_nextBufferWriteIndex = (this->m_nextBufferWriteIndex + 1) % BUFFER_SIZE;
    
    /* NOTE: Expected 3 bytes data to decompress will be in the following format:
        [XXXXX, YYY], [XXXXX, YYY], [XXXXX, YYY]
        [Red, Repeats], [Green, Repeats], [Blue, Repeats]
    */
    if (this->m_nextBufferWriteIndex == 0)
    {
        // Buffer full, so decompress into frame buffer
        uint8_t redByte = (this->m_buffer[0] & 0xF8);
        uint8_t redRepeats = (this->m_buffer[0] & 0x07);
        uint8_t greenByte = (this->m_buffer[1] & 0xF8);
        uint8_t greenRepeats = (this->m_buffer[1] & 0x07);
        uint8_t blueByte = (this->m_buffer[2] & 0xF8);
        uint8_t blueRepeats = (this->m_buffer[2] & 0x07);
        
        for (uint8_t i = 0; i < redRepeats; i++)
        {
            
            pFramesBuffer[currentWritePos++] = redByte;
            pFramesBuffer[currentWritePos++] = greenByte;
            pFramesBuffer[currentWritePos++] = blueByte;
        }
    }
}

bool gotSoftResetSequence()
{
    return this->m_doSoftReset;
}

void resetSoftResetDetector()
{
    this->m_doSoftReset = false;
}