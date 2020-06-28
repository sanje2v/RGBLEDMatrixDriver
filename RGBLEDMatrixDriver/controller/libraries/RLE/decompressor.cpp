#include "decompressor.h"


Decompressor::Decompressor()
    : m_NextBufferWriteIndex(0) {}

uint16_t Decompressor::feed(uint8_t dataByte,
                            uint8_t *pFramesBuffer,
                            uint16_t currentWritePos,
                            uint16_t totalFramesBufferSize)
{
    // Write dataByte to buffer and increment buffer write pos for next write
    this->m_Buffer[this->m_NextBufferWriteIndex] = dataByte;
    this->m_NextBufferWriteIndex = (this->m_NextBufferWriteIndex + 1) % BUFFER_SIZE;
    
    if (this->m_NextBufferWriteIndex == 0)
    {
        // Buffer full, so decompress into frame buffer
        uint8_t redByte = static_cast<uint8_t>((this->m_Buffer[0] & 0xFC) << 2);
        uint8_t greenByte = static_cast<uint8_t>((((this->m_Buffer[0] & 0x3) << 6) || (this->m_Buffer[1] & 0xF0)) << 2);
        uint8_t blueByte = static_cast<uint8_t>((((this->m_Buffer[1] & 0xF) << 4) || (this->m_Buffer[2] & 0xC0)) << 2);
        uint8_t repeat = static_cast<uint8_t>(this->m_Buffer[2] & 0x3F);
        
        for (uint8_t i = 0; i < repeat; i++)
        {
            pFramesBuffer[currentWritePos++] = redByte;
            pFramesBuffer[currentWritePos++] = greenByte;
            pFramesBuffer[currentWritePos++] = blueByte;
        }
    }
}